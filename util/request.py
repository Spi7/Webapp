class Request:

    def __init__(self, request: bytes):
        # TODO: parse the bytes of the request and populate the following instance variables

        self.body = b""
        self.method = ""
        self.path = ""
        self.http_version = ""
        self.headers = {}
        self.cookies = {}

        # 1) separate header & body
        # head_body = [0] --> request line & header | [1] --> body
        head_body_separator = request.split(b"\r\n\r\n", 1)
        if len(head_body_separator) > 1:
            self.body = head_body_separator[1]

        # 2) Convert the header from raw bytes to string
        header_strings = head_body_separator[0].decode("utf-8")
        header_strings_split = header_strings.split("\r\n")

        # 3) [0] in header_strings will be the request_line, rest will be headers
        """
            request line contains:
                [0]--> Method type | [1]--> path | [2]--> http version | all separate by a space 
        """
        request_line = header_strings_split[0]
        request_line_split = request_line.split(" ")
        self.method = request_line_split[0]
        self.path = request_line_split[1]
        self.http_version = request_line_split[2]

        # 4) for all idx> 0 in header_strings[idx] --> they are all headers
        # 5) if there are cookies header, store them
        for i in range(1, len(header_strings_split)):
            curr_header = header_strings_split[i]
            curr_header_split = curr_header.split(":", 1)
            curr_key = curr_header_split[0].strip()
            curr_value = curr_header_split[1].strip()

            if curr_key == "Cookie":
                cookie_list = curr_value.split(";")
                for cookie in cookie_list:
                    key_value_split = cookie.split("=")
                    curr_cookie_key = key_value_split[0].strip()
                    curr_cookie_value = key_value_split[1].strip()
                    self.cookies[curr_cookie_key] = curr_cookie_value
            else:
                self.headers[curr_key] = curr_value


def test1():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nConnection: keep-alive\r\n\r\n')
    assert request.method == "GET"
    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"  # note: The leading space in the header value must be removed
    assert request.body == b""  # There is no body for this request.
    # When parsing POST requests, the body must be in bytes, not str

    # This is the start of a simple way (ie. no external libraries) to test your code.
    # It's recommended that you complete this test and add others, including at least one
    # test using a POST request. Also, ensure that the types of all values are correct

def test_w_cookies():
    request = Request(b'GET / HTTP/1.1\r\nHost: localhost:8080\r\nCookie: cookie1=value1; cookie2=value2; cookie3=value3\r\nConnection: keep-alive\r\n\r\n')
    assert request.method == "GET"
    assert "Host" in request.headers
    assert request.headers["Host"] == "localhost:8080"
    assert request.body == b""

    assert len(request.cookies) == 3
    assert request.cookies["cookie1"] == "value1"
    assert request.cookies["cookie2"] == "value2"
    assert request.cookies["cookie3"] == "value3"

def test_post_w_body():
    request = Request(b'POST /path HTTP/1.1\r\nContent-Type: text/plain\r\nContent-Length: 5\r\nCookie: #### WAS RIGHT HERE \r\n\r\nhello')
    assert request.method == "POST"
    assert "Content-Type" in request.headers
    assert request.headers["Content-Type"] == "text/plain"
    assert "Content-Length" in request.headers
    assert request.headers["Content-Length"] == "5"
    assert request.body == b"hello"

if __name__ == '__main__':
    #test1()
    #test_w_cookies()
    test_post_w_body()
