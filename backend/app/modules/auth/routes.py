"""
Authentication API routes
"""
import os
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
from app.modules.auth.models import User, UserRole
from app.modules.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserResponse,
    RefreshTokenRequest,
    TokenResponse
)
from app.shared.schemas import success_response, error_response

router = APIRouter(prefix="/auth", tags=["Authentication"])


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
