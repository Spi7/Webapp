# Full Stack Chat & Web Application

A Python based full-stack web application with the following features:
- Authentications
    - Account Registration & Login (token-based)
    - Sign in with Guthub (Github OAuth authentication / API Call)
    - Two Factor Authentication (TOTP)
- User Profile
    - Dicebear API call (avatar generation)
    - Avatar upload and profile customization
- VideoTube
    - Allow user to upload videos, set thumbnails, pick certain resolutions 144p / 360p using ffmpeg
    - Auto generated subtitle for videos under 30 seconds (transcription API)
- WebSocket
    - WebSocket Echo System
    - A drawing board
    - Direct Messaging
    - Video-Calls (WebRTC)

###Requirements
- Docker + Docker Compose
- Python 3.10+
- MongoDB

### Setup Instructions
1. Clone this repo
2. cd to your project
3. Open terminal and run "pip install -r requirements.txt"
4. In terminal run "docker compose -f docker-compose.db-only.yml up --build -d"
5. In terminal run "python server.py" or "python3 server.py" or go to server.py file and click on the start/run button
6. Open a web browser and go to http://localhost:8080
