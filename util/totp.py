from util.response import Response
from util.database import user_collection
import hashlib
import pyotp
import time

def enable_totp(request, handler):
    res = Response()

    auth_token = request.cookies.get('auth_token')
    if not auth_token:
        res.set_status(401, "Unauthorized")
        res.text("You are unauthorized, no authentication token found")
        handler.request.sendall(res.to_data())

    hashed_auth_token = hashlib.sha256(auth_token.encode('utf-8')).hexdigest()
    user_data = user_collection.find_one({'session': hashed_auth_token})

    if user_data:
        user_id = user_collection.find_one({'session': hashed_auth_token})['user_id']
        totp_secret = pyotp.random_base32()
        user_collection.update_one({"user_id": user_id}, {"$set": {"totp_secret": totp_secret}})
        res.json({"secret": totp_secret})
    else: # no user data found
        res.set_status(401, "Unauthorized")
        res.text("Invalid authentication token, no user found")
    handler.request.sendall(res.to_data())

def verify_totp(totp_code, user_data):
    totp_secret = user_data.get("totp_secret")
    if not totp_code or not totp_secret:
        return False

    totp = pyotp.TOTP(totp_secret)
    return totp.verify(totp_code)
