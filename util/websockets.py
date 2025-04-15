import hashlib
import base64

from util.wsFrame import wsFrame

def compute_accept(ws_key):
    #random ws key --> accept response
    guid = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
    combined_key = ws_key + guid
    hashed_combined_key = hashlib.sha1(combined_key.encode("utf-8")).digest() #digest outputs bytes, hexdigest output hexstr
    accept_response = base64.b64encode(hashed_combined_key).decode("utf-8")
    return accept_response

def parse_ws_frame(bytes_frame):
    frame = wsFrame()
    frame.parse_headers(bytes_frame)
    frame.parse_payload(bytes_frame)
    return frame


def generate_ws_frame(payload: bytes):
    frame = bytearray()

    # byte 0, fin_bit = 1,  rsv will be 000, opcode = 0001 (for text)
    byte0 = 0b10000001
    frame.append(byte0)

    # byte 1, mask_bit = 0 + payload_length
    mask_bit = 0
    payload_length = len(payload)
    if payload_length < 126:
        byte_1 = payload_length
        frame.append(byte_1)
    elif payload_length < 65536:
        byte_1 = 0b01111110 #126
        frame.append(byte_1)

        payload_len_in_bytes = payload_length.to_bytes(2, byteorder='big')
        frame.append(payload_len_in_bytes[0])
        frame.append(payload_len_in_bytes[1])
    else:  # payload_length requires 8 bytes
        byte_1 = 0b01111111 #127
        frame.append(byte_1)

        payload_length_in_bytes = payload_length.to_bytes(8, byteorder='big')
        for i in range(8):
            frame.append(payload_length_in_bytes[i])

    frame.extend(payload)
    return bytes(frame)


def test_parse_frame():
    bytes = b'\x81\xa97\x02\x9d\x12L \xf0wDq\xfcuRV\xe4bR \xa70Ra\xf5}ha\xf1{Rl\xe90\x1b \xe9wOv\xbf(\x15j\xf40J'

    expected_frame = wsFrame()
    expected_frame.fin_bit = 1
    expected_frame.opcode = 1
    expected_frame.mask_bit = 1
    expected_frame.payload_length = 41
    expected_frame.payload = b'{"messageType":"echo_client","text":"hi"}'

    actual_frame = parse_ws_frame(bytes)

    assert expected_frame.fin_bit == actual_frame.fin_bit
    assert expected_frame.opcode == actual_frame.opcode
    assert expected_frame.mask_bit == actual_frame.mask_bit
    assert expected_frame.payload_length == actual_frame.payload_length
    assert expected_frame.payload == actual_frame.payload

if __name__ == '__main__':
    test_parse_frame()