import hashlib

from util.database import user_collection
from util.response import Response
from util.public_path import get_file_extension
from util.multipart import parse_multipart, get_things_in_content_disposition
import os

mime_types = {
    ".jpg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
}

os.makedirs("public/imgs/profile-pics", exist_ok=True)

def store_avatar(filename, image):
    extension = get_file_extension(filename)
    if extension not in mime_types:
        return None

    profile_dir = "public/imgs/profile-pics"
    files = []
    for file in os.listdir(profile_dir):
        if file.startswith("image") and (file.endswith(".jpg") or file.endswith(".png") or file.endswith(".gif")):
            files.append(file)
    next_num = len(files) + 1

    new_filename = "image" + str(next_num) + extension
    file_path = os.path.join(profile_dir, new_filename)

    #save the img in the dir
    with open(file_path, "wb") as f:
        f.write(image)

    return "/" + file_path

def change_avatar(request, handler):
    res = Response()
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        res.set_status(401, "Unauthorized")
        res.text("No auth token found, cannot upload img")
        handler.request.sendall(res.to_data())
        return

    hashed_auth_token = hashlib.sha256(auth_token.encode("utf-8")).hexdigest()

    parsed_multidata = parse_multipart(request) #return a MultiDataParser object

    for part in parsed_multidata.parts:
        if part.name == "avatar":
            dict = get_things_in_content_disposition(part.headers)
            file_name = dict.get("filename")
            file_path = store_avatar(file_name, part.content)
            if not file_path:
                res.set_status(403, "Forbidden")
                res.text("The file you upload ins invalid, it must be either jpg, png, or gif")
                handler.request.sendall(res.to_data())
                return
            user_collection.update_one({"session": hashed_auth_token}, {"$set": {"imageURL": file_path}})
            break

    res.text("Successfully uploaded image")
    handler.request.sendall(res.to_data())





