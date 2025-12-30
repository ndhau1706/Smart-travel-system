"""
Pytest configuration and shared fixtures for the Food Chatbot Backend tests.

This file is automatically loaded by pytest and provides:
- Shared test fixtures (test client, database, mocks)
- Test configuration
- Common utilities for testing

Usage:
    pytest                          # Run all tests
    pytest tests/unit/              # Run unit tests only
    pytest tests/integration/       # Run integration tests only
    pytest -v                       # Verbose output
    pytest --cov=.                  # With coverage report
    pytest -k "test_auth"           # Run tests matching pattern
"""
import pytest
import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch
from typing import AsyncGenerator, Generator

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


# =============================================================================
# Event Loop Configuration
# =============================================================================
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# =============================================================================
# Environment Setup
# =============================================================================
@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Set up test environment variables before any tests run."""
    os.environ["DEBUG"] = "false"
    os.environ["DATABASE_PATH"] = ":memory:"  # Use in-memory SQLite for tests
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-for-testing-only"
    os.environ["GROQ_API_KEYS"] = "test_key_1,test_key_2"
    yield
    # Cleanup if needed


# =============================================================================
# Application Fixtures
# =============================================================================
@pytest.fixture
def app():
    """Create a test FastAPI application instance."""
    # Import after environment is set up
    from main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app) -> Generator:
    """Create a synchronous test client for the FastAPI app."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
async def async_client(app) -> AsyncGenerator:
    """Create an asynchronous test client for the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# =============================================================================
# Database Fixtures
# =============================================================================
@pytest.fixture
async def test_db():
    """Create a test database with fresh tables."""
    from database import db_manager
    
    # Initialize fresh database
    await db_manager.init_db()
    
    yield db_manager
    
    # Cleanup - tables will be dropped when in-memory db is closed


@pytest.fixture
def mock_db_manager():
    """Create a mocked database manager."""
    mock = MagicMock()
    mock.get_connection = MagicMock(return_value=AsyncMock())
    mock.init_db = AsyncMock()
    mock.clear_expired_cache = AsyncMock()
    return mock


# =============================================================================
# Authentication Fixtures
# =============================================================================
@pytest.fixture
def test_user():
    """Create a test user data."""
    return {
        "user_id": "test-user-123",
        "username": "testuser",
        "email": "test@example.com",
        "is_active": True
    }


@pytest.fixture
def test_user_token(test_user):
    """Create a valid JWT token for the test user."""
    from middleware.auth import create_access_token
    return create_access_token(data={"sub": test_user["user_id"]})


@pytest.fixture
def auth_headers(test_user_token):
    """Create authorization headers with Bearer token."""
    return {"Authorization": f"Bearer {test_user_token}"}


@pytest.fixture
def mock_current_user(test_user):
    """Create a mock User object for dependency injection."""
    from middleware.auth import User
    return User(
        user_id=test_user["user_id"],
        username=test_user["username"],
        email=test_user["email"],
        is_active=test_user["is_active"]
    )


# =============================================================================
# Service Mocks
# =============================================================================
@pytest.fixture
def mock_groq_service():
    """Create a mocked Groq LLM service."""
    mock = MagicMock()
    mock.generate = AsyncMock(return_value={
        "response": "Test AI response",
        "model_used": "llama-3.3-70b-versatile",
        "tokens_used": 100
    })
    mock.get_health_stats = MagicMock(return_value={
        "primary_model": "llama-3.3-70b-versatile",
        "fallback_model": "llama-3.1-8b-instant",
        "key_stats": {"key_1": {"is_blocked": False}}
    })
    return mock


@pytest.fixture
def mock_vector_store():
    """Create a mocked vector store for FAISS search."""
    mock = MagicMock()
    mock.search = MagicMock(return_value=[
        {"id": 1, "name": "Test Restaurant 1", "score": 0.95},
        {"id": 2, "name": "Test Restaurant 2", "score": 0.87}
    ])
    mock.index = MagicMock()  # Simulate loaded index
    return mock


@pytest.fixture
def mock_bm25_search():
    """Create a mocked BM25 search service."""
    mock = MagicMock()
    mock.search = MagicMock(return_value=[
        {"id": 1, "name": "Test Restaurant 1", "score": 12.5},
        {"id": 3, "name": "Test Restaurant 3", "score": 8.3}
    ])
    mock.bm25 = MagicMock()  # Simulate loaded index
    return mock


@pytest.fixture
def mock_session_manager():
    """Create a mocked session manager."""
    mock = MagicMock()
    mock.create_session = AsyncMock(return_value="test-session-id-123")
    mock.get_session = AsyncMock(return_value={
        "session_id": "test-session-id-123",
        "user_id": "test-user-123",
        "created_at": "2024-01-01T00:00:00Z"
    })
    mock.get_sessions = AsyncMock(return_value=[
        {"session_id": "session-1", "user_id": "test-user-123"},
        {"session_id": "session-2", "user_id": "test-user-123"}
    ])
    mock.get_messages = AsyncMock(return_value=[])
    mock.add_message = AsyncMock()
    return mock


# =============================================================================
# Sample Data Fixtures
# =============================================================================
@pytest.fixture
def sample_restaurant():
    """Create sample restaurant data for testing."""
    return {
        "id": 1,
        "name": "Phở Hà Nội",
        "address": "123 Nguyễn Huệ, Quận 1, TP.HCM",
        "cuisine_type": "Việt Nam",
        "rating": 4.5,
        "rating_count": 1250,
        "price_range": "$$",
        "latitude": 10.7731,
        "longitude": 106.7030,
        "opening_hours": "6:00 - 22:00"
    }


@pytest.fixture
def sample_restaurants(sample_restaurant):
    """Create a list of sample restaurants for testing."""
    return [
        sample_restaurant,
        {
            "id": 2,
            "name": "Sushi Tokyo",
            "address": "456 Lê Lợi, Quận 1, TP.HCM",
            "cuisine_type": "Nhật Bản",
            "rating": 4.7,
            "rating_count": 890,
            "price_range": "$$$",
            "latitude": 10.7755,
            "longitude": 106.7020
        },
        {
            "id": 3,
            "name": "Pizza Italia",
            "address": "789 Đồng Khởi, Quận 1, TP.HCM",
            "cuisine_type": "Ý",
            "rating": 4.2,
            "rating_count": 650,
            "price_range": "$$",
            "latitude": 10.7780,
            "longitude": 106.7010
        }
    ]


@pytest.fixture
def sample_chat_request():
    """Create a sample chat request for testing."""
    return {
        "message": "Tìm quán phở ngon ở Quận 1",
        "session_id": "test-session-123",
        "language": "vi"
    }


@pytest.fixture
def sample_feedback_request():
    """Create a sample feedback request for testing."""
    return {
        "session_id": "test-session-123",
        "feedback_type": "rating",
        "rating": 5,
        "comment": "Great recommendations!",
        "restaurant_id": 1
    }


# =============================================================================
# HTTP Request Fixtures
# =============================================================================
@pytest.fixture
def csrf_token():
    """Create a mock CSRF token for testing protected endpoints."""
    return "test-csrf-token-12345"


@pytest.fixture
def csrf_headers(csrf_token):
    """Create headers with CSRF token."""
    return {
        "X-CSRF-Token": csrf_token,
        "Cookie": f"csrf_token={csrf_token}"
    }


@pytest.fixture
def full_auth_headers(auth_headers, csrf_headers):
    """Create headers with both auth and CSRF tokens."""
    return {**auth_headers, **csrf_headers}


# =============================================================================
# Utility Functions
# =============================================================================
def create_test_session(user_id: str = "test-user-123") -> dict:
    """Helper function to create a test session dictionary."""
    import secrets
    from datetime import datetime
    
    return {
        "session_id": secrets.token_urlsafe(32),
        "user_id": user_id,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "message_count": 0
    }


def create_test_message(role: str = "user", content: str = "Test message") -> dict:
    """Helper function to create a test message dictionary."""
    import secrets
    from datetime import datetime
    
    return {
        "message_id": secrets.token_urlsafe(16),
        "role": role,
        "content": content,
        "created_at": datetime.utcnow().isoformat()
    }


# =============================================================================
# Pytest Configuration Hooks
# =============================================================================
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "slow: mark test as slow (may be skipped)")
    config.addinivalue_line("markers", "auth: mark test as authentication related")


def pytest_collection_modifyitems(config, items):
    """Modify collected test items based on markers."""
    # Add skip markers for slow tests if --fast is passed
    if config.getoption("--fast", default=False):
        skip_slow = pytest.mark.skip(reason="Skipping slow tests with --fast")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--fast",
        action="store_true",
        default=False,
        help="Skip slow tests"
    )
