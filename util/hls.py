import ffmpeg
import os

def encode_hls(video_path, video_name):
    directory = "public/videos/hls/" + video_name + "/"
    os.makedirs(directory, exist_ok=True)

    #Encode 144 & 480 resolution
    encode_144p(video_path, directory)
    encode_480p(video_path, directory)

    directory += "resolutions.m3u8"
    with open (directory, "w") as file:
        file.write("#EXTM3U\n")
        file.write("#EXT-X-STREAM-INF:BANDWIDTH=250000,RESOLUTION=256x144\n")
        file.write("144p.m3u8\n")
        file.write("#EXT-X-STREAM-INF:BANDWIDTH=1000000,RESOLUTION=854x480\n")
        file.write("480p.m3u8\n")
    return directory

def encode_480p(video_path, directory):
    target_url = directory + "480p.m3u8"
    #start number, indicates the naming for files 00.ts, 01.ts, etc.
    #hls_time, the duration for each hls video seg
    #vf resizes

    #if no directory found, check /480p_...
    ffmpeg.input(video_path).output(target_url, format="hls", start_number=0, hls_time=5, hls_list_size=0, hls_segment_filename=directory+"/480p_%02d.ts", vf="scale=854:480").run(quiet=True, overwrite_output=True)

def encode_144p(video_path, directory):
    target_url = directory + "144p.m3u8"
    ffmpeg.input(video_path).output(target_url, format="hls", start_number=0, hls_time=5, hls_list_size=0, hls_segment_filename=directory + "/144p_%02d.ts", vf="scale=256:144").run(quiet=True, overwrite_output=True)
