from flask import Blueprint, request, jsonify, current_app, Response
from app import db
from app.models import User
from app.auth.utils import generate_otp, send_otp_email, send_reset_email
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from passlib.hash import argon2
import bleach
import json
from typing import Tuple, Dict, Any
from flask_jwt_extended import get_jwt

auth_bp = Blueprint("auth", __name__)


# --- 1. API ĐĂNG KÝ: Lưu Redis + Gửi OTP ---
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    full_name = data.get("full_name")

    # Validate đầu vào
    if not email or not password or not full_name:
        return jsonify({"message": "Thiếu thông tin (email, password, full_name)"}), 400

    # Check xem email đã có trong Database chưa
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "Email này đã được sử dụng"}), 409

    # 1. Sinh OTP & Hash Password trước
    otp = generate_otp()
    hashed_password = argon2.hash(password)
    clean_name = bleach.clean(full_name)

    # 2. Đóng gói dữ liệu để lưu tạm vào Redis
    temp_data = {"full_name": clean_name, "password_hash": hashed_password, "otp": otp}

    # 3. Lưu vào Redis (Hết hạn sau 300s = 5 phút)
    try:
        # current_app.redis_client được khai báo bên __init__.py
        current_app.redis_client.setex(name=f"reg:{email}", time=300, value=json.dumps(temp_data)) # type: ignore
    except Exception as e:
        return jsonify({"message": "Lỗi kết nối Redis", "error": str(e)}), 500

    # 4. Gửi Email OTP
    if send_otp_email(email, otp):
        return jsonify({"message": "Đã gửi OTP. Vui lòng kiểm tra email!"}), 200
    else:
        return jsonify({"message": "Lỗi gửi email"}), 500


# --- 2. API XÁC THỰC: Check Redis -> Lưu Database ---
@auth_bp.route("/verify", methods=["POST"])
def verify_register():
    data = request.get_json()
    email = data.get("email")
    otp_input = data.get("otp")

    if not email or not otp_input:
        return jsonify({"message": "Thiếu email hoặc OTP"}), 400

    # 1. Lấy dữ liệu từ Redis ra
    redis_key = f"reg:{email}"
    stored_data_bytes = current_app.redis_client.get(redis_key) # type: ignore

    if not stored_data_bytes:
        return jsonify({"message": "OTP hết hạn hoặc không tồn tại"}), 400

    # 2. Check OTP
    stored_data = json.loads(stored_data_bytes)
    if stored_data["otp"] != otp_input:
        return jsonify({"message": "Mã OTP không đúng"}), 400

    # 3. Mọi thứ OK -> Lưu User thật vào Database
    new_user = User(
        email=email,
        full_name=stored_data["full_name"],
        password_hash=stored_data["password_hash"],  # Password đã hash sẵn trong Redis
        role="customer",
        is_active=True,
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        # 4. Xóa dữ liệu rác trong Redis
        current_app.redis_client.delete(redis_key) # type: ignore

        return (
            jsonify({"message": "Đăng ký thành công! Bạn có thể đăng nhập ngay."}),
            201,
        )
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Lỗi Database", "error": str(e)}), 500


# --- 3. LOGIN ---
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user = User.query.filter_by(email=email).first()

    if user and argon2.verify(password, user.password_hash):
        access_token = create_access_token(identity=str(user.id))
        refresh_token = create_refresh_token(identity=str(user.id))
        return (
            jsonify(
                {
                    "message": "Login thành công",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user": {
                        "name": user.full_name,
                        "email": user.email,
                        "role": user.role,
                    },
                }
            ),
            200,
        )

    return jsonify({"message": "Sai email hoặc mật khẩu"}), 401

# --- 4. QUÊN MẬT KHẨU: Gửi OTP (Redis TTL 300s) ---
@auth_bp.route('/forgot-password', methods=['POST'])
def forgot_password() -> Tuple[Response, int]:
    data: Dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({"message": "Dữ liệu không hợp lệ"}), 400

    email: str = data.get('email', '')
    if not email:
        return jsonify({"message": "Vui lòng nhập email"}), 400

    # 1. Kiểm tra user có tồn tại không
    user = User.query.filter_by(email=email).first()
    
    # Dù email không tồn tại vẫn báo thành công 
    # để Hacker không dò được danh sách email của hệ thống.
    if not user:
        return jsonify({"message": "Nếu email tồn tại, mã OTP đã được gửi."}), 200

    # 2. Sinh OTP
    otp = generate_otp()

    # 3. Lưu OTP vào Redis (Key: reset:{email})
    # Chỉ cần lưu OTP thôi, không cần lưu pass hay tên vì user đã có trong DB
    redis_data = {
        "otp": otp
    }
    
    try:
        current_app.redis_client.setex( # type: ignore
            name=f"reset:{email}",
            time=300,  
            value=json.dumps(redis_data)
        )
    except Exception as e:
        return jsonify({"message": "Lỗi kết nối Redis", "error": str(e)}), 500

    # 4. Gửi Email (Dùng hàm mới viết trong utils.py)
    if send_reset_email(email, otp):
        return jsonify({"message": "Nếu email tồn tại, mã OTP đã được gửi."}), 200
    else:
        return jsonify({"message": "Lỗi gửi email"}), 500


# --- 5. ĐẶT LẠI MẬT KHẨU: Check OTP Redis -> Update DB ---
@auth_bp.route('/reset-password', methods=['POST'])
def reset_password() -> Tuple[Response, int]:
    data: Dict[str, Any] | None = request.get_json()
    if not data:
        return jsonify({"message": "No data"}), 400

    email: str = data.get('email', '')
    otp_input: str = data.get('otp', '')
    new_password: str = data.get('new_password', '')

    if not email or not otp_input or not new_password:
        return jsonify({"message": "Thiếu thông tin (email, otp, new_password)"}), 400

    # 1. Lấy OTP từ Redis ra check
    redis_key = f"reset:{email}"
    stored_data_bytes = current_app.redis_client.get(redis_key) # type: ignore

    if not stored_data_bytes:
        return jsonify({"message": "Mã OTP đã hết hạn hoặc không tồn tại"}), 400

    stored_data = json.loads(stored_data_bytes)
    
    if stored_data['otp'] != otp_input:
        return jsonify({"message": "Mã OTP không đúng"}), 400

    # 2. OTP đúng -> Tiến hành đổi mật khẩu
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "Người dùng không tồn tại"}), 404

    # 3. Hash mật khẩu mới (Argon2)
    user.password_hash = argon2.hash(new_password)

    try:
        db.session.commit() # Lưu vào DB

        # 4. Xóa OTP cũ trong Redis để không dùng lại được nữa
        current_app.redis_client.delete(redis_key) # type: ignore
        
        return jsonify({"message": "Đặt lại mật khẩu thành công! Hãy đăng nhập lại."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Lỗi Database", "error": str(e)}), 500
    
# --- 6. CẤP LẠI ACCESS TOKEN (REFRESH TOKEN FLOW) ---
@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True) # Chỉ chấp nhận Refresh Token
def refresh() -> Tuple[Response, int]:
    """
    API dùng để xin cấp lại Access Token mới khi cái cũ hết hạn.
    Yêu cầu: Phải gửi kèm Refresh Token ở Header (Bearer Token).
    """
    try:
        # 1. Lấy User ID từ Refresh Token đang gửi lên
        current_user_id = get_jwt_identity()
        
        # 2. Tạo một Access Token mới tinh (Hạn 15 phút)
        new_access_token = create_access_token(identity=current_user_id)
        
        # 3. Trả về cho Client
        return jsonify({"access_token": new_access_token}), 200
        
    except Exception as e:
        return jsonify({"message": "Lỗi cấp lại token", "error": str(e)}), 500
    

# --- 7. ĐĂNG XUẤT (LOGOUT - BLACKLIST TOKEN) ---
@auth_bp.route('/logout', methods=['POST'])
@jwt_required() # <--- Bắt buộc phải có Token mới cho logout
def logout() -> Tuple[Response, int]:
    """
    Đăng xuất: Đưa Access Token hiện tại vào Blacklist Redis.
    Token này sẽ bị vô hiệu hóa ngay lập tức cho đến khi hết hạn tự nhiên.
    """
    try:
        # 1. Lấy thông tin từ Token hiện tại
        jti = get_jwt()["jti"]  # ID của Token
        exp = get_jwt()["exp"]  # Thời điểm hết hạn (Timestamp)
        
        # 2. Tính thời gian sống còn lại (TTL) của Token
        # Redis cần TTL tính bằng giây. 
        # Token còn sống bao lâu thì set bấy nhiêu. Token chết rồi thì Redis tự xóa key.
        import time
        now = int(time.time())
        ttl = exp - now
        
        # 3. Lưu vào Redis Blacklist
        if ttl > 0:
            current_app.redis_client.setex( # type: ignore
                name=f"blacklist:{jti}",
                time=ttl,
                value="revoked"
            )
            
        return jsonify({"message": "Đăng xuất thành công"}), 200
        
    except Exception as e:
        return jsonify({"message": "Lỗi đăng xuất", "error": str(e)}), 500
    
# --- 8. LẤY THÔNG TIN NGƯỜI DÙNG HIỆN TẠI (GET ME) ---
@auth_bp.route('/me', methods=['GET'])
@jwt_required() 
def get_current_user() -> Tuple[Response, int]:
    """
    API lấy thông tin profile của user đang đăng nhập.
    Frontend sẽ gọi API này ngay sau khi Login thành công để lấy Avatar/Tên hiển thị.
    """
    try:
        # 1. Lấy ID user từ Token (đã được giải mã)
        user_id = get_jwt_identity()
        
        # 2. Tìm trong Database
        user = User.query.get(user_id)
        
        # 3. Case hy hữu: Token còn hạn nhưng User đã bị xóa khỏi DB
        if not user:
            return jsonify({"message": "Người dùng không tồn tại"}), 404
            
        # 4. Trả về JSON (Dùng hàm to_dict vừa viết)
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        return jsonify({"message": "Lỗi lấy thông tin", "error": str(e)}), 500