import uuid
import json

from util.database import video_call_collection
from util.response import Response
from util.websockets import generate_ws_frame

rooms = {}  # room_id : [{socket_id, username, connection}, ...]
users_in_room = {}  # socket_id : room_id


def create_room(request, handler):
    res = Response()
    body = json.loads(request.body.decode('utf-8'))
    room_name = body.get("name", "").strip()

    if not room_name:
        res.set_status(400, "Bad Request")
        res.text("No room name provided.")
        handler.request.sendall(res.to_data())
        return

    room_id = str(uuid.uuid4())
    video_call_collection.insert_one({
        "room_id": room_id,
        "room_name": room_name
    })

    res.json({"id": room_id})
    handler.request.sendall(res.to_data())


def send_call_list(active_connections):
    all_rooms = video_call_collection.find({}, {"_id": 0})

    all_calls = []
    for room in all_rooms:
        curr_room_info = {"id": room["room_id"], "name": room["room_name"]}
        all_calls.append(curr_room_info)

    res_payload = {"messageType": "call_list", "calls": all_calls}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode('utf-8'))
    for curr_connection in active_connections.values():
        curr_connection.sendall(res_frame)


def join_room_call(payload, username, curr_connection):
    room_id = payload["callId"]
    socket_id = str(uuid.uuid4())

    if room_id not in rooms:
        rooms[room_id] = []
    users_in_room[socket_id] = room_id

    curr_room = rooms[room_id]
    curr_room.append({
        "socket_id": socket_id,
        "username": username,
        "connection": curr_connection
    })

    room = video_call_collection.find_one({"room_id": room_id})
    room_name = room["room_name"]

    # manage with call_info
    room_name_payload = {"messageType": "call_info", "name": room_name}
    room_name_payload = json.dumps(room_name_payload)

    room_name_frame = generate_ws_frame(room_name_payload.encode('utf-8'))
    curr_connection.sendall(room_name_frame)

    # manage with existing participants
    participants = []
    for participant in curr_room:
        if participant["connection"] != curr_connection:
            curr_participant = {"socketId": participant["socket_id"], "username": participant["username"]}
            participants.append(curr_participant)

    participants_payload = {"messageType": "existing_participants", "participants": participants}
    participants_payload = json.dumps(participants_payload)

    participants_frame = generate_ws_frame(participants_payload.encode('utf-8'))
    curr_connection.sendall(participants_frame)

    # manage with user_join broadcast
    user_joined_payload = {"messageType": "user_joined", "socketId": socket_id}
    user_joined_payload = json.dumps(user_joined_payload)

    user_joined_frame = generate_ws_frame(user_joined_payload.encode('utf-8'))
    for user in curr_room:
        if user["socket_id"] != socket_id:
            curr_user_connection = user["connection"]
            curr_user_connection.sendall(user_joined_frame)


def webRTC_messages(payload, username):
    # handle offer, answer, ice_candidates

    target_user_socket_id = payload["socketId"]
    #Find the room target_user is in. We can assume that sender & target_user is in the same room

    room_id = users_in_room[target_user_socket_id]

    sender = None
    for participant in rooms[room_id]:
        if participant["username"] == username:
            sender = participant
            break

    #evoke error (no sender found?)
    if not sender:
        return

    #message payload
    message_payload = payload.copy()
    message_payload["socketId"] = sender["socket_id"]
    message_payload["username"] = sender["username"] #or can just use username
    message_payload = json.dumps(message_payload)

    message_frame = generate_ws_frame(message_payload.encode('utf-8'))

    target_user = None
    for participant in rooms[room_id]:
        if participant["socket_id"] == target_user_socket_id:
            target_user = participant
            break

    #evoke error (No target user found)
    if not target_user:
        return

    #target_user["connection] --> target user's handler.request
    target_user["connection"].sendall(message_frame)

def disconnect(username):
    socket_id = None
    room_id = None
    for curr_room_id in rooms:
        for user in rooms[curr_room_id]:
            if user["username"] == username:
                socket_id = user["socket_id"]
                room_id = curr_room_id
                break
        if socket_id and room_id:
            break

    #user is not in a video call
    if not socket_id or not room_id:
        return

    new_participants = []
    for curr_user in rooms[room_id]:
        if curr_user["socket_id"] != socket_id:
            new_participants.append(curr_user)

    rooms[room_id] = new_participants

    if socket_id in users_in_room:
        del users_in_room[socket_id]

    user_left_payload = {"messageType": "user_left", "socketId": socket_id}
    user_left_payload = json.dumps(user_left_payload)

    user_left_frame = generate_ws_frame(user_left_payload.encode('utf-8'))

    for user in rooms[room_id]:
        curr_user_connection = user["connection"]
        curr_user_connection.sendall(user_left_frame)




