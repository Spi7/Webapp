from util.response import Response
from util.request import Request
from util.multidata_parser import MultiDataParser, Part
import os

#assume that each input Request is a multipart request
#Goal: return an OBJECT
def parse_multipart(request):
    #get boundaries
    boundary = get_boundary(request) #in string
    boundary_in_byte = b'\r\n--' + boundary.encode("utf-8")  # in bytes

    #deal with parts
    parts = []
    body = b'\r\n' + request.body #deal w first boundary
    raw_parts = body.split(boundary_in_byte)
    raw_parts = raw_parts[1:]

    #deal with all parts except last part
    for i in range(len(raw_parts)):
        curr_part = raw_parts[i]

        #print(curr_part)
        curr_part_split = curr_part.split(b'\r\n\r\n', 1) #[0] will be headers, [1] will be content
        curr_part_header = curr_part_split[0].decode('utf-8').split("\r\n") #extra line after a header?
        curr_part_content = curr_part_split[1] #the contents should remain in bytes
        #print("Curr Part Content:", curr_part_content)

        headers = get_headers(curr_part_header)
        name = get_things_in_content_disposition(headers).get("name")

        part = Part(headers, name, curr_part_content)
        parts.append(part)
    #parts[-1].content = parts[-1].content[:-2] #remove the last \r\n
    return MultiDataParser(boundary, parts)

def get_boundary(request):
    content_type = request.headers.get('Content-Type')
    content_boundary_split = content_type.split(';', 1) #split the content type &  boundary
    boundary_key_value = content_boundary_split[1].split("boundary=") # split the boundary key and its VALUE
    boundary = boundary_key_value[1].strip() #<-- we need the key

    return boundary

def get_headers(headers):
    headers_dict = {}
    for header in headers:
        if ":" not in header:
            continue
        curr_part_header_split = header.split(":")
        curr_key = curr_part_header_split[0].strip()
        curr_value = curr_part_header_split[1].strip()
        headers_dict[curr_key] = curr_value
    return headers_dict

def get_things_in_content_disposition(headers):
    content_disposition = headers.get("Content-Disposition")
    dict = {}
    if content_disposition:
        content_disposition_value_split = content_disposition.split(";")

        for content_disposition_value in content_disposition_value_split:
            if "=" not in content_disposition_value:
                continue
            curr_key = content_disposition_value.split("=")[0].strip()
            curr_value = content_disposition_value.split("=")[1].strip().strip('"')
            dict[curr_key] = curr_value

    return dict


def test1():
    request_bytes = b'POST /api/users/avatar HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\nContent-Length: 673\r\nsec-ch-ua-platform: "Windows"\r\nUser-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.36\r\nsec-ch-ua: "Chromium";v="134", "Not:A-Brand";v="24", "Google Chrome";v="134"\r\nContent-Type: multipart/form-data; boundary=----WebKitFormBoundary6CeaT91JsBxc2q0U\r\nsec-ch-ua-mobile: ?0\r\nAccept: */*\r\nOrigin: http://localhost:8080\r\nSec-Fetch-Site: same-origin\r\nSec-Fetch-Mode: cors\r\nSec-Fetch-Dest: empty\r\nReferer: http://localhost:8080/change-avatar\r\nAccept-Encoding: gzip, deflate, br, zstd\r\nAccept-Language: en-US,en;q=0.9\r\nCookie: oauth_state=a9ebbe49-27d3-4049-9d93-76e834b9a2cc; auth_token=e4850664-2244-4238-8298-3878edf27856\r\n\r\n------WebKitFormBoundary6CeaT91JsBxc2q0U\r\nContent-Disposition: form-data; name="avatar"; filename="elephant-small.jpg"\r\nContent-Type: image/jpeg\r\n\r\n\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x84\x00\x10\x10\x10\x10\x11\x10\x12\x14\x14\x12\x19\x1b\x18\x1b\x19%"\x1f\x1f"%8(+(+(8U5>55>5UK[JEJ[K\x87j^^j\x87\x9c\x83|\x83\x9c\xbd\xa9\xa9\xbd\xee\xe2\xee\xff\xff\xff\x01\x10\x10\x10\x10\x11\x10\x12\x14\x14\x12\x19\x1b\x18\x1b\x19%"\x1f\x1f"%8(+(+(8U5>55>5UK[JEJ[K\x87j^^j\x87\x9c\x83|\x83\x9c\xbd\xa9\xa9\xbd\xee\xe2\xee\xff\xff\xff\xff\xc2\x00\x11\x08\x00\x18\x00\x18\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x16\x00\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x04\x05\xff\xda\x00\x08\x01\x01\x00\x00\x00\x00\xd4\x8e\x9ds\x85\x0b\x8f\x90\x7f\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xff\xda\x00\x08\x01\x02\x10\x00\x00\x00\x95?\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xff\xda\x00\x08\x01\x03\x10\x00\x00\x00\xa9?\xff\xc4\x00&\x10\x00\x02\x01\x02\x05\x02\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x00\x12\x01\x05\x10\x13B"2\x14!$3\x82\x92\xa2\xff\xda\x00\x08\x01\x01\x00\
x01?\x00\xccf\xcc\xdf \xbc\xd0\x03\xdbo*<\xd5\xe3\x16\xfc^^]7V\\\xf7o\xab\x055\xac\x12\xee\xbb\xf5Y\xc4_\x13\t\xb6{\x807\r \x9e\xf1\x08\xf8r=\xbf\xb5C\x84\x98J\xb1\x7f"\xc7HHh\xce\
x83\xb9\x10\xd5\xea\xc8\x88\xad\xe3\xd3n\x9f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \xff\xda\x00\x08\x01\x02\x01\x01?\x00\x1f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \xff\xda\x00\x08\x01\x03\x01\x01?\x00\x1f\xff\xd9\r\n------WebKitFormBoundary6CeaT91JsBxc2q0U--\r\n'
    request = Request(request_bytes)
    multi_response = parse_multipart(request)

    assert multi_response.boundary == "----WebKitFormBoundary6CeaT91JsBxc2q0U"
    assert len(multi_response.parts) == 1

    assert multi_response.parts[0].name == "avatar"
    assert multi_response.parts[0].headers["Content-Disposition"] == 'form-data; name="avatar"; filename="elephant-small.jpg"'
    assert multi_response.parts[0].headers["Content-Type"] == "image/jpeg"

    assert multi_response.parts[0].content == b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xdb\x00\x84\x00\x10\x10\x10\x10\x11\x10\x12\x14\x14\x12\x19\x1b\x18\x1b\x19%"\x1f\x1f"%8(+(+(8U5>55>5UK[JEJ[K\x87j^^j\x87\x9c\x83|\x83\x9c\xbd\xa9\xa9\xbd\xee\xe2\xee\xff\xff\xff\x01\x10\x10\x10\x10\x11\x10\x12\x14\x14\x12\x19\x1b\x18\x1b\x19%"\x1f\x1f"%8(+(+(8U5>55>5UK[JEJ[K\x87j^^j\x87\x9c\x83|\x83\x9c\xbd\xa9\xa9\xbd\xee\xe2\xee\xff\xff\xff\xff\xc2\x00\x11\x08\x00\x18\x00\x18\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x16\x00\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x07\x04\x05\xff\xda\x00\x08\x01\x01\x00\x00\x00\x00\xd4\x8e\x9ds\x85\x0b\x8f\x90\x7f\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xff\xda\x00\x08\x01\x02\x10\x00\x00\x00\x95?\xff\xc4\x00\x15\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\xff\xda\x00\x08\x01\x03\x10\x00\
x00\x00\xa9?\xff\xc4\x00&\x10\x00\x02\x01\x02\x05\x02\x07\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x03\x04\x00\x12\x01\x05\x10\x13B"2\x14!$3\x82\x92\xa2\xff\xda\x00\x08\x01\x01\x00\
x01?\x00\xccf\xcc\xdf \xbc\xd0\x03\xdbo*<\xd5\xe3\x16\xfc^^]7V\\\xf7o\xab\x055\xac\x12\xee\xbb\xf5Y\xc4_\x13\t\xb6{\x807\r \x9e\xf1\x08\xf8r=\xbf\xb5C\x84\x98J\xb1\x7f"\xc7HHh\xce\
x83\xb9\x10\xd5\xea\xc8\x88\xad\xe3\xd3n\x9f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \xff\xda\x00\x08\x01\x02\x01\x01?\x00\x1f\xff\xc4\x00\x14\x11\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00 \xff\xda\x00\x08\x01\x03\x01\x01?\x00\x1f\xff\xd9'


if __name__ == '__main__':
    test1()