"""
Authentication routes for login, register, and user management.

Implements:
- POST /auth/register - Register new user with JWT tokens
- POST /auth/login - Login and get JWT tokens
- POST /auth/refresh - Refresh access token
- POST /auth/logout - Logout and invalidate tokens
- POST /auth/guest - Create guest user
- GET /auth/me - Get current user info
"""
import logging
from fastapi import APIRouter, HTTPException, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.auth_service import auth_service
from middleware.auth import (
    create_tokens,
    verify_token,
    add_to_blacklist,
    get_current_user,
    get_current_user_optional,
    User,
    Token,
    security
)

logger = logging.getLogger("chatbot.auth")

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """Register request model."""
    email: EmailStr
    username: str
    password: str


class LoginRequest(BaseModel):
    """Login request model."""
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str


class TokenResponse(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserResponse"


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    email: Optional[str] = None
    username: str
    is_guest: bool


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, response: Response):
    """
    Register a new user account.
    
    Args:
        request: Registration details (email, username, password)
        
    Returns:
        JWT tokens and user information
    """
    logger.info(f"Registration attempt for email: {request.email}")
    
    result = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password
    )
    
    if "error" in result:
        logger.warning(f"Registration failed: {result['error']}")
        raise HTTPException(status_code=400, detail=result["error"])
    
    # Create JWT tokens
    tokens = create_tokens(result)
    
    logger.info(f"User registered successfully: {result['user_id']}")
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse(**result)
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, response: Response):
    """
    Login with email and password.
    
    Args:
        request: Login credentials (email, password)
        
    Returns:
        JWT tokens and user information
    """
    logger.info(f"Login attempt for email: {request.email}")
    
    result = await auth_service.login_user(
        email=request.email,
        password=request.password
    )
    
    if "error" in result:
        logger.warning(f"Login failed for {request.email}: {result['error']}")
        raise HTTPException(status_code=401, detail=result["error"])
    
    # Create JWT tokens
    tokens = create_tokens(result)
    
    logger.info(f"User logged in successfully: {result['user_id']}")
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse(**result)
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshRequest):
    """
    Refresh access token using refresh token.
    
    Args:
        request: Refresh token
        
    Returns:
        New JWT tokens
    """
    # Verify refresh token
    token_data = verify_token(request.refresh_token, token_type="refresh")
    
    if token_data is None:
        logger.warning("Invalid refresh token attempt")
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    # Get user info
    user_info = await auth_service.get_user_info(token_data.user_id)
    
    if not user_info:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Create new tokens
    tokens = create_tokens(user_info)
    
    # Blacklist old refresh token
    add_to_blacklist(request.refresh_token)
    
    logger.info(f"Token refreshed for user: {token_data.user_id}")
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse(**user_info)
    )


@router.post("/logout")
async def logout(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    Logout and invalidate the current token.
    
    Returns:
        Success message
    """
    if credentials:
        add_to_blacklist(credentials.credentials)
        logger.info("User logged out, token blacklisted")
    
    return {"message": "Logged out successfully"}


@router.post("/guest", response_model=TokenResponse)
async def create_guest():
    """
    Create a guest user with limited message quota.
    
    Returns:
        JWT tokens and guest user information
    """
    guest_id = await auth_service.create_guest_user()
    user_info = await auth_service.get_user_info(guest_id)
    
    if not user_info:
        raise HTTPException(status_code=500, detail="Failed to create guest user")
    
    # Create JWT tokens for guest
    tokens = create_tokens(user_info)
    
    logger.info(f"Guest user created: {guest_id}")
    
    return TokenResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=UserResponse(**user_info)
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information.
    
    Requires: Bearer token in Authorization header
    
    Returns:
        Current user information
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        is_guest=current_user.is_guest
    )


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get user information by ID.
    
    Requires: Bearer token in Authorization header
    Only allows users to get their own info (or admin)
    
    Args:
        user_id: User ID
        
    Returns:
        User information
    """
    # Users can only view their own profile
    if current_user.user_id != user_id:
        raise HTTPException(
            status_code=403,
            detail="You can only view your own profile"
        )
    
    user_info = await auth_service.get_user_info(user_id)
    
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user_info)
