"""
JWT Authentication Middleware for Food Chatbot Backend.

Implements:
- JWT access token (15 min) + refresh token (7 days)
- get_current_user dependency for FastAPI
- get_current_active_user with role checking
- Token blacklist for logout
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ============== Configuration ==============
# Load from environment with secure defaults
SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("SECRET_KEY", "your-super-secret-key-change-in-production"))
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


# ============== Token Models ==============
class Token(BaseModel):
    """Token response model."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = ACCESS_TOKEN_EXPIRE_MINUTES * 60


class TokenData(BaseModel):
    """Token payload data."""
    user_id: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    is_guest: bool = False
    token_type: str = "access"  # "access" or "refresh"


class User(BaseModel):
    """User model for authentication."""
    user_id: str
    email: Optional[str] = None
    username: str
    is_guest: bool = False
    is_active: bool = True
    

# ============== Token Blacklist ==============
# In-memory blacklist for revoked tokens (should use Redis in production)
_token_blacklist: set = set()


def add_to_blacklist(token: str) -> None:
    """Add a token to the blacklist (for logout)."""
    _token_blacklist.add(token)
    logger.info(f"Token added to blacklist")


def is_blacklisted(token: str) -> bool:
    """Check if a token is blacklisted."""
    return token in _token_blacklist


def clear_expired_from_blacklist() -> None:
    """Clear expired tokens from blacklist (call periodically)."""
    # In production, use Redis with TTL instead
    pass


# ============== Token Functions ==============
def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data (user_id, email, etc.)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT refresh token.
    
    Args:
        data: Payload data (user_id only recommended)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_tokens(user_data: Dict[str, Any]) -> Token:
    """
    Create both access and refresh tokens for a user.
    
    Args:
        user_data: Dict with user_id, email, username, is_guest
        
    Returns:
        Token object with access_token and refresh_token
    """
    access_token = create_access_token({
        "sub": user_data["user_id"],
        "email": user_data.get("email"),
        "username": user_data.get("username"),
        "is_guest": user_data.get("is_guest", False)
    })
    
    refresh_token = create_refresh_token({
        "sub": user_data["user_id"]
    })
    
    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        TokenData if valid, None otherwise
    """
    try:
        # Check blacklist
        if is_blacklisted(token):
            logger.warning("Attempted to use blacklisted token")
            return None
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Verify token type
        if payload.get("type") != token_type:
            logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
            return None
        
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return TokenData(
            user_id=user_id,
            email=payload.get("email"),
            username=payload.get("username"),
            is_guest=payload.get("is_guest", False),
            token_type=token_type
        )
        
    except JWTError as e:
        logger.warning(f"JWT verification failed: {e}")
        return None


# ============== FastAPI Dependencies ==============
async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    This is the main dependency for protected routes.
    
    Usage:
        @router.get("/protected")
        async def protected_route(current_user: User = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    
    Args:
        request: FastAPI request object
        credentials: HTTP Bearer credentials
        
    Returns:
        User object
        
    Raises:
        HTTPException 401: If not authenticated or token invalid
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Check for Bearer token
    if credentials is None:
        logger.warning("No credentials provided")
        raise credentials_exception
    
    token = credentials.credentials
    
    # Verify token
    token_data = verify_token(token, token_type="access")
    if token_data is None:
        raise credentials_exception
    
    # Get user from database
    from services.auth_service import auth_service
    user_info = await auth_service.get_user_info(token_data.user_id)
    
    if user_info is None:
        raise credentials_exception
    
    return User(
        user_id=user_info["user_id"],
        email=user_info.get("email"),
        username=user_info.get("username", "Unknown"),
        is_guest=user_info.get("is_guest", False),
        is_active=True
    )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    This dependency extends get_current_user with additional checks.
    
    Args:
        current_user: User from get_current_user
        
    Returns:
        Active User object
        
    Raises:
        HTTPException 403: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[User]:
    """
    Get the current user if authenticated, otherwise return None.
    
    Useful for endpoints that work both with and without authentication.
    
    Args:
        credentials: HTTP Bearer credentials (optional)
        
    Returns:
        User object or None
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    token_data = verify_token(token, token_type="access")
    
    if token_data is None:
        return None
    
    from services.auth_service import auth_service
    user_info = await auth_service.get_user_info(token_data.user_id)
    
    if user_info is None:
        return None
    
    return User(
        user_id=user_info["user_id"],
        email=user_info.get("email"),
        username=user_info.get("username", "Unknown"),
        is_guest=user_info.get("is_guest", False),
        is_active=True
    )


async def require_non_guest(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Require a non-guest (registered) user.
    
    Args:
        current_user: User from get_current_user
        
    Returns:
        Non-guest User object
        
    Raises:
        HTTPException 403: If user is a guest
    """
    if current_user.is_guest:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires a registered account"
        )
    return current_user


# ============== Password Utilities ==============
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)
