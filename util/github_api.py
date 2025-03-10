import hashlib

import requests
import uuid
from util.response import Response
from util.configuration import GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, REDIRECT_URI
from util.database import user_collection, chat_collection

access_tokens = {}
# 1) Users are redirected to request their GitHub identity
# 2) Users are redirected back to your site by GitHub
# 3) Your app accesses the API with the user's access token

def github_api_call(request, handler):
    res = Response()

    #generate an unique state for security
    state = str(uuid.uuid4())

    github_api_url = "https://github.com/login/oauth/authorize"
    query = "?client_id=" + GITHUB_CLIENT_ID + "&redirect_uri=" + REDIRECT_URI + "&scope=user:email,repo" + "&state=" + state
    github_api_url = github_api_url + query

    res.set_status(302, "Found")
    res.header["Location"] = github_api_url
    res.cookies({"oauth_state": state}) #keep track for state, --> security improvement
    res.text("Redirecting to github.")
    handler.request.sendall(res.to_data())

def github_callback(request, handler):
    res = Response()
    query = request.path.split("?")[1]
    header_list = query.split("&")

    header_dict = {}
    for header in header_list:
        key_value = header.split("=")
        curr_key = key_value[0]
        curr_value = key_value[1]
        header_dict[curr_key] = curr_value

    # from document, there should be a header key with code & state
    if "code" and "state" in header_dict:
        #exchange the temporary "code" for access token
        curr_state = request.cookies.get("oauth_state")
        header_state = header_dict["state"]
        if curr_state == header_state:
            code = header_dict["code"]
            token_url = "https://github.com/login/oauth/access_token"
            accept_header = {"Accept": "application/json"} #Make it json, so easier to get information
            data = {
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "redirect_uri": REDIRECT_URI,
                "code": code
            }
            token_res = requests.post(token_url, data=data, headers=accept_header)
            token_json = token_res.json()

            #in token_json there should have the access_token
            access_token = token_json["access_token"]
            user_url = "https://api.github.com/user"
            auth_header = {"Authorization": "token " + access_token}

            user_res = requests.get(user_url, headers=auth_header)
            user_info = user_res.json()

            username = user_info["login"]
            user_email = user_info["email"]

            auth_token = str(uuid.uuid4())
            hashed_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()

            access_tokens[auth_token] = access_token

            user_data = user_collection.find_one({"author": username})

            if user_data:
                user_collection.update_one({"author": username}, {"$set": {"session": hashed_auth_token}})
            else:
                user_id = str(uuid.uuid4())
                user_collection.insert_one({
                    "user_id": user_id,
                    "session": hashed_auth_token,
                    "author": username,
                    "nickname": username,
                    "email": user_email,
                    "imageURL": "",
                    "github": True
                })
            #similar as login, update messages send as guest
            session_token = request.cookies.get("session")
            if session_token:
                #get the current stored user_data for github user once again
                user_data = user_collection.find_one({"author": username})

                user_guest = user_collection.find_one({"session": session_token})
                user_guest_user_id = user_guest.get("user_id")
                chat_collection.update_many({"user_id": user_guest_user_id}, {
                    "$set": {"user_id": user_data.get("user_id"), "author": username, "nickname": username, "imageURL": ""}})
                user_collection.delete_one({"user_id": user_guest_user_id})
                # Delete the session cookie
                res.cookies({"session": session_token + "; Max-Age=0"})

            res.cookies({"auth_token": auth_token + "; Max-Age=86400; HttpOnly; Path=/"})
            res.cookies({"oauth_state": curr_state + "; Max-Age=0; HttpOnly; Path=/"})
            res.set_status(302, "Found")
            res.header["Location"] = "/"
            handler.request.sendall(res.to_data())
        else:
            res.set_status(400, "Bad Request")
            res.text("Invalid state")
            handler.request.sendall(res.to_data())

    else:
        res.set_status("400", "Bad Request")
        res.text("No code found from headers")
        handler.request.sendall(res.to_data())

def get_repos(username):
    url = "https://api.github.com/users/" + username + "/repos" + "?per_page=50"
    github_response = requests.get(url) #Method: GET --> /users/{username}/repos

    if github_response.status_code == 200:
        repositories = github_response.json()
        repo_list = []

        for repository in repositories:
            #each link should bring you to the user's actual repositories rather than the whole repo list page
            link = '<a href="https://github.com/' + username + "/" + repository["name"] + '">' + repository["name"] + "</a>"
            repo_list.append(link)
        return ", ".join(repo_list)
    return "failed"

def star_repo(auth_token, repo_name):
    # hashed_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()
    # user_data = user_collection.find_one({"session": hashed_auth_token})
    # curr_username = user_data.get("author")
    url = "https://api.github.com/user/starred/" + repo_name
    auth_header = {"Authorization": "token " + access_tokens[auth_token]}
    github_response = requests.put(url, headers=auth_header) #Method:PUT --> /user/starred/{owner}/{repo}

    #when user typed, the second part would be owner/repo_name
    if github_response.status_code == 204:
        return "User has starred " + '<a href="https://github.com/' + repo_name + '" style="color:lightblue;">' + repo_name + "</a>"
    return "failed"

def create_issue(auth_token, repo, title):
    url = "https://api.github.com/repos/" + repo + "/issues"
    auth_header = {"Authorization": "token " + access_tokens[auth_token]}
    data = {"title": title, "body": ""}
    github_response = requests.post(url, headers=auth_header, json=data) #Method: POST -->/repos/{owner}/{repo}/issues

    if github_response.status_code == 201:
        html_url = github_response.json()["html_url"]
        return "User has created an issue: " + '<a href="' + html_url + '" style="color:lightblue;">' + title + "</a>"
    return "failed"