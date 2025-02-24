import socketserver
from util.request import Request
from util.router import Router
from util.hello_path import hello_path
from util.public_path import public_path
#from util.chat_path import select_function
from util.chat_path import get_message, create_message, select_chat_or_reaction
from util.auth_path import registration, login, logout

class MyTCPHandler(socketserver.BaseRequestHandler):

    def __init__(self, request, client_address, server):
        self.router = Router()
        self.router.add_route("GET", "/hello", hello_path, True)
        # TODO: Add your routes here
        #Static Files
        self.router.add_route("GET", "/public", public_path, False)
        self.router.add_route("GET", "/", public_path, True)
        self.router.add_route("GET", "/chat", public_path, True)
        #/api/chats files & /api/reactions
        #self.router.add_route("*", "/api/chats", select_function, False)
        self.router.add_route("GET", "/api/chats", get_message, True)
        self.router.add_route("POST", "/api/chats", create_message, True)
        self.router.add_route("PATCH", "/api", select_chat_or_reaction, False)
        self.router.add_route("DELETE", "/api", select_chat_or_reaction, False)
        #HW2, render pages
        self.router.add_route("GET", "/register", public_path, True)
        self.router.add_route("GET", "/login", public_path, True)
        self.router.add_route("GET", "/settings", public_path, True)
        self.router.add_route("GET", "/search-users", public_path, True)
        #HW2, register, login, logout
        self.router.add_route("POST", "/register", registration, False)
        self.router.add_route("POST", "/login", login, False)
        self.router.add_route("GET", "/logout", logout, True)
        super().__init__(request, client_address, server)

    def handle(self):
        received_data = self.request.recv(2048)
        print(self.client_address)
        print("--- received data ---")
        print(received_data)
        print("--- end of data ---\n\n")
        request = Request(received_data)

        self.router.route_request(request, self)


def main():
    host = "0.0.0.0"
    port = 8080
    socketserver.TCPServer.allow_reuse_address = True

    server = socketserver.TCPServer((host, port), MyTCPHandler)

    print("Listening on port " + str(port))
    server.serve_forever()


if __name__ == "__main__":
    main()
