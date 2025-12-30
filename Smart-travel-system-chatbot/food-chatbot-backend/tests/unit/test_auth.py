"""
Unit tests for authentication middleware.

Tests JWT token creation, verification, and user authentication flows.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch, AsyncMock
from fastapi import HTTPException
from jose import jwt


class TestJWTTokenCreation:
    """Tests for JWT token creation functions."""
    
    def test_create_access_token_basic(self):
        """Test creating a basic access token."""
        from middleware.auth import create_access_token
        
        token = create_access_token(data={"sub": "user-123"})
        
        assert token is not None
        assert isinstance(token, str)
        assert len(token) > 0
    
    def test_create_access_token_with_expiry(self):
        """Test access token has correct expiry."""
        from middleware.auth import create_access_token, SECRET_KEY, ALGORITHM
        
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=30)
        )
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert "exp" in payload
        assert "sub" in payload
        assert payload["sub"] == "user-123"
    
    def test_create_access_token_contains_user_data(self):
        """Test access token contains custom user data."""
        from middleware.auth import create_access_token, SECRET_KEY, ALGORITHM
        
        token = create_access_token(data={
            "sub": "user-123",
            "username": "testuser",
            "role": "admin"
        })
        
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload["sub"] == "user-123"
        assert payload["username"] == "testuser"
        assert payload["role"] == "admin"
    
    def test_create_refresh_token(self):
        """Test creating a refresh token."""
        from middleware.auth import create_refresh_token
        
        token = create_refresh_token(data={"sub": "user-123"})
        
        assert token is not None
        assert isinstance(token, str)
    
    def test_create_tokens_returns_both(self):
        """Test create_tokens returns both access and refresh tokens."""
        from middleware.auth import create_tokens, Token
        
        # create_tokens expects a dict with user_data
        tokens = create_tokens(user_data={
            "user_id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "is_guest": False
        })
        
        assert isinstance(tokens, Token)
        assert tokens.access_token is not None
        assert tokens.refresh_token is not None
        assert tokens.token_type == "bearer"


class TestJWTTokenVerification:
    """Tests for JWT token verification."""
    
    def test_verify_valid_token(self):
        """Test verifying a valid token."""
        from middleware.auth import create_access_token, verify_token
        
        token = create_access_token(data={"sub": "user-123"})
        token_data = verify_token(token)
        
        assert token_data is not None
        assert token_data.user_id == "user-123"
    
    def test_verify_expired_token(self):
        """Test that expired tokens return None."""
        from middleware.auth import create_access_token, verify_token
        
        # Create a token that's already expired
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(seconds=-10)  # Expired 10 seconds ago
        )
        
        # verify_token returns None for invalid/expired tokens
        result = verify_token(token)
        assert result is None
    
    def test_verify_invalid_token(self):
        """Test that invalid tokens return None."""
        from middleware.auth import verify_token
        
        # verify_token returns None for invalid tokens
        result = verify_token("invalid-token-string")
        assert result is None
    
    def test_verify_tampered_token(self):
        """Test that tampered tokens return None."""
        from middleware.auth import create_access_token, verify_token
        
        token = create_access_token(data={"sub": "user-123"})
        # Tamper with the token
        tampered_token = token[:-5] + "xxxxx"
        
        result = verify_token(tampered_token)
        assert result is None
    
    def test_verify_blacklisted_token(self):
        """Test that blacklisted tokens return None."""
        from middleware.auth import create_access_token, verify_token, add_to_blacklist, _token_blacklist
        
        token = create_access_token(data={"sub": "user-123"})
        
        # Blacklist the token
        add_to_blacklist(token)
        
        result = verify_token(token)
        assert result is None
        
        # Cleanup
        _token_blacklist.discard(token)


class TestUserModels:
    """Tests for user-related Pydantic models."""
    
    def test_user_model_creation(self):
        """Test creating a User model."""
        from middleware.auth import User
        
        user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.email == "test@example.com"
        assert user.is_active is True
    
    def test_user_model_defaults(self):
        """Test User model default values."""
        from middleware.auth import User
        
        # User requires username as it doesn't have a default
        user = User(user_id="user-123", username="testuser")
        
        assert user.user_id == "user-123"
        assert user.username == "testuser"
        assert user.email is None
        assert user.is_active is True
        assert user.is_guest is False
    
    def test_token_model_creation(self):
        """Test creating a Token model."""
        from middleware.auth import Token
        
        token = Token(
            access_token="abc123",
            refresh_token="def456",
            token_type="bearer"
        )
        
        assert token.access_token == "abc123"
        assert token.refresh_token == "def456"
        assert token.token_type == "bearer"


class TestPasswordHashing:
    """Tests for password hashing utilities."""
    
    def test_hash_password(self):
        """Test password hashing."""
        from middleware.auth import pwd_context
        
        password = "mysecretpassword"
        hashed = pwd_context.hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_verify_password_correct(self):
        """Test verifying correct password."""
        from middleware.auth import pwd_context
        
        password = "mysecretpassword"
        hashed = pwd_context.hash(password)
        
        assert pwd_context.verify(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        from middleware.auth import pwd_context
        
        password = "mysecretpassword"
        wrong_password = "wrongpassword"
        hashed = pwd_context.hash(password)
        
        assert pwd_context.verify(wrong_password, hashed) is False
    
    def test_hash_password_is_unique(self):
        """Test that same password produces different hashes."""
        from middleware.auth import pwd_context
        
        password = "mysecretpassword"
        hash1 = pwd_context.hash(password)
        hash2 = pwd_context.hash(password)
        
        # Bcrypt produces unique hashes with different salts
        assert hash1 != hash2


class TestGetCurrentUser:
    """Tests for get_current_user dependency."""
    
    @pytest.mark.asyncio
    async def test_get_current_user_valid_token(self):
        """Test getting current user with valid token."""
        from middleware.auth import create_access_token, get_current_user
        from fastapi.security import HTTPAuthorizationCredentials
        from unittest.mock import AsyncMock, patch
        
        token = create_access_token(data={
            "sub": "user-123",
            "email": "test@example.com",
            "username": "testuser"
        })
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        request = MagicMock()
        
        # Mock auth_service.get_user_info
        mock_user_info = {
            "user_id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "is_guest": False
        }
        
        with patch('middleware.auth.auth_service') as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user_info)
            
            # This would normally call the DB, but we're mocking it
            user = await get_current_user(request, credentials)
            
            assert user.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_get_current_user_missing_token(self):
        """Test that missing token raises 401."""
        from middleware.auth import get_current_user
        
        request = MagicMock()
        
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request, None)
        
        assert exc_info.value.status_code == 401
    
    @pytest.mark.asyncio
    async def test_get_current_active_user(self):
        """Test get_current_active_user with active user."""
        from middleware.auth import get_current_active_user, User
        
        active_user = User(
            user_id="user-123",
            username="testuser",
            email="test@example.com",
            is_active=True
        )
        
        result = await get_current_active_user(active_user)
        
        assert result.user_id == "user-123"
        assert result.is_active is True


class TestGetCurrentUserOptional:
    """Tests for get_current_user_optional dependency."""
    
    @pytest.mark.asyncio
    async def test_optional_auth_with_token(self):
        """Test optional auth with valid token."""
        from middleware.auth import create_access_token, get_current_user_optional
        from fastapi.security import HTTPAuthorizationCredentials
        
        token = create_access_token(data={
            "sub": "user-123",
            "email": "test@example.com",
            "username": "testuser"
        })
        
        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)
        
        # Mock auth_service.get_user_info
        mock_user_info = {
            "user_id": "user-123",
            "email": "test@example.com",
            "username": "testuser",
            "is_guest": False
        }
        
        with patch('middleware.auth.auth_service') as mock_service:
            mock_service.get_user_info = AsyncMock(return_value=mock_user_info)
            
            user = await get_current_user_optional(credentials)
            
            assert user is not None
            assert user.user_id == "user-123"
    
    @pytest.mark.asyncio
    async def test_optional_auth_without_token(self):
        """Test optional auth returns None without token."""
        from middleware.auth import get_current_user_optional
        
        user = await get_current_user_optional(None)
        
        assert user is None


class TestTokenBlacklist:
    """Tests for token blacklist functionality."""
    
    def test_add_to_blacklist(self):
        """Test adding token to blacklist."""
        from middleware.auth import add_to_blacklist, is_blacklisted, _token_blacklist
        
        test_token = "test-token-12345"
        
        add_to_blacklist(test_token)
        
        assert is_blacklisted(test_token) is True
        
        # Cleanup
        _token_blacklist.discard(test_token)
    
    def test_is_blacklisted_false(self):
        """Test token not in blacklist."""
        from middleware.auth import is_blacklisted
        
        assert is_blacklisted("non-existent-token") is False


class TestTokenTypes:
    """Tests for different token types."""
    
    def test_access_token_type(self):
        """Test access token has correct type."""
        from middleware.auth import create_access_token, SECRET_KEY, ALGORITHM
        
        token = create_access_token(data={"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload.get("type") == "access"
    
    def test_refresh_token_type(self):
        """Test refresh token has correct type."""
        from middleware.auth import create_refresh_token, SECRET_KEY, ALGORITHM
        
        token = create_refresh_token(data={"sub": "user-123"})
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        assert payload.get("type") == "refresh"
    
    def test_verify_wrong_token_type(self):
        """Test verifying token with wrong type returns None."""
        from middleware.auth import create_refresh_token, verify_token
        
        # Create a refresh token
        refresh_token = create_refresh_token(data={"sub": "user-123"})
        
        # Try to verify as access token (should fail)
        result = verify_token(refresh_token, token_type="access")
        assert result is None
        
        # Verify as refresh token (should succeed)
        result = verify_token(refresh_token, token_type="refresh")
        assert result is not None
        assert result.user_id == "user-123"
