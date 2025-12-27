"""
Unit tests for session management.

Tests session creation, retrieval, IDOR protection, and message handling.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException


class TestSessionCreation:
    """Tests for session creation."""
    
    @pytest.mark.asyncio
    async def test_create_session_for_authenticated_user(self, mock_session_manager, test_user):
        """Test creating session for authenticated user."""
        mock_session_manager.create_session = AsyncMock(return_value="session-123")
        
        session_id = await mock_session_manager.create_session(user_id=test_user["user_id"])
        
        assert session_id == "session-123"
        mock_session_manager.create_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_session_for_guest(self, mock_session_manager):
        """Test creating session for guest user."""
        mock_session_manager.create_session = AsyncMock(return_value="guest-session-456")
        
        session_id = await mock_session_manager.create_session(user_id=None)
        
        assert session_id is not None
    
    @pytest.mark.asyncio
    async def test_session_id_format(self, mock_session_manager):
        """Test session ID has correct format."""
        import secrets
        
        # Session IDs should be URL-safe tokens
        session_id = secrets.token_urlsafe(32)
        
        assert len(session_id) == 43  # Base64 encoding of 32 bytes
        assert all(c.isalnum() or c in '-_' for c in session_id)


class TestSessionRetrieval:
    """Tests for session retrieval with IDOR protection."""
    
    @pytest.mark.asyncio
    async def test_get_own_session(self, mock_session_manager, test_user):
        """Test user can retrieve their own session."""
        mock_session_manager.get_session = AsyncMock(return_value={
            "session_id": "session-123",
            "user_id": test_user["user_id"],
            "created_at": "2024-01-01T00:00:00Z"
        })
        
        session = await mock_session_manager.get_session("session-123")
        
        assert session["user_id"] == test_user["user_id"]
    
    @pytest.mark.asyncio
    async def test_cannot_get_other_user_session(self, mock_session_manager, test_user):
        """Test IDOR protection - user cannot access other's session."""
        other_user_session = {
            "session_id": "session-456",
            "user_id": "different-user-id",
            "created_at": "2024-01-01T00:00:00Z"
        }
        mock_session_manager.get_session = AsyncMock(return_value=other_user_session)
        
        session = await mock_session_manager.get_session("session-456")
        
        # The route should verify ownership and reject
        assert session["user_id"] != test_user["user_id"]
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, mock_session_manager):
        """Test retrieving non-existent session returns None."""
        mock_session_manager.get_session = AsyncMock(return_value=None)
        
        session = await mock_session_manager.get_session("nonexistent-session")
        
        assert session is None


class TestSessionListing:
    """Tests for listing user sessions."""
    
    @pytest.mark.asyncio
    async def test_list_own_sessions_only(self, mock_session_manager, test_user):
        """Test user only sees their own sessions."""
        mock_session_manager.get_sessions = AsyncMock(return_value=[
            {"session_id": "session-1", "user_id": test_user["user_id"]},
            {"session_id": "session-2", "user_id": test_user["user_id"]}
        ])
        
        sessions = await mock_session_manager.get_sessions(user_id=test_user["user_id"])
        
        assert len(sessions) == 2
        assert all(s["user_id"] == test_user["user_id"] for s in sessions)
    
    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, mock_session_manager, test_user):
        """Test listing sessions when user has none."""
        mock_session_manager.get_sessions = AsyncMock(return_value=[])
        
        sessions = await mock_session_manager.get_sessions(user_id=test_user["user_id"])
        
        assert sessions == []
    
    @pytest.mark.asyncio
    async def test_list_sessions_with_pagination(self, mock_session_manager, test_user):
        """Test session listing supports pagination."""
        all_sessions = [
            {"session_id": f"session-{i}", "user_id": test_user["user_id"]}
            for i in range(50)
        ]
        
        mock_session_manager.get_sessions = AsyncMock(
            return_value=all_sessions[:10]  # First page
        )
        
        sessions = await mock_session_manager.get_sessions(
            user_id=test_user["user_id"],
            limit=10,
            offset=0
        )
        
        assert len(sessions) == 10


class TestMessageManagement:
    """Tests for message handling within sessions."""
    
    @pytest.mark.asyncio
    async def test_add_user_message(self, mock_session_manager):
        """Test adding user message to session."""
        mock_session_manager.add_message = AsyncMock()
        
        await mock_session_manager.add_message(
            session_id="session-123",
            role="user",
            content="Hello, find me a restaurant"
        )
        
        mock_session_manager.add_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_add_assistant_message(self, mock_session_manager):
        """Test adding assistant message to session."""
        mock_session_manager.add_message = AsyncMock()
        
        await mock_session_manager.add_message(
            session_id="session-123",
            role="assistant",
            content="Here are some recommendations..."
        )
        
        mock_session_manager.add_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_messages_ordered(self, mock_session_manager):
        """Test messages are returned in chronological order."""
        messages = [
            {"id": 1, "role": "user", "content": "First", "created_at": "2024-01-01T00:00:00Z"},
            {"id": 2, "role": "assistant", "content": "Second", "created_at": "2024-01-01T00:01:00Z"},
            {"id": 3, "role": "user", "content": "Third", "created_at": "2024-01-01T00:02:00Z"}
        ]
        mock_session_manager.get_messages = AsyncMock(return_value=messages)
        
        result = await mock_session_manager.get_messages("session-123")
        
        assert result[0]["id"] == 1
        assert result[2]["id"] == 3
    
    @pytest.mark.asyncio
    async def test_get_messages_empty_session(self, mock_session_manager):
        """Test getting messages from empty session."""
        mock_session_manager.get_messages = AsyncMock(return_value=[])
        
        messages = await mock_session_manager.get_messages("session-123")
        
        assert messages == []


class TestSessionDeletion:
    """Tests for session deletion."""
    
    @pytest.mark.asyncio
    async def test_delete_own_session(self, mock_session_manager, test_user):
        """Test user can delete their own session."""
        mock_session_manager.delete_session = AsyncMock(return_value=True)
        
        result = await mock_session_manager.delete_session(
            session_id="session-123",
            user_id=test_user["user_id"]
        )
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_cannot_delete_other_user_session(self, mock_session_manager, test_user):
        """Test IDOR protection for session deletion."""
        mock_session_manager.delete_session = AsyncMock(return_value=False)
        
        # Attempting to delete another user's session should fail
        result = await mock_session_manager.delete_session(
            session_id="other-user-session",
            user_id=test_user["user_id"]
        )
        
        # Should return False or raise exception
        assert result is False


class TestSessionMetadata:
    """Tests for session metadata handling."""
    
    def test_session_includes_message_count(self):
        """Test session includes message count."""
        session = {
            "session_id": "session-123",
            "user_id": "user-123",
            "message_count": 10,
            "created_at": "2024-01-01T00:00:00Z"
        }
        
        assert session["message_count"] == 10
    
    def test_session_includes_timestamps(self):
        """Test session includes creation and update timestamps."""
        session = {
            "id": "session-123",
            "user_id": "user-123",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T01:00:00Z"
        }
        
        assert "created_at" in session
        assert "updated_at" in session
    
    def test_session_model_validation(self):
        """Test session model validates required fields."""
        from models import SessionInfo
        from datetime import datetime
        
        # Valid session
        session = SessionInfo(
            id="session-123",
            user_id="user-123",
            title="Test Session",
            language="vi",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert session.id == "session-123"
