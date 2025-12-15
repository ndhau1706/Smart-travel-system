from flask import Flask
# SỬA Ở ĐÂY: Import db, migrate từ extensions chứ KHÔNG khai báo mới
from .extensions import db, migrate 
from flask_cors import CORS
from redis import Redis
from config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 1. Gắn extension vào App
    db.init_app(app)
    migrate.init_app(app, db)
    
    CORS(app, resources={r"/*": {"origins": "*"}})

    # 2. Kết nối Redis
    if app.config.get("REDIS_URL"):
        # Lưu ý: type ignore nếu IDE báo lỗi
        app.redis_client = Redis.from_url(app.config["REDIS_URL"]) 
        print("Redis Connected!")
    else:
        print("Warning: No REDIS_URL found.")

    # 3. Đăng ký Blueprint
    from app.feedback.routes import feedback_bp
    app.register_blueprint(feedback_bp, url_prefix="/api/feedback")

    # 4. Tạo bảng Database
    with app.app_context():
        # Import models để SQLAlchemy nhận diện bảng Review
        from app.feedback import models  
        db.create_all()

    return app