import os
import dotenv

dotenv.load_dotenv(".env.example")

#GITHUB
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET')
REDIRECT_URI = os.environ.get('REDIRECT_URI')

#Subtitles for video
TRANSCRIPTION_API_KEY = os.environ.get('TRANSCRIPTION_API_KEY')

#Google, useless for now, but for practice
# GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
# GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')