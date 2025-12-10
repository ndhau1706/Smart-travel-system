from app import db
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default="customer")
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    reviews = relationship("Review", backref="author", lazy=True)

    def __init__(self, email: str, password_hash: str, full_name: str, role: str = 'customer', is_active: bool = True):
        self.email = email
        self.password_hash = password_hash
        self.full_name = full_name
        self.role = role
        self.is_active = is_active
    
    def __repr__(self):
        return f"<User {self.email} - {self.role}>"
    
    def to_dict(self):
        """Chuyển đổi Object User thành Dictionary để trả về API"""
        return {
            "id": self.id,
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role,
            "is_active": self.is_active,
        }


class Review(db.Model):
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Float, nullable=False)
    comment = db.Column(db.Text, nullable=False)

    sentiment_score = db.Column(db.Float)
    final_score = db.Column(db.Float)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    restaurant_id = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"<Review {self.id} - Score: {self.final_score}>"
