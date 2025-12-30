"""
Streaming Response Service for Real-time AI Responses with Groq
Implements Server-Sent Events (SSE) for ChatGPT-like streaming experience.
Powered by Groq Cloud with Llama 3.3 70B (primary) and fallback models.
"""
import logging
from typing import AsyncGenerator, Dict, Any, Optional
import asyncio
import json
from services.groq_service import get_groq_service

logger = logging.getLogger(__name__)


class StreamingService:
    """
    Handles streaming responses for better UX.
    Reduces perceived latency from 3-5s to instant feedback.
    """
    
    def __init__(self):
        self.chunk_delay = 0.03  # 30ms between chunks for smooth display
        self.groq_service = None
    
    async def stream_chat_response(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        restaurants: Optional[list] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat response token by token.
        
        Yields:
            JSON strings with format: {"type": "chunk", "content": "..."}
                                     {"type": "done"}
                                     {"type": "error", "message": "..."}
        """
        try:
            # Build full prompt with context
            full_prompt = self._build_streaming_prompt(prompt, context, restaurants)
            
            # Determine if we need fallback model
            use_fallback = len(full_prompt) > 3000 or (context and context.get('retry_count', 0) > 1)
            
            # Get streaming response from Groq
            async for chunk in self._stream_groq_response(full_prompt, use_fallback):
                yield json.dumps({
                    "type": "chunk",
                    "content": chunk
                }) + "\n"
                
                # Small delay for smooth streaming
                await asyncio.sleep(self.chunk_delay)
            
            # Send completion signal
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
    
    async def _stream_groq_response(self, prompt: str, use_fallback: bool = False) -> AsyncGenerator[str, None]:
        """Stream response from Groq API with intelligent model selection."""
        try:
            # Initialize Groq service if needed
            if not self.groq_service:
                self.groq_service = get_groq_service()
            
            # Build messages for Groq
            messages = [
                {
                    "role": "system",
                    "content": "Bạn là trợ lý tìm kiếm nhà hàng thông minh tại TP.HCM. Trả lời ngắn gọn, tự nhiên và hữu ích."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            
            # Stream from Groq
            async for chunk in self.groq_service.generate_streaming(
                messages=messages,
                temperature=0.7,
                max_tokens=2048,
                use_fallback=use_fallback
            ):
                yield chunk
                    
        except Exception as e:
            logger.error(f"Groq streaming error: {e}", exc_info=True)
            # Try fallback model if primary failed
            if not use_fallback:
                logger.info("Retrying with fallback model...")
                async for chunk in self._stream_groq_response(prompt, use_fallback=True):
                    yield chunk
            else:
                raise
    
    def _build_streaming_prompt(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]],
        restaurants: Optional[list]
    ) -> str:
        """Build prompt for streaming response."""
        prompt_parts = []
        
        # System instruction
        prompt_parts.append("""Bạn là trợ lý tìm kiếm nhà hàng thông minh tại TP.HCM.
Nhiệm vụ: Trả lời câu hỏi người dùng về nhà hàng một cách tự nhiên, thân thiện.

Hướng dẫn:
- Trả lời ngắn gọn, súc tích
- Ưu tiên thông tin quan trọng nhất
- Sử dụng emoji phù hợp
- Không cần giải thích quá chi tiết
""")
        
        # Add context if available
        if context:
            previous_messages = context.get('previous_messages', [])
            if previous_messages:
                prompt_parts.append("\n## Lịch sử hội thoại:")
                for msg in previous_messages[-3:]:  # Last 3 messages
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    prompt_parts.append(f"{role}: {content}")
        
        # Add restaurant results if available
        if restaurants:
            prompt_parts.append("\n## Kết quả tìm kiếm:")
            for i, rest in enumerate(restaurants[:5], 1):  # Top 5
                name = rest.get('name', 'N/A')
                rating = rest.get('rating', 'N/A')
                price = rest.get('price_level', 'N/A')
                cuisine = rest.get('food_tags', 'N/A')
                address = rest.get('address', 'N/A')
                
                prompt_parts.append(f"""
{i}. **{name}**
   - Đánh giá: {rating}⭐
   - Giá: {price}
   - Món: {cuisine}
   - Địa chỉ: {address}
""")
        
        # Add user query
        prompt_parts.append(f"\n## Câu hỏi người dùng:\n{user_query}")
        
        # Add instruction for response
        prompt_parts.append("""
## Trả lời:
(Hãy trả lời ngắn gọn, tự nhiên, và hữu ích)
""")
        
        return "\n".join(prompt_parts)
    
    async def stream_search_progress(
        self,
        query: str,
        search_func
    ) -> AsyncGenerator[str, None]:
        """
        Stream search progress updates for better UX.
        
        Yields progress updates as search progresses:
        1. Understanding query
        2. Searching database
        3. Personalizing results
        4. Generating response
        """
        try:
            # Step 1: Understanding
            yield json.dumps({
                "type": "progress",
                "step": 1,
                "total": 4,
                "message": "🔍 Đang phân tích yêu cầu..."
            }) + "\n"
            await asyncio.sleep(0.2)
            
            # Step 2: Searching
            yield json.dumps({
                "type": "progress",
                "step": 2,
                "total": 4,
                "message": "🍽️ Đang tìm kiếm nhà hàng..."
            }) + "\n"
            await asyncio.sleep(0.3)
            
            # Execute search
            results = await search_func(query)
            
            # Step 3: Personalizing
            yield json.dumps({
                "type": "progress",
                "step": 3,
                "total": 4,
                "message": "✨ Đang cá nhân hóa kết quả..."
            }) + "\n"
            await asyncio.sleep(0.2)
            
            # Step 4: Generating response
            yield json.dumps({
                "type": "progress",
                "step": 4,
                "total": 4,
                "message": "💬 Đang tạo câu trả lời..."
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Send results
            yield json.dumps({
                "type": "results",
                "data": results
            }) + "\n"
            
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
    
    async def stream_hybrid_search(
        self,
        query: str,
        semantic_search_func,
        keyword_search_func,
        merge_func
    ) -> AsyncGenerator[str, None]:
        """
        Stream hybrid search with progress updates.
        Shows parallel semantic and keyword search progress.
        """
        try:
            # Start parallel searches
            yield json.dumps({
                "type": "progress",
                "message": "🔍 Semantic search..."
            }) + "\n"
            
            semantic_task = asyncio.create_task(semantic_search_func(query))
            
            yield json.dumps({
                "type": "progress",
                "message": "📝 Keyword search..."
            }) + "\n"
            
            keyword_task = asyncio.create_task(keyword_search_func(query))
            
            # Wait for both
            semantic_results, keyword_results = await asyncio.gather(
                semantic_task, keyword_task
            )
            
            yield json.dumps({
                "type": "progress",
                "message": "🔀 Merging results..."
            }) + "\n"
            
            # Merge results
            final_results = await merge_func(semantic_results, keyword_results)
            
            # Send final results
            yield json.dumps({
                "type": "results",
                "data": final_results,
                "metadata": {
                    "semantic_count": len(semantic_results),
                    "keyword_count": len(keyword_results),
                    "final_count": len(final_results)
                }
            }) + "\n"
            
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
    
    async def stream_conversation_context(
        self,
        messages: list[Dict[str, str]]
    ) -> AsyncGenerator[str, None]:
        """
        Stream conversation summary for context understanding.
        Useful for showing "Chatbot is typing..." with context awareness.
        """
        try:
            # Analyze conversation
            yield json.dumps({
                "type": "analysis",
                "message": "📊 Analyzing conversation..."
            }) + "\n"
            await asyncio.sleep(0.1)
            
            # Extract key topics
            topics = self._extract_topics(messages)
            
            yield json.dumps({
                "type": "context",
                "topics": topics,
                "message_count": len(messages)
            }) + "\n"
            
            yield json.dumps({"type": "done"}) + "\n"
            
        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e)
            }) + "\n"
    
    def _extract_topics(self, messages: list[Dict[str, str]]) -> list[str]:
        """Extract main topics from conversation (simple keyword extraction)."""
        # Simple implementation - can be enhanced with NLP
        keywords = set()
        
        common_food_keywords = [
            'pizza', 'sushi', 'phở', 'bún', 'cơm', 'mì', 'bánh',
            'lẩu', 'nướng', 'hải sản', 'chay', 'ăn vặt'
        ]
        
        for msg in messages:
            content = msg.get('content', '').lower()
            for keyword in common_food_keywords:
                if keyword in content:
                    keywords.add(keyword)
        
        return list(keywords)


# Global instance
streaming_service = StreamingService()
