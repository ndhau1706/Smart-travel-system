from ..extensions import db 
# XÓA DÒNG NÀY: from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime, timezone 

class Review(db.Model):
    __tablename__ = 'reviews'

    # SỬA DÒNG NÀY: Dùng db.String(36) hoặc db.Uuid (nếu SQLAlchemy > 2.0) cho tương thích mọi DB
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # SỬA DÒNG NÀY: Lưu UUID dưới dạng String để an toàn nhất
    user_id = db.Column(db.String(36), nullable=False, index=True)
    
    # ... các trường khác giữ nguyên ...
    place_id = db.Column(db.String(100), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    content = db.Column(db.Text, nullable=True)
    sentiment = db.Column(db.String(50), nullable=True)
    final_score = db.Column(db.Float, default=0.0, index=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Cập nhật __init__ để đảm bảo user_id là string
    def __init__(self, user_id, place_id, rating, content=None, sentiment=None, final_score=0.0):
        self.user_id = str(user_id) # Ép kiểu string ngay khi khởi tạo
        self.place_id = place_id
        self.rating = rating
        self.content = content
        self.sentiment = sentiment
        self.final_score = final_score

    # ... hàm to_dict giữ nguyên ...
    def to_dict(self):
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "place_id": self.place_id,
            "rating": self.rating,
            "content": self.content,
            "sentiment": self.sentiment,
            "final_score": self.final_score,
            "created_at": self.created_at.isoformat()
        }