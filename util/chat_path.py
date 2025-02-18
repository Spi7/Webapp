import html
import json
import uuid
import os
import requests
from util.response import Response
from util.database import chat_collection, user_collection

def select_chat_or_reaction(request, handler):
    if request.path.startswith("/api/chats"):
        if request.method == "PATCH":
            update_message(request, handler)
        elif request.method == "DELETE":
            delete_message(request, handler)
    elif request.path.startswith("/api/reaction"):
        if request.method == "PATCH":
            add_reaction(request, handler)
        elif request.method == "DELETE":
            delete_reaction(request, handler)
    elif request.path.startswith("/api/nickname"):
            change_nickname(request, handler)
    else:
        res = Response()
        res.set_status(404, "Not Found")
        res.text("INVALID PATH: " + request.path)
        handler.request.sendall(res.to_data())

#AO3 generate profile-pics
def generate_profile_pic(token):
    api_url = "https://api.dicebear.com/9.x/pixel-art/svg?seed=" + token
    api_response = requests.get(api_url)

    if api_response.status_code == 200:
        os.makedirs("public/imgs/profile-pics", exist_ok=True)
        profile_path = "public/imgs/profile-pics/" + token + ".svg"
        with open (profile_path, "wb") as profile_pic:
            profile_pic.write(api_response.content)
        return "/" + profile_path
    else:
        return "" #default back to broken image if api dicebear didn't work out

def create_user(token):
    user_id = str(uuid.uuid4())
    author = "Guest-" + uuid.uuid4().hex[:3]

    img_url = generate_profile_pic(token)
    user_collection.insert_one({
        "session": token,
        #"user_id": user_id,
        "author": author,
        "nickname": "",
        "imageURL": img_url
    })

def get_user(token):
    user_data =  user_collection.find_one({"session": token})
    if user_data is None:
        create_user(token)
        user_data = user_collection.find_one({"session": token})
    return user_data

#Create Message
def create_message(request, handler):
    res = Response()

    body = json.loads(request.body.decode("utf-8")) #later store as string into db
    body_content = html.escape(body["content"].strip())

    user_token = request.cookies.get("session") # token = session_id made by uuid

    if not user_token:
        user_token = str(uuid.uuid4())
        create_user(user_token)

    user_data = get_user(user_token)
    message_id = str(uuid.uuid4())

    chat_collection.insert_one({
        "id": message_id,
        "session": user_token,
        #"user_id": user_data["user_id"],
        "author": user_data["author"],
        "content": body_content,
        "nickname": user_data["nickname"],
        "imageURL": user_data.get("imageURL", ""),
        "updated": False
    })

    res.cookies({"session": user_token})
    res.text("message sent")
    handler.request.sendall(res.to_data())

def get_message(request, handler):
    res = Response()

    message_data = list(chat_collection.find({}, {"_id":0})) #contain all the messages

    all_messages = []
    for message in message_data:
        curr_mes = {
            "id": message["id"],
            "author": message["author"],
            "content": message["content"],
            "updated": message["updated"],
            "session": message["session"],
            #"user_id": message["user_id"],
            "reactions": message.get("reactions", {}),
            "nickname": message.get("nickname", ""), # front end js: message.nickname ? message.nickname : message.author
            "imageURL": message.get("imageURL", "")
        }
        all_messages.append(curr_mes)

    res.json({"messages": all_messages})
    handler.request.sendall(res.to_data())


def update_message(request, handler):
    res = Response()

    #get the curr id in order to grab the unique token
    get_message_id = request.path.rsplit("/", 1)[1] #check correct message_id
    user_token = request.cookies.get("session")
    user_data = get_user(user_token)
    curr_user_id = user_data["session"]
    curr_author = user_data["author"]

    #the current new modified body content
    body = json.loads(request.body.decode("utf-8"))
    body_content = html.escape(body["content"].strip())

    #checking if it's the actual author editing its message
    curr_message = chat_collection.find_one({"id": get_message_id})
    curr_message_author = curr_message["author"]
    curr_message_user_id = curr_message["session"]

    if curr_user_id == curr_message_user_id and curr_author == curr_message_author:
        chat_collection.update_one({"id": get_message_id}, {"$set": {"content": body_content, "updated": True}})
        res.text("message updated")
    else:
        res.set_status(403, "Forbidden")
        res.text("Be nice, don't EDIT other user's messages")
    handler.request.sendall(res.to_data())


def delete_message(request, handler):
    res = Response()

    get_message_id = request.path.rsplit("/", 1)[1]
    user_token = request.cookies.get("session")
    user_data = get_user(user_token)
    curr_user_id = user_data["session"]
    curr_author = user_data["author"]

    #check if it's actual author deleting the message
    curr_message = chat_collection.find_one({"id": get_message_id})
    curr_message_author = curr_message["author"]
    curr_message_user_id = curr_message["session"]

    if curr_user_id == curr_message_user_id and curr_author == curr_message_author:
        chat_collection.delete_one({"id": get_message_id})
        res.text("message deleted")
    else:
        res.set_status(403, "Forbidden")
        res.text("Be nice, don't DELETE other user's messages")
    handler.request.sendall(res.to_data())

#AO1 -------------------------------------------------------------------------
def add_reaction(request, handler):
    res = Response()

    #get the message_id to get the message in db | get the current user token so we can store who added this emoji in this message
    get_message_id = request.path.rsplit("/", 1)[1]
    curr_user = request.cookies.get("session")
    user_data = get_user(curr_user)
    curr_user_id = user_data["session"]
    curr_message = chat_collection.find_one({"id": get_message_id})

    #get the emoji
    body_content = json.loads(request.body.decode("utf-8"))
    emoji = html.escape(body_content["emoji"].strip()) # this have the emoji

    reactions = curr_message.get("reactions", {})

    #check if this user already added this emoji before or not
    if emoji not in reactions:
        reactions[emoji] = []

    #check if the user already add this emoji in this message
    if curr_user_id in reactions[emoji]:
        res.set_status(403, "Forbidden")
        res.text("You already added this reaction")
    else:
        reactions[emoji].append(curr_user_id)
        chat_collection.update_one({"id": get_message_id}, {"$set": {"reactions": reactions}})
        res.text("Reaction added")
    handler.request.sendall(res.to_data())


def delete_reaction(request, handler):
    res = Response()

    get_message_id = request.path.rsplit("/", 1)[1]
    curr_user = request.cookies.get("session")
    user_data = get_user(curr_user)
    curr_user_id = user_data["session"]
    curr_message = chat_collection.find_one({"id": get_message_id})

    body_content = json.loads(request.body.decode("utf-8"))
    emoji = html.escape(body_content["emoji"].strip())

    #check if the user ever applied that emoji in the curr message, if yes remove it
    reactions = curr_message.get("reactions", {})
    if curr_user_id in reactions[emoji]:
        reactions[emoji].remove(curr_user_id)
        if len(reactions[emoji]) == 0:
            #remove the key for this emoji if there isn't any users
            reactions.pop(emoji, None)
        chat_collection.update_one({"id": get_message_id}, {"$set": {"reactions": reactions}})
        res.text("Reaction deleted")
    else:
        res.set_status(403, "Forbidden")
        res.text("The emoji was either never added by YOU or YOU already removed it!")
    handler.request.sendall(res.to_data())

#AO2 -------------------------------------------------------------------------
def change_nickname(request, handler):
    res = Response()

    #get the current user
    user_token = request.cookies.get("session")
    user_data = get_user(user_token)
    curr_user_id = user_data["session"]

    #get the request content (new username)
    body_content = json.loads(request.body.decode("utf-8"))
    new_username = html.escape(body_content["nickname"].strip())

    #go into user collection and set a new field: nickname
    user_collection.update_one({"session": curr_user_id}, {"$set": {"nickname": new_username}})

    #update all messages with the session token to this new name
    chat_collection.update_many({"session": curr_user_id}, {"$set": {"nickname": new_username}})

    res.text("Nickname changed")
    handler.request.sendall(res.to_data())

#future use when change implementation for router
# def select_function(request, handler):
#     request_method = request.method
#     if request_method == "POST":
#         create_message(request, handler)
#     elif request_method == "GET":
#         get_message(request, handler)
#     elif request_method == "PATCH":
#         update_message(request, handler)
#     elif request_method == "DELETE":
#         delete_message(request, handler)