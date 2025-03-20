from util.response import Response
from util.multidata_parser import MultiDataParser, Part

#assume that each input Request is a multipart request
#Goal: return an OBJECT
def parse_multipart(request):
    #get boundaries
    boundary = get_boundary(request) #in string
    boundary_in_byte = boundary.encode('utf-8') #in bytes

    #deal with parts
    parts = []
    body = request.body
    # print("=====Im multi request body:=====")
    # print(request.body)
    # print("===================")
    raw_parts = body.split(boundary_in_byte)
    raw_parts = raw_parts[1:]

    #deal with all parts except last part
    for i in range(len(raw_parts)-1):
        curr_part = raw_parts[i]
        curr_part_split = curr_part.split(b'\r\n\r\n', 1) #[0] will be headers, [1] will be content
        curr_part_header = curr_part_split[0].decode('utf-8').split("\r\n") #extra line after a header?
        curr_part_content = curr_part_split[1] #the contents should remain in bytes

        headers = get_headers(curr_part_header)
        name = get_things_in_content_disposition(headers).get("name")

        part = Part(headers, name, curr_part_content)
        parts.append(part)

    return MultiDataParser(boundary, parts)

def get_boundary(request):
    content_type = request.headers.get('Content-Type')
    content_boundary_split = content_type.split(';', 1) #split the content type &  boundary
    boundary_key_value = content_boundary_split[1].split("boundary=") # split the boundary key and its VALUE
    boundary = boundary_key_value[1] #<-- we need the key

    return "--" + boundary #do i need to add --? or just get what the boundary= gives me?

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
