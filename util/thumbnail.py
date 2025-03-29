import os
import subprocess
import json
from util.response import Response
from util.database import video_collection

def get_timestamp_thumbnail(duration):
    percentage = [0, 0.25, 0.5, 0.75]
    timestamp = []
    for i in percentage:
        timestamp.append(duration * i)
    #last frame, try 0.5 frame b4
    timestamp.append(duration-0.5)
    return timestamp

def choose_thumbnail(video_path, video_id, duration):
    timestamp = get_timestamp_thumbnail(duration)
    thumbnails = []
    os.makedirs("public/videos/thumbnails/", exist_ok=True)
    for i in range(5):
        time = timestamp[i]
        thumbnail_path = "public/videos/thumbnails/" + video_id + "_" + str(i) + ".jpg"
        #frames: v 1 --> extract one frame
        command = "ffmpeg -y -ss " + str(time) + " -i " + video_path + " -frames:v 1 " + thumbnail_path
        subprocess.call(command, shell=True)
        thumbnails.append(thumbnail_path)
    return thumbnails

def set_thumbnail(request, handler):
 res = Response()
 video_id = request.path.rsplit("/", 1)[1]
 body = request.body
 body = json.loads(body)
 thumbnail_url = body.get("thumbnailURL")

 video_data = video_collection.find_one({"video_id": video_id})
 video_collection.update_one({"video_id": video_id}, {"$set": {"thumbnailURL": thumbnail_url}})
 res.json({"message": "Thumbnail successfully updated"})
 handler.request.sendall(res.to_data())


