import random
from flask_mail import Message
from app import mail
from flask import current_app

def generate_otp():
    """Sinh mã OTP 6 số ngẫu nhiên"""
    return str(random.randint(100000, 999999))


def send_otp_email(to_email, otp_code) -> bool:
    """Gửi email chứa OTP"""
    msg = Message(
        subject="[Food Review] Mã xác thực đăng ký",
        recipients=[to_email],
        body=f"\n\nMã OTP của bạn là: {otp_code}\n\nMã này sẽ hết hạn sau 5 phút. Tuyệt đối không chia sẻ mã này.",
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi gửi mail: {e}")
        return False

def send_reset_email(to_email: str, otp_code: str) -> bool:
    """Gửi email chứa OTP để đặt lại mật khẩu"""
    msg = Message(
        subject="[Food Review] Yêu cầu đặt lại mật khẩu",
        recipients=[to_email],
        body=f"\n\n Mã OTP xác thực của bạn là: {otp_code}\n\nMã này sẽ hết hạn sau 5 phút. Nếu bạn không thực hiện yêu cầu này, vui lòng bỏ qua email."
    )
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Lỗi gửi mail reset: {e}")
        return False

def check_if_token_is_revoked(jwt_header, jwt_payload: dict) -> bool:
    """
    Callback function cho Flask-JWT-Extended.
    Hàm này sẽ chạy TỰ ĐỘNG mỗi khi có route dùng @jwt_required().
    
    Return:
        - True: Token bị chặn (nằm trong blacklist) -> Trả về lỗi 401
        - False: Token hợp lệ -> Cho qua
    """
    jti = jwt_payload["jti"] # Lấy ID của token
    
    try:
        # Kiểm tra xem jti này có trong Redis không
        # Key trong Redis sẽ là: blacklist:xxxx-xxxx-xxxx
        token_in_redis = current_app.redis_client.get(f"blacklist:{jti}") # type: ignore
        
        # Nếu tìm thấy trong Redis => Token đã bị revoked => Trả về True (Chặn)
        return token_in_redis is not None
        
    except Exception as e:
        print(f"Lỗi check blacklist: {e}")
        # Nếu lỗi Redis, tạm thời cho qua (hoặc chặn tùy chính sách bảo mật)
        return True