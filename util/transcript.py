from util.response import Response
from util.configuration import TRANSCRIPTION_API_KEY
from util.database import video_collection

import subprocess
import requests
import ffmpeg

"""
- `-i`: Specifies the input file.
- `-vn`: Tells FFmpeg to disable video recording.
- `-ar`: Sets the audio sampling frequency (44100 Hz in this case).
- `-ac`: Sets the number of audio channels (2 for stereo audio).
- `-b:a`: Sets the audio bitrate (192k here)
"""

def convert_video_to_audio(video_path, audio_path):
    command = "ffmpeg -i {} -vn -ar 44100 -ac 2 -b:a 192k {}".format(video_path, audio_path)
    subprocess.call(command, shell=True)

def get_video_duration(video_path):
    # command = "ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {}".format(video_path)
    # result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    probe = ffmpeg.probe(video_path)
    duration = float(probe["format"]["duration"])
    return duration

def get_transcription_id(audio_path):
    with open (audio_path, 'rb') as audio_file:
        api_url = "https://transcription-api.nico.engineer/transcribe"
        headers = {"Authorization": "Bearer " + TRANSCRIPTION_API_KEY}

        api_response = requests.post(api_url, headers=headers, files={"file": audio_file})

        if api_response.status_code != 200:
            return None
        return api_response.json().get("unique_id")


def subtitle_api(request, handler):
    res = Response()
    video_id = request.path.rsplit('/', 1)[1] #get the video_id

    video = video_collection.find_one({"video_id": video_id})
    if not video:
        res.set_status(400, "Bad Request")
        res.text("No video found")
        handler.request.sendall(res.to_data())
        return

    #if there isn't a transcription_id already stored (calling for the first time), do the api call
    transcription_id = video.get("transcription_id")
    if not transcription_id:
        res.set_status(400, "Bad Request")
        res.text("No transcription found")
        handler.request.sendall(res.to_data())
        return

    #check if transcription is ready or not by making (GET /transcriptions/:id) api call
    check_transcription_url = "https://transcription-api.nico.engineer/transcriptions/" + transcription_id
    headers = {"Authorization": "Bearer " + TRANSCRIPTION_API_KEY}
    api_response = requests.get(check_transcription_url, headers=headers)

    if api_response.status_code == 420:
        res.set_status(202, "Accepted")
        res.text("The transcription is still on progress. Please wait another 30 seconds")
        handler.request.sendall(res.to_data())
        return

    vtt_url = api_response.json().get("s3_url") #got this key from checking api/transcriptions/video_id
    vtt_response = requests.get(vtt_url)
    if vtt_response.status_code != 200:
        res.set_status(500, "Internal Server Error")
        res.text("Failed to fetch the vtt file")
        handler.request.sendall(res.to_data())
        return

    #the transcription is ready
    res.header["Content-Type"] = "text/vtt"
    res.text("Transcription is successfully progressed")
    res.body = vtt_response.content
    handler.request.sendall(res.to_data())