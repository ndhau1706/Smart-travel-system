from unittest.mock import patch
from passlib.hash import argon2
from app.models import User
from app import db


def test_register_missing_fields(test_client):
    payload = {"email": "fail@test.com", "full_name": "Test Fail"}
    response = test_client.post("api/auth/register", json=payload, content_type="application/json")

    assert response.status_code == 400
    json_data = response.get_json()
    assert "thiếu thông tin" in json_data["message"].lower()


@patch("app.auth.routes.send_otp_email")
def test_register_success(mock_send_mail, test_client):
    # Giả bộ gửi mail luôn thành công (True)
    mock_send_mail.return_value = True

    payload = {
        "email": "success@test.com",
        "password": "password123",
        "full_name": "Test Success",
    }
    response = test_client.post("/api/auth/register", json=payload, content_type="application/json")

    assert response.status_code == 200
    json_data = response.get_json()
    assert "đã gửi otp" in json_data["message"].lower()


@patch("app.auth.routes.send_otp_email")
def test_register_duplicate_email(mock_send_mail, test_client):
    mock_send_mail.return_value = True

    # Bước 1: Tạo user mẫu trong DB giả (Bỏ qua bước verify OTP, nhét thẳng vào DB)
    existing_user = User(email="duplicate@test.com", password_hash="dummyhash", full_name="Existing User")
    db.session.add(existing_user)
    db.session.commit()

    # Bước 2: Gọi API đăng ký với email y hệt
    payload = {
        "email": "duplicate@test.com",
        "password": "newpass",
        "full_name": "New User",
    }
    response = test_client.post("/api/auth/register", json=payload, content_type="application/json")

    # Bước 3: Mong đợi lỗi 409 (Conflict)
    assert response.status_code == 409
    json_data = response.get_json()
    assert "đã được sử dụng" in json_data["message"].lower()


@patch("app.auth.routes.send_otp_email")
@patch("app.auth.routes.generate_otp")
def test_verify_success(mock_gen_otp, mock_send_mail, test_client):
    # 1. Cấu hình kịch bản (Setup)
    mock_send_mail.return_value = True  # Giả vờ gửi mail OK
    mock_gen_otp.return_value = "123456"  # <--- MOCK NÂNG CAO: Ép OTP luôn là 123456

    email_test = "verify@test.com"

    # 2. Gọi API Đăng ký trước (để Server lưu OTP 123456 vào Redis)
    test_client.post(
        "/api/auth/register",
        json={"email": email_test, "password": "123", "full_name": "Test Verify"},
    )

    # 3. Gọi API Verify (Lúc này ta đã biết chắc chắn OTP là 123456)
    payload = {"email": email_test, "otp": "123456"}  # Dùng đúng số ta đã ép buộc
    response = test_client.post("/api/auth/verify", json=payload)

    # 4. Kiểm tra
    assert response.status_code == 201
    json_data = response.get_json()
    assert "thành công" in json_data["message"].lower()


def test_login_success(test_client):
    # Bước 1: Tạo User trong DB (Phải hash pass thật để login được)
    raw_password = "password123"
    hashed = argon2.hash(raw_password)

    user = User(email="login@test.com", password_hash=hashed, full_name="Login User")
    db.session.add(user)
    db.session.commit()

    # Bước 2: Gửi request Login
    response = test_client.post("/api/auth/login", json={"email": "login@test.com", "password": raw_password})

    # Bước 3: Kiểm tra
    assert response.status_code == 200
    data = response.get_json()

    # Kiểm tra phải có Token trả về
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["user"]["email"] == "login@test.com"


def test_login_fail_wrong_password(test_client):
    # Tạo User
    hashed = argon2.hash("dung")
    user = User(email="wrong@test.com", password_hash=hashed, full_name="User Wrong")
    db.session.add(user)
    db.session.commit()

    # Gửi sai pass
    response = test_client.post("/api/auth/login", json={"email": "wrong@test.com", "password": "sai"})

    assert response.status_code == 401
    json_data = response.get_json()
    assert "sai email hoặc mật khẩu" in json_data["message"].lower()


@patch('app.auth.routes.send_reset_email')
def test_forgot_password_request(mock_send_mail, test_client):
    """Test API xin cấp OTP quên mật khẩu"""
    mock_send_mail.return_value = True
    
    # 1. Tạo User mẫu
    u = User(email="forgot@test.com", password_hash="oldhash", full_name="User Forgot")
    db.session.add(u)
    db.session.commit()

    # 2. Gửi yêu cầu
    response = test_client.post('/api/auth/forgot-password', json={
        "email": "forgot@test.com"
    })

    # 3. Check kết quả
    assert response.status_code == 200
    json_data = response.get_json()
    assert "mã otp đã được gửi" in json_data["message"].lower()


@patch('app.auth.routes.send_reset_email')
@patch('app.auth.routes.generate_otp')
def test_reset_password_success(mock_gen_otp, mock_send_mail, test_client):
    """Test trọn bộ luồng: Xin OTP -> Đổi mật khẩu thành công"""
    # Setup: Ép OTP luôn là 654321
    mock_send_mail.return_value = True
    mock_gen_otp.return_value = "654321"

    email = "reset@test.com"
    
    # 1. Tạo User
    u = User(email=email, password_hash="oldhash", full_name="User Reset")
    db.session.add(u)
    db.session.commit()

    # 2. Gọi API quên mật khẩu (Để Server lưu OTP 654321 vào Redis)
    test_client.post('/api/auth/forgot-password', json={"email": email})

    # 3. Gọi API đổi mật khẩu (Dùng đúng OTP 654321)
    response = test_client.post('/api/auth/reset-password', json={
        "email": email,
        "otp": "654321",
        "new_password": "newpassword123"
    })

    # 4. Check kết quả
    assert response.status_code == 200
    json_data = response.get_json()
    assert "thành công" in json_data["message"].lower()
    

@patch('app.auth.routes.send_reset_email')
@patch('app.auth.routes.generate_otp')
def test_reset_password_wrong_otp(mock_gen_otp, mock_send_mail, test_client):
    """Test trường hợp nhập sai OTP"""
    mock_send_mail.return_value = True
    mock_gen_otp.return_value = "654321" # Server giữ số này

    email = "wrongotp@test.com"
    u = User(email=email, password_hash="oldhash", full_name="User Wrong")
    db.session.add(u)
    db.session.commit()

    # Xin OTP
    test_client.post('/api/auth/forgot-password', json={"email": email})

    # Nhập OTP sai (111111)
    response = test_client.post('/api/auth/reset-password', json={
        "email": email,
        "otp": "111111", # Sai nè
        "new_password": "newpassword123"
    })

    assert response.status_code == 400
    json_data = response.get_json()
    assert "không đúng" in json_data["message"].lower()