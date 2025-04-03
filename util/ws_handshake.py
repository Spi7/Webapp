from util.response import Response
from util.websockets import compute_accept, parse_ws_frame, generate_ws_frame
from util.wsFrame import wsFrame
from util.database import user_collection

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

    username = user['username']

    active_connections[username] = handler.request #each user's username map to each of their web socket connection

    socket_key = request.headers.get("Sec-WebSocket-Key")
    accept_response = compute_accept(socket_key)

    res.set_status(101, "Switching Protocols")
    res.headers([{"Upgrade": "websocket"}, {"Connection": "Upgrade"}, {"Sec-WebSocket-Accept": accept_response}])
    handler.request.sendall(res.to_data())

    buffer = b""
    while True:
        #receive first chunk of 2048 bytes
        received_data = handler.request.recv(2048)
        print(received_data)

        buffer += received_data

        frame = wsFrame()
        frame.parse_headers(received_data)
        full_frame_length = frame.header_length + frame.payload_length

        #make sure buffer must have the whole frame before parsing
        while len(buffer) < full_frame_length:
            buffer += handler.request.recv(2048)

        whole_frame = parse_ws_frame(buffer)

        #disconnection
        if whole_frame.opcode == 8:
            del active_connections[username]

            close_frame = generate_ws_frame(payload=b"")
            handler.request.sendall(close_frame)

            handler.request.close()
            return



        pass

    # buffer = buffer[full_frame_length:]