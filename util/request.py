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
        self.body = head_body_separator[1]

        # 2) Convert the header from raw bytes to string
        header_strings = head_body_separator[0].decode("utf-8")

        # 3) [0] in header_strings will be the request_line, rest will be headers
        """
            request line contains:
                [0]--> Method type | [1]--> path | [2]--> http version | all separate by a space 
        """
        request_line = header_strings[0]
        request_line_split = request_line.split(" ")
        self.method = request_line_split[0]
        self.path = request_line_split[1]
        self.http_version = request_line_split[2]

        # 4) for all idx> 0 in header_strings[idx] --> they are all headers
        for i in range(1, len(request_line_split)):
            self.headers.append(request_line_split[i])

        # 5) Cookies



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


if __name__ == '__main__':
    test1()
