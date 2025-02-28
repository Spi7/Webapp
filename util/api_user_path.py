from util.response import Response
from util.database import user_collection
from util.auth import extract_credentials, validate_password
import hashlib
import bcrypt

def select_method(request, handler):
    if request.method == 'GET':
        if request.path.startswith("/api/users/@me"):
            profile_display(request, handler)
        elif request.path.startswith("/api/users/search"):
            search_user(request, handler)
    elif request.method == 'POST':
        if request.path.startswith("/api/users/settings"):
            update_profile(request, handler)


def profile_display(request, handler):
    res = Response()
    auth_token = request.cookies.get('auth_token')
    if auth_token:
        hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest()
        user_data = user_collection.find_one({'session': hashed_auth_token})

        username_and_user_id = {"username": user_data["author"], "id": user_data["user_id"],"nickname": user_data["nickname"]}
        res.json(username_and_user_id)
    else:
        res.set_status(401, "Unauthorized")
        res.json({})
    handler.request.sendall(res.to_data())




def search_user(request, handler):
    res = Response()
    user_list = []

    if "?" in request.path:
        query_key = request.path.split("?")[1]
        if "=" in query_key:
            query_value = query_key.split("=")[1]
            if query_value != "":
                users = user_collection.find({"author": {"$regex": "^" + query_value}}) #find users that matches query_key
                for user in users:
                    dict = {"id": user["user_id"], "username": user["author"]}
                    user_list.append(dict)

    res.json({"users": user_list})
    handler.request.sendall(res.to_data())

def update_profile(request, handler):
    res = Response()
    auth_token = request.cookies.get('auth_token')
    if auth_token:
        hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest() #check in db
        new_credentials = extract_credentials(request) #[0] --> username, [1] --> password
        new_username = new_credentials[0]
        new_password = new_credentials[1]
        curr_user_data = user_collection.find_one({'session': hashed_auth_token})
        curr_username = curr_user_data["author"]

        if new_username != curr_username:
            username_exist = user_collection.find_one({"author": new_username})
            if username_exist:
                # check if new_username had been taken or not
                res.set_status(400, "Bad Request")
                res.text("The new username you want had already been taken.")
                handler.request.sendall(res.to_data())
                return
            else:
                user_collection.update_one({"user_id": curr_user_data["user_id"]}, {"$set": {"nickname": new_username, "author": new_username, "username": new_username}})

        if new_password:
            if validate_password(new_password):
                # new password follows the requirement
                salt = bcrypt.gensalt()
                hashed_new_password = bcrypt.hashpw(new_password.encode("utf-8"), salt).decode('utf-8')
                user_collection.update_one({"user_id": curr_user_data["user_id"]}, {"$set": {"password": hashed_new_password, "session": ""}})

                res.set_status(302, "Found")
                res.text("Update successfully, please login again.")
                res.cookies({"auth_token": "dummy; Max-Age=0; HttpOnly; Path=/"})
                res.header["Location"] = "/login"
                res.header["Content-Length"] = "0"
                handler.request.sendall(res.to_data())
                return
            else:
                res.set_status(400, "Bad Request")
                res.text("Your new password is not strong enough.")
                handler.request.sendall(res.to_data())
                return
    else:
        res.set_status(401, "Unauthorized")
        res.text("No authentication token")
    handler.request.sendall(res.to_data())