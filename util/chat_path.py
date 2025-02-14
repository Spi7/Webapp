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
            "updated": message["updated"]
        }
        all_messages.append(curr_mes)

    res.json({"messages": all_messages})
    handler.request.sendall(res.to_data())


def update_message(request, handler):
    pass


def delete_message(request, handler):
    pass