import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    FIREBASE_CRED_PATH = os.getenv("FIREBASE_CRED_PATH")
    DEBUG = os.getenv("FLASK_DEBUG", "False") == "True"