import json

from util.database import user_collection, dm_collection
from util.websockets import generate_ws_frame

def get_all_users(user_connection):
    users = user_collection.find({}, {"_id": 0})
    account_users = []
    for user in users:
        nickname = user.get("nickname", "")
        author = user["author"]

        if nickname != "" and not author.startswith("Guest-"):
            curr_user = {"username": nickname}
            account_users.append(curr_user)

    res_payload = {"messageType": "all_users_list", "users": account_users}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode("utf-8"))
    user_connection.sendall(res_frame)

def get_dm_history(from_user, to_user, user_connection):
    messages = dm_collection.find({
        "$or": [
            {"fromUser": from_user, "toUser": to_user},
            {"fromUser": to_user, "toUser": from_user},
        ]
    }).sort({"_id": 1})

    message_history = []
    for message in messages:
        curr_dict = {
            "messageType": message["messageType"],
            "fromUser": message["fromUser"],
            "text": message["text"]
        }
        message_history.append(curr_dict)

    res_payload = {"messageType": "message_history", "messages": message_history}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode("utf-8"))
    user_connection.sendall(res_frame)


def send_dm(from_user, payload, active_connections):
    message_type = payload.get("messageType")
    to_user = payload.get("targetUser")
    message = payload.get("text")

    dm_collection.insert_one({
        "messageType": message_type,
        "fromUser": from_user,
        "toUser": to_user,
        "text": message
    })

    res_payload = {"messageType": "direct_message", "fromUser": from_user, "text": message}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode("utf-8"))

    if from_user in active_connections:
        from_user_connection = active_connections[from_user]
        from_user_connection.sendall(res_frame)
    if to_user in active_connections:
        to_user_connection = active_connections[to_user]
        to_user_connection.sendall(res_frame)