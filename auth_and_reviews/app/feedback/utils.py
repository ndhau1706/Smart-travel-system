from functools import wraps
import uuid
import bleach
from textblob import TextBlob
from deep_translator import GoogleTranslator

TEST_USER_ID = uuid.UUID('12345678-1234-5678-1234-567812345678')

class MockUser:
    def __init__(self):
        # Tạo UUID ngẫu nhiên (dạng Object) để khớp với model
        # Mỗi lần gọi API sẽ là một user mới toanh
        self.id = str(TEST_USER_ID)
        self.email = "local_random_tester@fake.com"

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # Tạo user giả
        current_user = MockUser()
        # Truyền user giả vào hàm xử lý
        return f(current_user, *args, **kwargs)
    return decorated

def calculate_hybrid_score(user_rating, content):
    """
    Tính điểm lai dựa trên Rating của User (70%) và AI Sentiment (30%).
    Input: 
        - user_rating: int (1-5)
        - content: str (Nội dung review)
    Output:
        - final_score_10: float (Thang 1-10)
        - sentiment_label: str (Positive/Neutral/Negative)
    """
    
    # 1. Xử lý trường hợp không có content (User chỉ chấm sao)
    if not content or not content.strip():
        # Nếu không có text, AI không có gì để đọc -> Tin tưởng User 100%
        # Quy đổi 5 sao -> 10 điểm
        return float(user_rating * 2), classify_sentiment(user_rating)

    try:
        # 2. Sanitization (Làm sạch HTML rác) 
        clean_text = bleach.clean(str(content))

        # 3. Translation (Dịch Việt -> Anh để TextBlob hiểu) 
        # Dùng deep_translator ổn định hơn googletrans
        translator = GoogleTranslator(source='auto', target='en')
        eng_text = translator.translate(clean_text)

        # 4. NLP Analysis (Tính Polarity -1 đến 1) 
        blob = TextBlob(eng_text)
        ai_polarity = blob.sentiment.polarity 

        # 5. Normalization (Chuẩn hóa về thang 1-5 sao) 
        # Công thức: ((polarity + 1) * 2) + 1
        # VD: -1 -> 1 sao | 0 -> 3 sao | 1 -> 5 sao
        ai_star = ((ai_polarity + 1) * 2) + 1

        # 6. Hybrid Calculation (Công thức 70/30) 
        final_score_5 = (user_rating * 0.7) + (ai_star * 0.3)

        # 7. Scale to 10 (Quy đổi ra thang 10) 
        final_score_10 = round(final_score_5 * 2, 1) # Làm tròn 1 số lẻ

        # 8. Gán nhãn Sentiment (Để lưu DB phục vụ Filter/UI)
        sentiment_label = classify_sentiment(final_score_5)

        return final_score_10, sentiment_label

    except Exception as e:
        print(f"Lỗi AI Sentiment: {e}")
        # Fallback: Nếu AI lỗi mạng hoặc dịch lỗi -> Dùng điểm gốc của User
        return float(user_rating * 2), classify_sentiment(user_rating)

def classify_sentiment(score_5_scale):
    """Helper để gán nhãn dựa trên điểm hệ 5"""
    if score_5_scale >= 3.5:
        return "Positive"
    elif score_5_scale <= 2.5:
        return "Negative"
    else:
        return "Neutral"
    
