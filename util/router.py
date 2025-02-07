from util.request import Request
from util.response import Response


class Router:

    def __init__(self):
        # store different routes where each info of a route will be store as a key-value pair in dict [{}, {}, {}]
        self.routes = []

    def add_route(self, method, path, action, exact_path=False):
        self.routes.append({"method": method, "path": path, "action": action, "exact_path": exact_path})

    def route_request(self, request, handler):
        # get the method & path from the req first
        request_method = request.method
        request_path = request.path

        # Matching
        for route in self.routes:
            route_method = route["method"]
            route_path = route["path"]
            if route_method == request_method:
                if route["exact_path"]:
                    if route_path == request_path:
                        route["action"](request, handler)
                        return
                else:
                    if request_path.startswith(route_path):
                        route["action"](request, handler)
                        return

        #No match occurs
        res = Response()
        res.set_status(404, "Not Found")
        res.text("404 Not Found, The page you requested " + request_path + " was not found.") #this displayed correctly
        handler.request.sendall(res.to_data())