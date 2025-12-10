from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import Config
from flask_mail import Mail
from redis import Redis

db = SQLAlchemy()
jwt = JWTManager()
mail = Mail()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Gắn các Extension vào App
    db.init_app(app)
    jwt.init_app(app)
    mail.init_app(app)
    CORS(app, resources={r"/*": {"origins": "*"}})
    if app.config["REDIS_URL"]:
        app.redis_client = Redis.from_url(app.config["REDIS_URL"]) # type: ignore
        print("Redis Connected!")
    else:
        print("Warning: No REDIS_URL found.")

    from app.auth.utils import check_if_token_is_revoked
    jwt.token_in_blocklist_loader(check_if_token_is_revoked)    

    from app.auth.routes import auth_bp
    from app.feedback.routes import feedback_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(feedback_bp, url_prefix="/api/feedback")

    with app.app_context():
        # import models để SQLAlchemy biết cấu trúc bảng
        from app import models  # noqa: F401

        db.create_all()

    return app
