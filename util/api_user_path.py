from util.response import Response
from util.database import user_collection
import hashlib

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
    if not auth_token:
        res.set_status(401, "Unauthorized")
        res.json({})
        handler.request.sendall(res.to_data())
        return
    #else the user is logged in, then we display the information
    hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest()
    user_data = user_collection.find_one({'session': hashed_auth_token})

    username_and_user_id = {"username": user_data["author"], "id": user_data["user_id"], "nickname": user_data["nickname"]}
    res.json(username_and_user_id)
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
    pass