"""
Authentication API routes
"""
import json
import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token,
    get_current_user_id
)
from app.core.config import settings
from app.modules.auth.models import EmailOtp, OtpPurpose, User, UserRole
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterStartRequest,
    RegisterVerifyRequest,
    RegisterResponse,
    UserResponse,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    RefreshTokenRequest,
    TokenResponse
)
from app.modules.auth.otp import generate_otp_code, hash_otp, send_otp_email, verify_otp
from app.shared.schemas import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _now_utc() -> datetime:
    # Use naive UTC datetimes for DB compatibility (existing columns are TIMESTAMP WITHOUT TIME ZONE).
    return datetime.utcnow()


def _as_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt
    # Normalize aware datetimes to naive UTC (fixes Postgres TIMESTAMPTZ vs naive comparisons).
    return dt.astimezone(timezone.utc).replace(tzinfo=None)


async def _get_otp(db: AsyncSession, email: str, purpose: OtpPurpose) -> EmailOtp | None:
    result = await db.execute(
        select(EmailOtp).where(EmailOtp.email == email.lower(), EmailOtp.purpose == purpose)
    )
    return result.scalar_one_or_none()


def _is_expired(otp: EmailOtp, now: datetime) -> bool:
    now_utc = _as_utc(now) or now
    expires_utc = _as_utc(otp.expires_at) if getattr(otp, "expires_at", None) else None
    return not expires_utc or expires_utc <= now_utc


def _check_resend_limit(otp: EmailOtp | None, now: datetime) -> str | None:
    limit = int(settings.OTP_RESEND_LIMIT_PER_HOUR or 0)
    if limit <= 0:
        return None

    if not otp or not otp.resend_window_started_at:
        return None

    now_utc = _as_utc(now) or now
    started_utc = _as_utc(otp.resend_window_started_at) or otp.resend_window_started_at
    if now_utc - started_utc >= timedelta(hours=1):
        return None

    if (otp.resend_count or 0) >= limit:
        return "Bạn đã yêu cầu OTP quá nhiều lần. Vui lòng thử lại sau."

    return None


def _reset_resend_window_if_needed(otp: EmailOtp, now: datetime) -> None:
    now_utc = _as_utc(now) or now
    started = otp.resend_window_started_at
    if not started:
        otp.resend_window_started_at = now
        otp.resend_count = 0
        return

    started_utc = _as_utc(started) or started
    if now_utc - started_utc >= timedelta(hours=1):
        otp.resend_window_started_at = now
        otp.resend_count = 0


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


@router.post("/register/start", response_model=dict)
async def register_start(request: RegisterStartRequest, db: AsyncSession = Depends(get_db)):
    """Start registration by sending OTP to email."""
    if request.password != request.confirm_password:
        return error_response("E1010", "Mật khẩu xác nhận không khớp")

    email = request.email.lower()

    # Check if email already exists
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        return error_response("E1005", "Email đã được sử dụng")

    now = _now_utc()
    existing = await _get_otp(db, email=email, purpose=OtpPurpose.REGISTER)
    limit_msg = _check_resend_limit(existing, now)
    if limit_msg:
        return error_response("E1012", limit_msg)

    otp_code = generate_otp_code()
    otp_hash = hash_otp(email=email, purpose=OtpPurpose.REGISTER, otp_code=otp_code)
    expires_at = now + timedelta(minutes=int(settings.OTP_TTL_MIN or 10))

    payload = {
        "name": request.name,
        "email": email,
        "password_hash": get_password_hash(request.password),
    }

    if existing:
        # Reset attempts on each resend and update payload.
        _reset_resend_window_if_needed(existing, now)

        existing.code_hash = otp_hash
        existing.payload_json = json.dumps(payload, ensure_ascii=False)
        existing.expires_at = expires_at
        existing.attempts = 0
        existing.resend_count = (existing.resend_count or 0) + 1
    else:
        db.add(
            EmailOtp(
                email=email,
                purpose=OtpPurpose.REGISTER,
                code_hash=otp_hash,
                payload_json=json.dumps(payload, ensure_ascii=False),
                expires_at=expires_at,
                attempts=0,
                resend_window_started_at=now,
                resend_count=1,
            )
        )

    await db.flush()

    try:
        send_otp_email(to_email=email, otp_code=otp_code, purpose=OtpPurpose.REGISTER)
    except Exception as exc:
        return error_response("E2001", "Không thể gửi OTP. Vui lòng thử lại sau.", {"error": str(exc)})

    return success_response(data={"email": email}, message="Đã gửi OTP")


@router.post("/register/verify", response_model=dict)
async def register_verify(request: RegisterVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and create user account."""
    email = request.email.lower()
    now = _now_utc()

    otp = await _get_otp(db, email=email, purpose=OtpPurpose.REGISTER)
    if not otp or _is_expired(otp, now):
        if otp:
            await db.delete(otp)
        return error_response("E1013", "OTP không tồn tại hoặc đã hết hạn")

    max_attempts = int(settings.OTP_MAX_ATTEMPTS or 0)
    if max_attempts > 0 and (otp.attempts or 0) >= max_attempts:
        await db.delete(otp)
        return error_response("E1014", "Bạn đã nhập sai OTP quá nhiều lần. Vui lòng yêu cầu mã mới.")

    if not verify_otp(email=email, purpose=OtpPurpose.REGISTER, otp_code=request.otp, expected_hash=otp.code_hash):
        otp.attempts = (otp.attempts or 0) + 1
        await db.flush()
        return error_response("E1011", "OTP không đúng")

    # Parse payload saved at /register/start
    try:
        payload = json.loads(otp.payload_json or "{}")
    except Exception:
        payload = {}

    name = (payload.get("name") or "").strip()
    password_hash = payload.get("password_hash")
    if not name or not password_hash:
        await db.delete(otp)
        return error_response("E1015", "Thông tin đăng ký không hợp lệ. Vui lòng đăng ký lại.")

    # Ensure email still not used
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        await db.delete(otp)
        return error_response("E1005", "Email đã được sử dụng")

    new_user = User(
        email=email,
        name=name,
        hashed_password=password_hash,
        is_verified=True,
    )
    db.add(new_user)
    await db.delete(otp)

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


@router.post("/forgot-password", response_model=dict)
async def forgot_password(request: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Send OTP to reset password (if email exists)."""
    email = request.email.lower()
    now = _now_utc()

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    # Always respond success to avoid user enumeration.
    if not user:
        return success_response(data={"email": email}, message="Nếu email tồn tại, OTP đã được gửi")

    existing = await _get_otp(db, email=email, purpose=OtpPurpose.RESET_PASSWORD)
    limit_msg = _check_resend_limit(existing, now)
    if limit_msg:
        return error_response("E1012", limit_msg)

    otp_code = generate_otp_code()
    otp_hash = hash_otp(email=email, purpose=OtpPurpose.RESET_PASSWORD, otp_code=otp_code)
    expires_at = now + timedelta(minutes=int(settings.OTP_TTL_MIN or 10))

    payload = {"user_id": user.id}

    if existing:
        _reset_resend_window_if_needed(existing, now)

        existing.code_hash = otp_hash
        existing.payload_json = json.dumps(payload, ensure_ascii=False)
        existing.expires_at = expires_at
        existing.attempts = 0
        existing.resend_count = (existing.resend_count or 0) + 1
    else:
        db.add(
            EmailOtp(
                email=email,
                purpose=OtpPurpose.RESET_PASSWORD,
                code_hash=otp_hash,
                payload_json=json.dumps(payload, ensure_ascii=False),
                expires_at=expires_at,
                attempts=0,
                resend_window_started_at=now,
                resend_count=1,
            )
        )

    await db.flush()

    try:
        send_otp_email(to_email=email, otp_code=otp_code, purpose=OtpPurpose.RESET_PASSWORD)
    except Exception as exc:
        return error_response("E2001", "Không thể gửi OTP. Vui lòng thử lại sau.", {"error": str(exc)})

    return success_response(data={"email": email}, message="Nếu email tồn tại, OTP đã được gửi")


@router.post("/reset-password", response_model=dict)
async def reset_password(request: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Verify OTP and reset password."""
    if request.new_password != request.confirm_password:
        return error_response("E1010", "Mật khẩu xác nhận không khớp")

    email = request.email.lower()
    now = _now_utc()

    otp = await _get_otp(db, email=email, purpose=OtpPurpose.RESET_PASSWORD)
    if not otp or _is_expired(otp, now):
        if otp:
            await db.delete(otp)
        return error_response("E1013", "OTP không tồn tại hoặc đã hết hạn")

    max_attempts = int(settings.OTP_MAX_ATTEMPTS or 0)
    if max_attempts > 0 and (otp.attempts or 0) >= max_attempts:
        await db.delete(otp)
        return error_response("E1014", "Bạn đã nhập sai OTP quá nhiều lần. Vui lòng yêu cầu mã mới.")

    if not verify_otp(email=email, purpose=OtpPurpose.RESET_PASSWORD, otp_code=request.otp, expected_hash=otp.code_hash):
        otp.attempts = (otp.attempts or 0) + 1
        await db.flush()
        return error_response("E1011", "OTP không đúng")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        await db.delete(otp)
        return error_response("E3004", "Không tìm thấy người dùng")

    user.hashed_password = get_password_hash(request.new_password)
    user.is_verified = True
    await db.delete(otp)
    await db.flush()

    return success_response(data={"email": email}, message="Đã cập nhật mật khẩu")


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
