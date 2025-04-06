from util.response import Response
from util.websockets import compute_accept, parse_ws_frame, generate_ws_frame
from util.wsFrame import wsFrame
from util.database import user_collection, drawing_collection
from util.drawingboard import store_drawing, send_all_drawings, broadcast_active_users
from util.direct_message import get_all_users, get_dm_history, send_dm

import hashlib
import json

active_connections = {}

def handle_ws_connection(request, handler):
    res = Response()

    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        res.set_status(401, "Unauthorized")
        res.text("No auth token")
        handler.request.sendall(res.to_data())
        return

    hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest()
    user = user_collection.find_one({'session': hashed_auth_token})

    username = user['nickname']

    active_connections[username] = handler.request #each user's username map to each of their web socket connection

    socket_key = request.headers.get("Sec-WebSocket-Key")
    accept_response = compute_accept(socket_key)

    res.set_status(101, "Switching Protocols")
    res.headers({"Upgrade": "websocket"})
    res.headers({"Connection": "Upgrade"})
    res.headers({"Sec-WebSocket-Accept": accept_response})
    handler.request.sendall(res.to_data())

    send_all_drawings(active_connections[username]) #send all the drawing strokes to this user who's connected
    broadcast_active_users(active_connections) #broadcast new user connected

    buffer = b""
    #continuation frame, first fin_bit = 0, opcode will be 0001, after first frame, all finbit = 0, opcode=0000, until last frame finbit=1, opcode still 0000
    curr_frame_info = {
        "payload": b"",
        "opcode": None
    }

    while True:
        #receive first chunk of 2048 bytes
        received_data = handler.request.recv(2048)
        # print("======== Received Data for ws =======")
        # print(received_data)
        # print("======== End Data =======")
        if len(received_data) < 2: #initial message is causing error
            break

        buffer += received_data

        #when buffer > the frame length, indicating more frame to be processed, process all before receiving new data, only receive new data when the frame doesn't have enough data to be parsed
        while len(buffer) >= 2:
            frame = wsFrame()
            frame.parse_headers(received_data)
            full_frame_length = frame.header_length + frame.payload_length

            #break to receive more data for buffer
            if len(buffer) < full_frame_length:
                break

            this_frame_bytes = buffer[:full_frame_length]
            buffer = buffer[full_frame_length:]
            whole_frame = parse_ws_frame(this_frame_bytes)

            if curr_frame_info["opcode"] is None:
                curr_frame_info["opcode"] = whole_frame.opcode
            curr_frame_info["payload"] += whole_frame.payload

            if whole_frame.fin_bit == 1:
                if curr_frame_info["opcode"] == 1:
                    json_payload = json.loads(curr_frame_info["payload"].decode('utf-8'))
                    message_type = json_payload['messageType']

                    if message_type == "echo_client":
                        res_payload = json.dumps({"messageType": "echo_server","text":json_payload["text"]}).encode('utf-8')
                        res_frame = generate_ws_frame(res_payload)
                        handler.request.sendall(res_frame)
                    elif message_type == "drawing":
                        store_drawing(json_payload, active_connections)
                    elif message_type == "get_all_users":
                        get_all_users(active_connections[username])
                    elif message_type == "select_user":
                        from_user = username
                        to_user = json_payload["targetUser"]
                        get_dm_history(from_user, to_user, active_connections[username])
                    elif message_type == "direct_message":
                        from_user = username
                        send_dm(from_user, json_payload, active_connections)

                    #reset for next frame
                    curr_frame_info = {
                        "payload": b"",
                        "opcode": None
                    }
                #disconnection
                elif curr_frame_info["opcode"] == 8:
                    del active_connections[username]
                    close_frame = generate_ws_frame(payload=b"")
                    handler.request.sendall(close_frame)
                    handler.request.close()

                    broadcast_active_users(active_connections) #broadcast the user disconnected
                    return


