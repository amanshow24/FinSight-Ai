import jwt
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import request

# Simple string — NOT related to Firebase key
JWT_SECRET   = "finsense_jwt_simple_secret_2026"
EXPIRY_HOURS = 24

def generate_token(uid, email):
    payload = {
        "uid":   uid,
        "email": email,
        "exp":   datetime.utcnow() + timedelta(hours=EXPIRY_HOURS),
        "iat":   datetime.utcnow()
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token

def verify_token(token):
    try:
        payload = jwt.decode(
            token, 
            JWT_SECRET, 
            algorithms=["HS256"]
        )
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        if not token:
            return {"message": "Token is missing!"}, 401
        payload = verify_token(token)
        if not payload:
            return {"message": "Token is invalid or expired!"}, 401
        request.uid   = payload["uid"]
        request.email = payload["email"]
        return f(*args, **kwargs)
    return decorated