from util.response import Response

mime_types = {
    ".text": "text/plain",
    ".html" : "text/html",
    ".css" : "text/css",
    ".js" : "text/javascript",
    ".png" : "image/png",
    ".jpg" : "image/jpeg",
    ".json" : "application/json",
    ".ico": "image/x-icon",
    ".gif": "image/gif",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".mp4": "video/mp4"
}

def get_file_extension(file_name):
    file_split = file_name.rsplit(".",1)
    if len(file_split) == 1:
        return "" #No extension
    return "." + file_split[1]

def public_path(request, handler):
    res = Response()
    file_path = ""

    if request.path == "/":
        file_path = "public/index.html"
    elif request.path == "/chat":
        file_path = "public/chat.html"
    elif request.path == "/register":
        file_path = "public/register.html"
    elif request.path == "/login":
        file_path = "public/login.html"
    elif request.path == "/search-users":
        file_path = "public/search-users.html"
    elif request.path == "/settings":
        file_path = "public/settings.html"
    elif request.path == "/change-avatar":
        file_path = "public/change-avatar.html"
    elif request.path.startswith("/videotube"):
        if request.path.startswith("/videotube/upload"):
            file_path = "public/upload.html"
        elif request.path.startswith("/videotube/videos"):
            file_path = "public/view-video.html"
        else:
            file_path = "public/videotube.html"
    else:
        file_path = request.path.split("/public", 1)[1]
        file_path = "public" + file_path

    try:
        with open(file_path, "rb") as currfile:
            file_content = currfile.read()
            file_extension = get_file_extension(file_path)
            mime_type = mime_types.get(file_extension)

            if file_extension == ".html":
                with open("public/layout/layout.html", "r", encoding="utf-8") as layoutfile:
                    layout_content = layoutfile.read()
                    rendered = layout_content.replace("{{content}}", file_content.decode("utf-8"))
                    res.text(rendered)
            else:
                res.bytes(file_content)

            res.header["Content-Type"] = mime_type
            handler.request.sendall(res.to_data())
    except FileNotFoundError:
        res.set_status(404, "Not Found")
        res.text("404 Not Found, " + request.path + "| " + file_path + " was not found.")
        handler.request.sendall(res.to_data())

