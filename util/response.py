import json
from email import charset


class Response:
    def __init__(self):
        self.status_code = "200"
        self.status_message = "OK"
        self.body = b""
        self.headers = {
            "Content-Type": "text/plain, charset=utf-8",
            "Content-Length": "0"
        }
        self.cookies = {}

    def set_status(self, code, text):
        #no matter if it's a 300/400/500, just modify the status code and its text from the default
        self.status_code = code
        self.status_message = text
        return self

    def headers(self, headers):
        for curr_header, curr_value in headers.items():
            self.headers[curr_header] = curr_value
        return self

    def cookies(self, cookies):
        #store all the cookies Set-Cookies haven't set up yet at this stage
        for curr_key, curr_value in cookies.items():
            self.cookies[curr_key] = {"value": curr_value, "maxAge": "3600"}
        return self

    def bytes(self, data):
        self.body += data
        self.headers["Content-Length"] = str((len(self.body))) #update content length everytime? or should i update it all at once in to_data?
        return self

    def text(self, data):
        return self.bytes(data.encode('utf-8')) #convert the data to bytes

    def json(self, data):
        self.body = json.dumps(data).encode('utf-8')
        self.headers["Content-Type"] = "application/json"
        return self

    def to_data(self):
        #Set cookie with expiration date? directives? check on that

        # 1) first line of the response
        status_line = "HTTP/1.1" + " " + self.status_code + " " + self.status_message + "\r\n"

        # 2) for security use, add MIME nosniff
        self.headers["X-Content-Type-Options"] = "nosniff"

        # 3) Get the headers into 1 string
        headers = ""
        for curr_header, curr_value in self.headers.items():
            headers += curr_header + ": " + curr_value + "\r\n"

        # 4) Get the cookies into 1 string
        cookies = ""
        for cookie_key, cookie_value in self.cookies.items():
            cookies += "Set-Cookie: " + cookie_key + "=" + cookie_value["value"]
            cookies += "; Max-Age=" + cookie_value["maxAge"] + "\r\n"

        #either last header or last cookie will only have 1 \r\n, so we will manually
        #add another \r\n to distinguish body from others
        response = (status_line + headers + cookies + "\r\n").encode('utf-8') + self.body

        return response


def test1():
    res = Response()
    res.text("hello")
    expected = b'HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nContent-Length: 5\r\n\r\nhello'
    actual = res.to_data()


if __name__ == '__main__':
    test1()
