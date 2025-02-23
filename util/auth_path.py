import bcrypt
import uuid
import hashlib
from util.response import Response
from util.auth import extract_credentials, validate_password
from util.database import user_collection, chat_collection
from util.chat_path import generate_profile_pic

def login(request, handler):
    res = Response()
    credentials = extract_credentials(request)
    username = credentials[0]
    password = credentials[1]

    pass

#session token never passed in, it only pass to /api
def registration(request, handler):
    # print("R1quest:")
    # headers = request.headers
    # for header in headers:
    #     print(header)
    res = Response()
    credentials = extract_credentials(request)
    username = credentials[0]
    password = credentials[1]
    session_token = request.cookies.get("session")

    #print(f"Session token received: {session_token}")

    username_exist = user_collection.find_one({"username": username})
    if username_exist:
        res.set_status(400, "Bad Request")
        res.text("This username had been taken. Please try again.")
        handler.request.sendall(res.to_data())
        return

    if validate_password(password):
        salt = bcrypt.gensalt()
        hashed_pass = bcrypt.hashpw(password.encode("utf-8"), salt).decode('utf-8')
        user_id = str(uuid.uuid4())
        auth_token = str(uuid.uuid4())
        hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest()
        img_url = generate_profile_pic(auth_token)

        user_collection.insert_one({
            "user_id": user_id,
            "author": username,
            "password": hashed_pass,
            "auth_token": hashed_auth_token,
            "nickname": username,
            "imageURL": img_url
        })

        #if the user send multiple message before registration, the registration will update all the guest message to this user.
        if session_token:
            user_guest = user_collection.find_one({"session": session_token})
            user_guest_user_id = user_guest.get("user_id")
            chat_collection.update_many({"user_id": user_guest_user_id}, {"$set": {"user_id": user_id, "author": username, "nickname": username, "imageURL": img_url}})
            user_collection.delete_one({"user_id": user_guest_user_id})
            #Delete the session cookie
            res.cookies({"session": session_token + "; Max-Age=0"})

        #Set cookies, need to set the authentication cookie with directives : Max-Age
        #res.cookies({"session": auth_token + "; Max-Age=2592000; Secure; HttpOnly"}) --> send when login

        res.set_status(200, "OK")
        res.text("Account Created")
        handler.request.sendall(res.to_data())
    else:
        res.set_status(400, "Bad Request")
        res.text("Do STRONGER password! Your password doesn't meet our requirements."
                 "\r\nYour password must be at least 8 characters, at least 1 of them is uppercase&lowercase, at least 1 digit, at least 1 special character!")
        handler.request.sendall(res.to_data())


def logout(request, handler):
    res = Response()
    pass