import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/complaint_app')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)
    SECRET_KEY = os.getenv('SECRET_KEY', 'flask-secret-key')
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']