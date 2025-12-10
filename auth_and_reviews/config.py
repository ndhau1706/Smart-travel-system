import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    # 1. Cấu hình Database
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or "sqlite:///site.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 2. Bảo mật (Secret Key để ký Token)
    SECRET_KEY = os.environ.get("SECRET_KEY") or "123456"

    # 3. Cấu hình JWT (Token)
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or "123457"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)

    # 4. Cấu hình Redis (Mặc định localhost)
    REDIS_URL = os.environ.get("REDIS_URL") or "redis://localhost:6379/0"

    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER")
