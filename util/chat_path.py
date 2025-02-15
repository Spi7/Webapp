import html
import json
import uuid
from util.response import Response
from util.database import chat_collection, user_collection

#future use when change implementation for router
def select_function(request, handler):
    request_method = request.method
    if request_method == "POST":
        create_message(request, handler)
    elif request_method == "GET":
        get_message(request, handler)
    elif request_method == "PATCH":
        update_message(request, handler)
    elif request_method == "DELETE":
        delete_message(request, handler)

def create_user(token):
    user_id = str(uuid.uuid4())
    author = "Guest-" + uuid.uuid4().hex[:3]

    user_collection.insert_one({
        "session": token,
        "user_id": user_id,
        "author": author
    })

def get_user(token):
    user_data =  user_collection.find_one({"session": token})
    if user_data is None:
        create_user(token)
        user_data = user_collection.find_one({"session": token})
    return user_data["user_id"], user_data["author"]

#Create Message
def create_message(request, handler):
    res = Response()

    body = json.loads(request.body.decode("utf-8")) #later store as string into db
    body_content = html.escape(body["content"].strip())

    user_token = request.cookies.get("session") # token = session_id made by uuid

    if not user_token:
        user_token = str(uuid.uuid4())
        create_user(user_token)

    user_id, author = get_user(user_token)
    message_id = str(uuid.uuid4())

    chat_collection.insert_one({
        "id": message_id,
        "user_id": user_id,
        "author": author,
        "content": body_content,
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
            "user_id": message["user_id"]
        }
        all_messages.append(curr_mes)

    res.json({"messages": all_messages})
    handler.request.sendall(res.to_data())


def update_message(request, handler):
    res = Response()

    #get the curr id in order to grab the unique token
    get_message_id = request.path.rsplit("/", 1)[1] #check correct message_id
    user_token = request.cookies.get("session")
    curr_user_id, curr_author = get_user(user_token)

    #the current new modified body content
    body = json.loads(request.body.decode("utf-8"))
    body_content = html.escape(body["content"].strip())

    #checking if it's the actual author editing its message
    curr_message = chat_collection.find_one({"id": get_message_id})
    curr_message_author = curr_message["author"]
    curr_message_user_id = curr_message["user_id"]

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
    curr_user_id, curr_author = get_user(user_token)

    #check if it's actual author deleting the message
    curr_message = chat_collection.find_one({"id": get_message_id})
    curr_message_author = curr_message["author"]
    curr_message_user_id = curr_message["user_id"]

    if curr_user_id == curr_message_user_id and curr_author == curr_message_author:
        chat_collection.delete_one({"id": get_message_id})
        res.text("message deleted")
    else:
        res.set_status(403, "Forbidden")
        res.text("Be nice, don't DELETE other user's messages")
    handler.request.sendall(res.to_data())