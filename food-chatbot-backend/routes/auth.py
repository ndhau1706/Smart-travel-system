"""
Authentication routes for login, register, and user management.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from services.auth_service import auth_service

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


class UserResponse(BaseModel):
    """User response model."""
    user_id: str
    email: Optional[str] = None
    username: str
    is_guest: bool


@router.post("/register", response_model=UserResponse)
async def register(request: RegisterRequest):
    """
    Register a new user account.
    
    Args:
        request: Registration details
        
    Returns:
        User information
    """
    result = await auth_service.register_user(
        email=request.email,
        username=request.username,
        password=request.password
    )
    
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    
    return UserResponse(**result)


@router.post("/login", response_model=UserResponse)
async def login(request: LoginRequest):
    """
    Login with email and password.
    
    Args:
        request: Login credentials
        
    Returns:
        User information
    """
    result = await auth_service.login_user(
        email=request.email,
        password=request.password
    )
    
    if "error" in result:
        raise HTTPException(status_code=401, detail=result["error"])
    
    return UserResponse(**result)


@router.post("/guest", response_model=UserResponse)
async def create_guest():
    """
    Create a guest user with limited message quota.
    
    Returns:
        Guest user information
    """
    guest_id = await auth_service.create_guest_user()
    user_info = await auth_service.get_user_info(guest_id)
    
    if not user_info:
        raise HTTPException(status_code=500, detail="Failed to create guest user")
    
    return UserResponse(**user_info)


@router.get("/user/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    """
    Get user information by ID.
    
    Args:
        user_id: User ID
        
    Returns:
        User information
    """
    user_info = await auth_service.get_user_info(user_id)
    
    if not user_info:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(**user_info)
