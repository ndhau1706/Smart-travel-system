"""
Authentication API routes
"""
import asyncio
import hashlib
import hmac
import json
import os
import secrets
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import Optional

from app.core.database import get_db
from app.core.email import render_otp_email, send_email
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id
)
from app.core.config import settings
from app.modules.auth.models import User, UserRole, OtpCode, OtpPurpose
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    RefreshTokenRequest,
    TokenResponse,
    RegisterStartRequest,
    RegisterVerifyRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    FirebaseLoginRequest,
)
from app.shared.schemas import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


_firebase_initialized = False


def _ensure_firebase():
    global _firebase_initialized
    if _firebase_initialized:
        return

    try:
        import firebase_admin  # type: ignore
        from firebase_admin import credentials  # type: ignore
    except Exception as e:  # pragma: no cover
        raise RuntimeError("firebase-admin chưa được cài đặt") from e

    if firebase_admin._apps:  # type: ignore[attr-defined]
        _firebase_initialized = True
        return

    options = {}
    project_id = os.environ.get("FIREBASE_PROJECT_ID") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    if project_id:
        options["projectId"] = project_id

    # Use Application Default Credentials on Cloud Run (no key file committed).
    try:
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred, options=options)
    except Exception:
        # Fallback: initialize without explicit credentials; verify_id_token still works using public keys.
        firebase_admin.initialize_app(options=options)

    _firebase_initialized = True


def _otp_settings() -> tuple[int, int, int]:
    ttl_min = int(os.environ.get("OTP_TTL_MIN", "10") or 10)
    max_attempts = int(os.environ.get("OTP_MAX_ATTEMPTS", "5") or 5)
    resend_limit = int(os.environ.get("OTP_RESEND_LIMIT_PER_HOUR", "5") or 5)
    return ttl_min, max_attempts, resend_limit


def _hash_otp(*, email: str, purpose: str, otp: str) -> str:
    key = (settings.SECRET_KEY or "otp").encode("utf-8")
    msg = f"{purpose}:{email.strip().lower()}:{otp.strip()}".encode("utf-8")
    return hmac.new(key, msg, hashlib.sha256).hexdigest()


def _generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


async def _send_otp_email(*, email: str, otp: str, ttl_min: int, title: str) -> None:
    subject, text, html = render_otp_email(code=otp, ttl_minutes=ttl_min, title=title)
    await asyncio.to_thread(send_email, to_email=email, subject=subject, html=html, text=text)


@router.post("/login", response_model=dict)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Login with email and password"""
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(request.password, user.hashed_password):
        return error_response("E1001", "Email hoặc mật khẩu không đúng")
    
    if not user.is_active:
        return error_response("E1004", "Tài khoản đã bị vô hiệu hóa")
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return success_response(
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        message="Đăng nhập thành công"
    )


@router.post("/firebase", response_model=dict)
async def firebase_login(request: FirebaseLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Login/Register via Firebase Authentication.

    Frontend sends a Firebase ID token. Backend verifies it and issues internal JWT tokens
    (so existing protected APIs keep working without changing the frontend auth header format).
    """
    try:
        _ensure_firebase()
        from firebase_admin import auth as firebase_auth  # type: ignore

        decoded = firebase_auth.verify_id_token(request.id_token)
    except Exception:
        return error_response("E1020", "Firebase token không hợp lệ")

    email = (decoded.get("email") or "").strip().lower()
    if not email:
        return error_response("E1021", "Firebase token thiếu email")

    name = (decoded.get("name") or decoded.get("displayName") or "").strip()
    avatar = decoded.get("picture")
    email_verified = bool(decoded.get("email_verified") or False)

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        # Create a local user row for the Firebase identity.
        # We still need a password hash due to the current schema (not used for Firebase login).
        random_secret = secrets.token_urlsafe(32)
        user = User(
            email=email,
            name=name or email.split("@", 1)[0],
            avatar=avatar,
            hashed_password=get_password_hash(random_secret),
            is_verified=email_verified,
            is_active=True,
        )
        db.add(user)
        await db.flush()
        await db.refresh(user)
    else:
        updated = False
        if name and user.name != name:
            user.name = name
            updated = True
        if avatar and user.avatar != avatar:
            user.avatar = avatar
            updated = True
        if email_verified and not user.is_verified:
            user.is_verified = True
            updated = True
        if updated:
            user.updated_at = datetime.utcnow()
            await db.flush()
            await db.refresh(user)

    if not user.is_active:
        return error_response("E1004", "Tài khoản đã bị vô hiệu hóa")

    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})

    return success_response(
        data={
            "user": UserResponse.model_validate(user).model_dump(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        message="Đăng nhập Firebase thành công",
    )


@router.post("/register/start", response_model=dict)
async def register_start(request: RegisterStartRequest, db: AsyncSession = Depends(get_db)):
    """Start registration flow by sending an OTP code to email."""
    email = request.email.strip().lower()
    if request.password != request.confirm_password:
        return error_response("E1010", "Mật khẩu xác nhận không khớp")

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        return error_response("E1005", "Email đã được sử dụng")

    ttl_min, _, resend_limit = _otp_settings()
    now = datetime.utcnow()

    count_res = await db.execute(
        select(func.count(OtpCode.id)).where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.REGISTER.value,
            OtpCode.created_at >= (now - timedelta(hours=1)),
        )
    )
    if (count_res.scalar() or 0) >= resend_limit:
        return error_response("E1011", "Bạn đã yêu cầu OTP quá nhiều lần. Vui lòng thử lại sau.")

    await db.execute(
        update(OtpCode)
        .where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.REGISTER.value,
            OtpCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )

    otp = _generate_otp()
    hashed_password = get_password_hash(request.password)

    db.add(
        OtpCode(
            email=email,
            purpose=OtpPurpose.REGISTER.value,
            code_hash=_hash_otp(email=email, purpose=OtpPurpose.REGISTER.value, otp=otp),
            context=json.dumps({"name": request.name, "password_hash": hashed_password}),
            attempts=0,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_min),
        )
    )

    title = os.environ.get("EMAIL_FROM_NAME", "Smart Travel").strip() or "Smart Travel"
    try:
        await _send_otp_email(email=email, otp=otp, ttl_min=ttl_min, title=title)
    except Exception:
        await db.rollback()
        return error_response("E1012", "Gửi OTP thất bại. Vui lòng thử lại sau.")

    return success_response(data={"email": email}, message="Đã gửi OTP qua email")


@router.post("/register/verify", response_model=dict)
async def register_verify(request: RegisterVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and create the user account."""
    email = request.email.strip().lower()
    otp = request.otp.strip()

    ttl_min, max_attempts, _ = _otp_settings()
    now = datetime.utcnow()

    code_res = await db.execute(
        select(OtpCode)
        .where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.REGISTER.value,
            OtpCode.consumed_at.is_(None),
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    code = code_res.scalar_one_or_none()
    if not code:
        return error_response("E1013", "OTP không tồn tại hoặc đã hết hạn")

    if code.expires_at < now:
        code.consumed_at = now
        return error_response("E1014", f"OTP đã hết hạn (hết hạn sau {ttl_min} phút). Vui lòng yêu cầu mã mới.")

    if (code.attempts or 0) >= max_attempts:
        code.consumed_at = now
        return error_response("E1015", "Bạn đã nhập sai OTP quá nhiều lần. Vui lòng yêu cầu mã mới.")

    expected_hash = _hash_otp(email=email, purpose=OtpPurpose.REGISTER.value, otp=otp)
    if not hmac.compare_digest(expected_hash, code.code_hash):
        code.attempts = (code.attempts or 0) + 1
        return error_response("E1016", "OTP không đúng")

    # Consume OTP before creating the account.
    code.consumed_at = now

    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        return error_response("E1005", "Email đã được sử dụng")

    try:
        context = json.loads(code.context or "{}")
    except Exception:
        context = {}

    name = (context.get("name") or "").strip() or email.split("@", 1)[0]
    password_hash = context.get("password_hash")
    if not password_hash:
        return error_response("E1017", "Không thể hoàn tất đăng ký. Vui lòng thử lại.")

    new_user = User(
        email=email,
        name=name,
        hashed_password=password_hash,
        is_verified=True,
    )

    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)

    access_token = create_access_token(data={"sub": new_user.id})
    refresh_token = create_refresh_token(data={"sub": new_user.id})

    return success_response(
        data={
            "user": UserResponse.model_validate(new_user).model_dump(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
        message="Đăng ký thành công",
    )


@router.post("/register", response_model=dict)
async def register(request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Register a new user"""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        return error_response("E1005", "Email đã được sử dụng")
    
    # Create new user
    hashed_password = get_password_hash(request.password)
    new_user = User(
        email=request.email,
        name=request.name,
        phone=request.phone,
        hashed_password=hashed_password
    )
    
    db.add(new_user)
    await db.flush()
    await db.refresh(new_user)
    
    # Create tokens
    access_token = create_access_token(data={"sub": new_user.id})
    refresh_token = create_refresh_token(data={"sub": new_user.id})
    
    return success_response(
        data={
            "user": UserResponse.model_validate(new_user).model_dump(),
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        message="Đăng ký thành công"
    )


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send OTP for resetting password. Always responds success for privacy."""
    email = request.email.strip().lower()
    ttl_min, _, resend_limit = _otp_settings()
    now = datetime.utcnow()

    count_res = await db.execute(
        select(func.count(OtpCode.id)).where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.RESET_PASSWORD.value,
            OtpCode.created_at >= (now - timedelta(hours=1)),
        )
    )
    if (count_res.scalar() or 0) >= resend_limit:
        return error_response("E1011", "Bạn đã yêu cầu OTP quá nhiều lần. Vui lòng thử lại sau.")

    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if not user:
        return success_response(data={"email": email}, message="Nếu email tồn tại, OTP sẽ được gửi.")

    await db.execute(
        update(OtpCode)
        .where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.RESET_PASSWORD.value,
            OtpCode.consumed_at.is_(None),
        )
        .values(consumed_at=now)
    )

    otp = _generate_otp()
    db.add(
        OtpCode(
            email=email,
            purpose=OtpPurpose.RESET_PASSWORD.value,
            code_hash=_hash_otp(email=email, purpose=OtpPurpose.RESET_PASSWORD.value, otp=otp),
            context=None,
            attempts=0,
            created_at=now,
            expires_at=now + timedelta(minutes=ttl_min),
        )
    )

    title = os.environ.get("EMAIL_FROM_NAME", "Smart Travel").strip() or "Smart Travel"
    try:
        await _send_otp_email(email=email, otp=otp, ttl_min=ttl_min, title=title)
    except Exception:
        await db.rollback()
        return error_response("E1012", "Gửi OTP thất bại. Vui lòng thử lại sau.")

    return success_response(data={"email": email}, message="Đã gửi OTP đặt lại mật khẩu")


@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and reset password."""
    email = request.email.strip().lower()
    otp = request.otp.strip()

    if request.new_password != request.confirm_password:
        return error_response("E1010", "Mật khẩu xác nhận không khớp")

    ttl_min, max_attempts, _ = _otp_settings()
    now = datetime.utcnow()

    code_res = await db.execute(
        select(OtpCode)
        .where(
            OtpCode.email == email,
            OtpCode.purpose == OtpPurpose.RESET_PASSWORD.value,
            OtpCode.consumed_at.is_(None),
        )
        .order_by(OtpCode.created_at.desc())
        .limit(1)
    )
    code = code_res.scalar_one_or_none()
    if not code:
        return error_response("E1013", "OTP không tồn tại hoặc đã hết hạn")

    if code.expires_at < now:
        code.consumed_at = now
        return error_response("E1014", f"OTP đã hết hạn (hết hạn sau {ttl_min} phút). Vui lòng yêu cầu mã mới.")

    if (code.attempts or 0) >= max_attempts:
        code.consumed_at = now
        return error_response("E1015", "Bạn đã nhập sai OTP quá nhiều lần. Vui lòng yêu cầu mã mới.")

    expected_hash = _hash_otp(email=email, purpose=OtpPurpose.RESET_PASSWORD.value, otp=otp)
    if not hmac.compare_digest(expected_hash, code.code_hash):
        code.attempts = (code.attempts or 0) + 1
        return error_response("E1016", "OTP không đúng")

    user_res = await db.execute(select(User).where(User.email == email))
    user = user_res.scalar_one_or_none()
    if not user:
        code.consumed_at = now
        return error_response("E3004", "Không tìm thấy người dùng")

    # Consume OTP
    code.consumed_at = now

    user.hashed_password = get_password_hash(request.new_password)
    user.updated_at = datetime.utcnow()

    return success_response(data={"email": email}, message="Đổi mật khẩu thành công")


@router.post("/refresh", response_model=dict)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    """Refresh access token"""
    payload = decode_token(request.refresh_token)
    
    if not payload or payload.get("type") != "refresh":
        return error_response("E1002", "Refresh token không hợp lệ")
    
    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user or not user.is_active:
        return error_response("E1003", "Người dùng không tồn tại hoặc đã bị vô hiệu hóa")
    
    # Create new tokens
    access_token = create_access_token(data={"sub": user.id})
    new_refresh_token = create_refresh_token(data={"sub": user.id})
    
    return success_response(
        data={
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        },
        message="Token đã được làm mới"
    )


@router.post("/logout", response_model=dict)
async def logout(user_id: str = Depends(get_current_user_id)):
    """Logout user (invalidate token on client side)"""
    return success_response(
        data={"message": "Đăng xuất thành công"},
        message="Đăng xuất thành công"
    )


@router.get("/me", response_model=dict)
async def get_current_user(
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    """Get current user info"""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")
    
    return success_response(
        data=UserResponse.model_validate(user).model_dump(),
        message="Lấy thông tin thành công"
    )


@router.post("/bootstrap-admin", response_model=dict)
async def bootstrap_admin(
    email: str,
    bootstrap_key: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Promote a user to ADMIN using a server-side bootstrap key.

    To enable, set env var `BOOTSTRAP_ADMIN_KEY` on the backend service.
    """
    expected = os.environ.get("BOOTSTRAP_ADMIN_KEY")
    if not expected:
        return error_response("E1006", "Bootstrap is disabled")

    if not bootstrap_key or bootstrap_key != expected:
        return error_response("E1007", "Bootstrap key không hợp lệ")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        return error_response("E3004", "Không tìm thấy người dùng")

    user.role = UserRole.ADMIN
    user.is_verified = True
    await db.flush()
    await db.refresh(user)

    return success_response(data=UserResponse.model_validate(user).model_dump(), message="Đã cấp quyền Admin")
