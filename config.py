import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY          = os.getenv("SECRET_KEY")
    FIREBASE_CRED_PATH  = os.getenv("FIREBASE_CRED_PATH")
    STORAGE_BUCKET      = os.getenv("FIREBASE_STORAGE_BUCKET")
    JWT_EXPIRY_HOURS    = int(os.getenv("JWT_EXPIRY_HOURS", 24))
    DEBUG               = os.getenv("FLASK_DEBUG", "False") == "True"
    MAX_FILE_SIZE       = 10 * 1024 * 1024  # 10MB