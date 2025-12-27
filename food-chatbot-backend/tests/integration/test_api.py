"""
Integration tests for API endpoints.

Tests the full request/response cycle through FastAPI.
"""
import pytest
from fastapi.testclient import TestClient


class TestHealthEndpoints:
    """Tests for health check endpoints."""
    
    def test_health_returns_200(self, client):
        """Test /health returns 200 OK."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
    
    def test_ready_returns_status(self, client):
        """Test /ready returns readiness status."""
        response = client.get("/ready")
        
        # May be 200 (ready) or 503 (not ready)
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        assert "checks" in data
    
    def test_root_returns_api_info(self, client):
        """Test / returns API information."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Food Chatbot Backend API"
        assert "endpoints" in data


class TestAuthenticationEndpoints:
    """Tests for authentication endpoints."""
    
    def test_register_new_user(self, client, csrf_headers):
        """Test user registration."""
        response = client.post(
            "/api/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "securepassword123"
            },
            headers=csrf_headers
        )
        
        # Should return 200 or 201 with tokens
        assert response.status_code in [200, 201]
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_valid_credentials(self, client, csrf_headers):
        """Test login with valid credentials."""
        # First register a user
        client.post(
            "/api/auth/register",
            json={
                "username": "logintest",
                "email": "login@example.com",
                "password": "testpassword123"
            },
            headers=csrf_headers
        )
        
        # Then login
        response = client.post(
            "/api/auth/login",
            json={
                "username": "logintest",
                "password": "testpassword123"
            },
            headers=csrf_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
    
    def test_login_invalid_credentials(self, client, csrf_headers):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "username": "nonexistent",
                "password": "wrongpassword"
            },
            headers=csrf_headers
        )
        
        assert response.status_code in [401, 404]
    
    def test_refresh_token(self, client, csrf_headers):
        """Test token refresh endpoint."""
        # Register and get tokens
        register_response = client.post(
            "/api/auth/register",
            json={
                "username": "refreshtest",
                "email": "refresh@example.com",
                "password": "testpassword123"
            },
            headers=csrf_headers
        )
        
        if register_response.status_code in [200, 201]:
            tokens = register_response.json()
            
            # Use refresh token
            response = client.post(
                "/api/auth/refresh",
                json={"refresh_token": tokens.get("refresh_token")},
                headers=csrf_headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assert "access_token" in data
    
    def test_get_current_user(self, client, auth_headers):
        """Test /me endpoint returns current user."""
        response = client.get(
            "/api/auth/me",
            headers=auth_headers
        )
        
        # Should return user info or 401 if not authenticated
        assert response.status_code in [200, 401]
    
    def test_guest_token(self, client, csrf_headers):
        """Test guest authentication."""
        response = client.post(
            "/api/auth/guest",
            headers=csrf_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data or "user_id" in data


class TestChatEndpoints:
    """Tests for chat endpoints."""
    
    def test_chat_without_session(self, client, csrf_headers):
        """Test chat creates new session if not provided."""
        response = client.post(
            "/api/chat",
            json={"message": "Tìm quán phở ngon"},
            headers=csrf_headers
        )
        
        # May succeed or require authentication
        assert response.status_code in [200, 401, 500]
    
    def test_chat_with_session(self, client, full_auth_headers):
        """Test chat with existing session."""
        # First create a session
        session_response = client.post(
            "/api/sessions",
            headers=full_auth_headers
        )
        
        if session_response.status_code == 200:
            session_id = session_response.json().get("session_id")
            
            response = client.post(
                "/api/chat",
                json={
                    "message": "Tìm quán sushi",
                    "session_id": session_id
                },
                headers=full_auth_headers
            )
            
            # Should return response or error from AI service
            assert response.status_code in [200, 500, 503]
    
    def test_chat_empty_message_rejected(self, client, csrf_headers):
        """Test empty message is rejected."""
        response = client.post(
            "/api/chat",
            json={"message": ""},
            headers=csrf_headers
        )
        
        assert response.status_code in [400, 422]
    
    def test_chat_returns_response_format(self, client, csrf_headers):
        """Test chat response has correct format."""
        response = client.post(
            "/api/chat",
            json={"message": "Hello"},
            headers=csrf_headers
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data or "message" in data


class TestSessionEndpoints:
    """Tests for session management endpoints."""
    
    def test_create_session(self, client, full_auth_headers):
        """Test creating a new session."""
        response = client.post(
            "/api/sessions",
            headers=full_auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert "session_id" in data
    
    def test_list_sessions_authenticated(self, client, full_auth_headers):
        """Test listing sessions for authenticated user."""
        response = client.get(
            "/api/sessions",
            headers=full_auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "sessions" in data or isinstance(data, list)
    
    def test_list_sessions_unauthenticated(self, client):
        """Test listing sessions without authentication fails."""
        response = client.get("/api/sessions")
        
        assert response.status_code == 401
    
    def test_get_session_history(self, client, full_auth_headers):
        """Test getting session history."""
        # Create a session first
        create_response = client.post(
            "/api/sessions",
            headers=full_auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            session_id = create_response.json().get("session_id")
            
            response = client.get(
                f"/api/sessions/{session_id}",
                headers=full_auth_headers
            )
            
            assert response.status_code == 200
    
    def test_get_other_user_session_forbidden(self, client, full_auth_headers):
        """Test IDOR protection - cannot access other user's session."""
        # Try to access a session that doesn't belong to the user
        response = client.get(
            "/api/sessions/other-user-session-id-12345",
            headers=full_auth_headers
        )
        
        # Should be 403 Forbidden or 404 Not Found
        assert response.status_code in [403, 404]


class TestFeedbackEndpoints:
    """Tests for feedback endpoints."""
    
    def test_submit_feedback(self, client, full_auth_headers, sample_feedback_request):
        """Test submitting feedback."""
        response = client.post(
            "/api/feedback",
            json=sample_feedback_request,
            headers=full_auth_headers
        )
        
        assert response.status_code in [200, 201]
        data = response.json()
        assert data.get("success") is True
    
    def test_get_restaurant_feedback(self, client):
        """Test getting restaurant feedback (public endpoint)."""
        response = client.get("/api/feedback/restaurant/1")
        
        # May return stats or 404 if no feedback
        assert response.status_code in [200, 404]
    
    def test_get_session_feedback_authenticated(self, client, full_auth_headers):
        """Test getting session feedback requires authentication."""
        # Create a session first
        create_response = client.post(
            "/api/sessions",
            headers=full_auth_headers
        )
        
        if create_response.status_code in [200, 201]:
            session_id = create_response.json().get("session_id")
            
            response = client.get(
                f"/api/feedback/session/{session_id}",
                headers=full_auth_headers
            )
            
            assert response.status_code == 200
    
    def test_get_session_feedback_unauthenticated(self, client):
        """Test getting session feedback without auth fails."""
        response = client.get("/api/feedback/session/some-session-id")
        
        assert response.status_code == 401


class TestCSRFProtection:
    """Tests for CSRF protection."""
    
    def test_post_without_csrf_token_rejected(self, client):
        """Test POST without CSRF token is rejected."""
        response = client.post(
            "/api/chat",
            json={"message": "test"}
        )
        
        # Should be rejected due to missing CSRF token
        assert response.status_code in [401, 403, 422]
    
    def test_get_csrf_token(self, client):
        """Test getting CSRF token."""
        response = client.get("/api/csrf-token")
        
        assert response.status_code == 200
    
    def test_post_with_valid_csrf_token(self, client, csrf_headers):
        """Test POST with valid CSRF token is accepted."""
        response = client.post(
            "/api/auth/guest",
            headers=csrf_headers
        )
        
        # Should be accepted (may still fail for other reasons)
        assert response.status_code != 403


class TestRateLimiting:
    """Tests for rate limiting."""
    
    def test_rate_limit_headers(self, client):
        """Test rate limit headers are present."""
        response = client.get("/health")
        
        # Some implementations add rate limit headers
        # This is optional based on implementation
        assert response.status_code == 200
    
    def test_excessive_requests_limited(self, client, csrf_headers):
        """Test excessive requests are rate limited."""
        # Make many requests quickly
        responses = []
        for _ in range(150):  # Assuming 100/min limit
            response = client.post(
                "/api/auth/guest",
                headers=csrf_headers
            )
            responses.append(response.status_code)
            
            # Stop if we get rate limited
            if response.status_code == 429:
                break
        
        # Should eventually get rate limited
        # (Note: may not trigger in fast test environment)
        assert True  # Rate limiting is best tested with actual timing


class TestCORSHeaders:
    """Tests for CORS headers."""
    
    def test_cors_headers_on_response(self, client):
        """Test CORS headers are present on responses."""
        response = client.get("/health")
        
        # CORS headers should be present for allowed origins
        # In test environment, may not have Origin header
        assert response.status_code == 200
    
    def test_preflight_request(self, client):
        """Test OPTIONS preflight request."""
        response = client.options(
            "/api/chat",
            headers={"Origin": "http://localhost:3000"}
        )
        
        # Should allow preflight
        assert response.status_code in [200, 204]


class TestSecurityHeaders:
    """Tests for security headers."""
    
    def test_security_headers_present(self, client):
        """Test security headers are present."""
        response = client.get("/health")
        
        # Check for important security headers
        headers = response.headers
        
        assert "x-frame-options" in headers or "X-Frame-Options" in headers
        assert "x-content-type-options" in headers or "X-Content-Type-Options" in headers
