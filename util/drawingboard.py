from util.database import drawing_collection
from util.websockets import generate_ws_frame
import json

#active_connections --> connections for all users
#user_connection --> a specific user's connection

def store_drawing(payload, active_connections):
    for user_connections in active_connections.values():
        frame = generate_ws_frame(json.dumps(payload).encode("utf-8"))
        user_connections.sendall(frame)

    #store drawings in database
    drawing_collection.insert_one({
        "startX": payload["startX"],
        "startY": payload["startY"],
        "endX": payload["endX"],
        "endY": payload["endY"],
        "color": payload["color"]
    })


def send_all_drawings(user_connections):
    all_drawings = list(drawing_collection.find({}, {"_id": 0}))

    res_payload = {"messageType": "init_strokes", "strokes": all_drawings}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode("utf-8"))
    user_connections.sendall(res_frame)

def broadcast_active_users(active_connections):
    all_users = []
    for user in active_connections.keys():
        curr_user = {"username": user}
        all_users.append(curr_user)

    res_payload = {"messageType": "active_users_list", "users": all_users}
    res_payload = json.dumps(res_payload)

    res_frame = generate_ws_frame(res_payload.encode("utf-8"))

    for user_connections in active_connections.values():
        user_connections.sendall(res_frame)


