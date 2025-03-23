import hashlib
from util.response import Response
from util.database import user_collection, video_collection
from util.multipart import parse_multipart, get_things_in_content_disposition
from util.public_path import get_file_extension
from util.transcript import get_video_duration, get_transcription_id, subtitle_api, convert_video_to_audio
from datetime import datetime, date
import uuid
import json
import os

VIDEO_FILE_PATH = "public/videos"
os.makedirs(VIDEO_FILE_PATH, exist_ok=True)

def select_video_method(request, handler):
    method = request.method
    if method == "GET":
        if request.path == "/api/videos":
            get_all_videos(request, handler)
        elif request.path.startswith("/api/videos"):
            get_one_video(request, handler)
    elif method == "POST":
        if request.path.startswith("/api/videos"):
            post_video(request, handler)

def store_video(video_content):
    files = []
    for file in os.listdir(VIDEO_FILE_PATH):
        if file.startswith("video") and file.endswith(".mp4"):
            files.append(file)
    next_num = len(files) + 1

    new_filename = "video" + str(next_num) + ".mp4"
    file_path = os.path.join(VIDEO_FILE_PATH, new_filename)

    #save the video in the files
    with open(file_path, "wb") as f:
        f.write(video_content)

    return VIDEO_FILE_PATH + "/" + new_filename


def post_video(request, handler):
    res = Response()
    auth_token = request.cookies.get("auth_token")
    if not auth_token:
        res.set_status(401, "Unauthorized")
        res.text("No auth token found for posting video")
        handler.request.sendall(res.to_data())
        return
    hashed_auth_token = hashlib.sha256(auth_token.encode()).hexdigest()
    user_data = user_collection.find_one({"session": hashed_auth_token})
    user_id = user_data["user_id"]

    parsed_data = parse_multipart(request) #MultiData
    parts = parsed_data.parts

    title = ""
    description = ""
    video_path = ""

    for part in parts:
        if part.name == "title":
            title = part.content.decode("utf-8")
        elif part.name == "description":
            description = part.content.decode("utf-8")
        elif part.name == "video":
            things_in_content_disposition = get_things_in_content_disposition(part.headers)
            file_name = things_in_content_disposition.get("filename")

            extension = get_file_extension(file_name)
            if extension != ".mp4":
                res.set_status(400, "Bad request")
                res.json({"error": "Invalid file extension"})
                handler.request.sendall(res.to_data())
                return
            video_content = part.content #keep it in bytes
            video_path = store_video(video_content)

    video_id = str(uuid.uuid4()) #generate an unique id for video
    created_at = date.today().strftime("%B %d, %Y") #%B --> convert MM to Months in English, %d--> day, with 0 padding if its single dig, %Y-->Year
    video_data = {
        "video_id": video_id,
        "user_id": user_id,
        "title": title,
        "description": description,
        "video_path": video_path,
        "created_at": created_at
    }

    video_duration = get_video_duration(video_path)
    if video_duration <= 60: #at max 1 minute
        audio_path = video_path.replace(".mp4", ".mp3")
        convert_video_to_audio(video_path, audio_path)

        transcription_id = get_transcription_id(audio_path)
        if transcription_id:
            video_data["transcription_id"] = transcription_id

    video_collection.insert_one(video_data)
    res.json({"id": video_id})
    handler.request.sendall(res.to_data())

def get_all_videos(request, handler):
    res = Response()

    video_data = list(video_collection.find({}, {"_id": 0}))  # contain all the videos

    all_videos = []
    for video in video_data:
        curr_video_info = {
            "author_id": video["user_id"],
            "title": video["title"],
            "description": video["description"],
            "video_path": video["video_path"],
            "created_at": video["created_at"],
            "id": video["video_id"]
        }
        all_videos.append(curr_video_info)

    res.json({"videos": all_videos})
    handler.request.sendall(res.to_data())


def get_one_video(request, handler):
    res = Response()

    video_id = request.path.rsplit("/", 1)[1] #get the video id
    this_video = video_collection.find_one({"video_id": video_id})
    video_data = {
        "author_id": this_video["user_id"],
        "title": this_video["title"],
        "description": this_video["description"],
        "video_path": this_video["video_path"],
        "created_at": this_video["created_at"],
        "id": this_video["video_id"]
    }

    res.json({"video": video_data})
    handler.request.sendall(res.to_data())

