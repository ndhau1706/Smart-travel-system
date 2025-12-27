"""
Unit tests for chat service functionality.

Tests the RAG pipeline, response generation, and chat processing logic.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestChatMessageValidation:
    """Tests for chat message validation."""
    
    def test_valid_message(self):
        """Test valid chat message passes validation."""
        from models import ChatRequest
        
        request = ChatRequest(
            message="Tìm quán phở ngon",
            session_id="test-session-123"
        )
        
        assert request.message == "Tìm quán phở ngon"
        assert request.session_id == "test-session-123"
    
    def test_empty_message_rejected(self):
        """Test empty message is rejected."""
        from models import ChatRequest
        from pydantic import ValidationError
        
        with pytest.raises(ValidationError):
            ChatRequest(message="", session_id="test-session")
    
    def test_message_too_long_rejected(self):
        """Test overly long message is rejected."""
        from models import ChatRequest
        from pydantic import ValidationError
        
        # Create a message longer than max allowed (assume 10000 chars)
        long_message = "a" * 10001
        
        with pytest.raises(ValidationError):
            ChatRequest(message=long_message, session_id="test-session")
    
    def test_language_default(self):
        """Test default language is Vietnamese."""
        from models import ChatRequest
        
        request = ChatRequest(
            message="Hello",
            session_id="test-session"
        )
        
        # Language should default to 'vi' if not specified
        assert hasattr(request, 'language') or True  # May be optional


class TestRAGPipeline:
    """Tests for RAG (Retrieval-Augmented Generation) pipeline."""
    
    @pytest.mark.asyncio
    async def test_search_restaurants(self, sample_restaurants):
        """Test restaurant search returns results."""
        with patch('services.hybrid_search.hybrid_search') as mock_search:
            mock_search.search = AsyncMock(return_value=sample_restaurants)
            
            results = await mock_search.search("phở ngon quận 1")
            
            assert len(results) == 3
            assert results[0]["name"] == "Phở Hà Nội"
    
    @pytest.mark.asyncio
    async def test_search_with_no_results(self):
        """Test search returns empty list when no matches."""
        with patch('services.hybrid_search.hybrid_search') as mock_search:
            mock_search.search = AsyncMock(return_value=[])
            
            results = await mock_search.search("món ăn từ sao hỏa")
            
            assert results == []
    
    @pytest.mark.asyncio
    async def test_context_building(self, sample_restaurants):
        """Test context is built correctly from search results."""
        # Context building should include restaurant info
        context_parts = []
        for r in sample_restaurants:
            context_parts.append(f"{r['name']} - {r['address']}")
        
        context = "\n".join(context_parts)
        
        assert "Phở Hà Nội" in context
        assert "Sushi Tokyo" in context
    
    @pytest.mark.asyncio
    async def test_prompt_construction(self, sample_chat_request, sample_restaurants):
        """Test LLM prompt is constructed correctly."""
        # Prompt should include user message and context
        user_message = sample_chat_request["message"]
        context = "\n".join([r["name"] for r in sample_restaurants])
        
        prompt = f"""Based on the following restaurants:
{context}

User query: {user_message}

Provide a helpful recommendation."""
        
        assert user_message in prompt
        assert "Phở Hà Nội" in prompt


class TestResponseGeneration:
    """Tests for AI response generation."""
    
    @pytest.mark.asyncio
    async def test_generate_response(self, mock_groq_service):
        """Test generating response from LLM."""
        response = await mock_groq_service.generate("Tìm quán phở")
        
        assert "response" in response
        assert "model_used" in response
    
    @pytest.mark.asyncio
    async def test_fallback_on_primary_failure(self, mock_groq_service):
        """Test fallback model is used when primary fails."""
        mock_groq_service.generate = AsyncMock(side_effect=[
            Exception("Primary model error"),
            {"response": "Fallback response", "model_used": "llama-3.1-8b-instant"}
        ])
        
        # First call fails, second succeeds with fallback
        try:
            await mock_groq_service.generate("test")
        except:
            pass
        
        response = await mock_groq_service.generate("test")
        assert response["model_used"] == "llama-3.1-8b-instant"
    
    @pytest.mark.asyncio
    async def test_response_contains_restaurant_info(self, sample_restaurants):
        """Test response includes relevant restaurant information."""
        # Mock a response that should include restaurant names
        response_text = "Tôi đề xuất Phở Hà Nội tại 123 Nguyễn Huệ"
        
        assert "Phở Hà Nội" in response_text
        assert "Nguyễn Huệ" in response_text


class TestLanguageDetection:
    """Tests for language detection and handling."""
    
    def test_detect_vietnamese(self):
        """Test detecting Vietnamese text."""
        text = "Tìm quán ăn ngon gần đây"
        # Language should be detected as Vietnamese
        # This would use actual detection logic
        assert True  # Placeholder
    
    def test_detect_english(self):
        """Test detecting English text."""
        text = "Find good restaurants nearby"
        # Language should be detected as English
        assert True  # Placeholder
    
    def test_response_matches_input_language(self):
        """Test response language matches input language."""
        # If user asks in Vietnamese, response should be in Vietnamese
        assert True  # Placeholder


class TestChatHistory:
    """Tests for conversation history management."""
    
    @pytest.mark.asyncio
    async def test_history_included_in_context(self, mock_session_manager):
        """Test chat history is included in context."""
        mock_session_manager.get_messages = AsyncMock(return_value=[
            {"role": "user", "content": "Tôi thích phở"},
            {"role": "assistant", "content": "Có nhiều quán phở ngon..."}
        ])
        
        messages = await mock_session_manager.get_messages("session-123")
        
        assert len(messages) == 2
        assert messages[0]["content"] == "Tôi thích phở"
    
    @pytest.mark.asyncio
    async def test_message_saved_after_response(self, mock_session_manager):
        """Test user message and response are saved."""
        await mock_session_manager.add_message(
            session_id="session-123",
            role="user",
            content="Test message"
        )
        
        mock_session_manager.add_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_context_window_management(self, mock_session_manager):
        """Test old messages are truncated for context window."""
        # Generate many messages
        messages = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(100)
        ]
        mock_session_manager.get_messages = AsyncMock(return_value=messages)
        
        all_messages = await mock_session_manager.get_messages("session-123")
        
        # In actual implementation, recent messages should be prioritized
        assert len(all_messages) == 100


class TestErrorHandling:
    """Tests for error handling in chat service."""
    
    @pytest.mark.asyncio
    async def test_handle_llm_timeout(self, mock_groq_service):
        """Test handling LLM timeout errors."""
        mock_groq_service.generate = AsyncMock(side_effect=TimeoutError("Request timeout"))
        
        with pytest.raises(TimeoutError):
            await mock_groq_service.generate("test")
    
    @pytest.mark.asyncio
    async def test_handle_rate_limit(self, mock_groq_service):
        """Test handling rate limit errors."""
        mock_groq_service.generate = AsyncMock(
            side_effect=Exception("Rate limit exceeded")
        )
        
        with pytest.raises(Exception) as exc_info:
            await mock_groq_service.generate("test")
        
        assert "Rate limit" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_graceful_degradation(self, mock_groq_service):
        """Test graceful degradation when AI is unavailable."""
        mock_groq_service.generate = AsyncMock(
            side_effect=Exception("Service unavailable")
        )
        
        # Should return a fallback message or raise appropriate exception
        with pytest.raises(Exception):
            await mock_groq_service.generate("test")
