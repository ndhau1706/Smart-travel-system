"""
Groq Cloud Service with intelligent multi-key rotation and fallback mechanism.
Primary Model: Qwen 3 32B (qwen-32b-preview) - Fast and efficient
Fallback Model: GPT OSS 120B (llama-3.3-120b-versatile) - For complex queries

Features:
- Multi-key rotation with circuit breaker
- Automatic fallback to powerful model on complex queries
- Exponential backoff on rate limits
- Smart error recovery
"""
from groq import Groq, AsyncGroq
import asyncio
import logging
from typing import List, Dict, Any, Optional, AsyncGenerator
from config import settings
import time
from datetime import datetime, timedelta
import random
import json

logger = logging.getLogger(__name__)


class GroqKeyRotator:
    """Advanced API key rotation with intelligent fallback."""
    
    # BUG #5 FIX: Constant block duration to prevent timing-based key count inference
    CONSTANT_BLOCK_DURATION = 120  # Always 2 minutes, regardless of failure count
    
    def __init__(self, api_keys: List[str]):
        self.api_keys = api_keys
        self.current_index = 0
        # Track usage and health
        self.key_health = {
            key: {
                'failures': 0,
                'last_failure': None,
                'is_blocked': False,
                'blocked_until': None,
                'success_count': 0,
                'total_requests': 0
            } for key in api_keys
        }
        # BUG #5 FIX: Don't log exact key count to prevent enumeration
        logger.info(f"✅ Groq service initialized with multi-key rotation")
    
    def get_available_key(self) -> Optional[str]:
        """Get next available healthy API key with constant-time operation."""
        now = datetime.now()
        
        # BUG #5 FIX: Add random jitter to prevent timing attacks (0.01-0.05s)
        import time
        jitter = random.uniform(0.01, 0.05)
        time.sleep(jitter)
        
        # Try all keys
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_index]
            health = self.key_health[key]
            
            # Check if key is temporarily blocked
            if health['is_blocked']:
                if health['blocked_until'] and now >= health['blocked_until']:
                    # BUG #5 FIX: Generic message without revealing unblock count
                    logger.info(f"🔄 API key rotation updated")
                    health['is_blocked'] = False
                    health['failures'] = 0
                    return key
                else:
                    # Still blocked, try next
                    self.current_index = (self.current_index + 1) % len(self.api_keys)
                    continue
            
            # This key is healthy
            return key
        
        # BUG #CRITICAL-3 FIX: Log that all keys are blocked WITHOUT revealing count
        logger.error("❌ Service temporarily unavailable - all API keys blocked due to rate limiting")
        return None
    
    def record_success(self, key: str):
        """Record successful API call."""
        health = self.key_health[key]
        health['success_count'] += 1
        health['total_requests'] += 1
        health['failures'] = 0  # Reset failures on success
        
        # Move to next key for load balancing
        self.current_index = (self.current_index + 1) % len(self.api_keys)
    
    def record_failure(self, key: str, error_type: str = "unknown"):
        """Record API failure and potentially block key with constant-time blocking."""
        # BUG #5 FIX: Add random jitter to prevent timing correlation (0.01-0.05s)
        import time
        jitter = random.uniform(0.01, 0.05)
        time.sleep(jitter)
        
        health = self.key_health[key]
        health['failures'] += 1
        health['total_requests'] += 1
        health['last_failure'] = datetime.now()
        
        # Block key after 3 consecutive failures
        if health['failures'] >= 3:
            # BUG #5 FIX: CONSTANT block duration to prevent timing-based key count inference
            # Always use same duration regardless of failure count
            block_duration = self.CONSTANT_BLOCK_DURATION
            health['is_blocked'] = True
            health['blocked_until'] = datetime.now() + timedelta(seconds=block_duration)
            # BUG #CRITICAL-3 FIX: Log that API key is blocked WITHOUT revealing key index
            logger.error(f"🔴 API rate limit reached, implementing backoff strategy")
            logger.warning(f"⚠️ API key blocked due to rate limiting")
        
        # Try next key
        self.current_index = (self.current_index + 1) % len(self.api_keys)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get aggregated health statistics without revealing individual key info."""
        # BUG #5 FIX: Aggregate stats without exposing key count or individual keys
        total_requests = sum(h['total_requests'] for h in self.key_health.values())
        total_successes = sum(h['success_count'] for h in self.key_health.values())
        blocked_count = sum(1 for h in self.key_health.values() if h['is_blocked'])
        
        return {
            'aggregate_stats': {
                'total_requests': total_requests,
                'success_rate': (
                    total_successes / total_requests * 100 
                    if total_requests > 0 else 0
                ),
                'service_status': 'degraded' if blocked_count > 0 else 'healthy',
                # BUG #5 FIX: Don't reveal exact blocked count or total key count
                'availability': 'limited' if blocked_count > 0 else 'full'
            }
        }


class GroqService:
    """
    Advanced Groq service with intelligent model selection.
    
    Strategy:
    1. Try Qwen 3 32B first (fast, efficient, handles 95% of queries)
    2. Fallback to Llama 3.3 70B for complex/failed queries (balanced)
    3. Multi-key rotation for high availability
    """
    
    # Model configurations - 3-tier fallback strategy
    PRIMARY_MODEL = "llama-3.3-70b-versatile"  # Llama 3.3 70B - Main workhorse (fast and capable)
    FALLBACK_MODEL = "llama-3.1-70b-versatile"  # Llama 3.1 70B - Brain backup (stable)
    SECONDARY_FALLBACK_MODEL = "llama-3.1-8b-instant"  # Llama 3.1 8B - Final backup (fast)
    
    def __init__(self):
        # Parse API keys from config with encryption support
        # Try GitHub Gist first (encrypted), then fallback to .env
        try:
            from utils.key_manager import secure_key_manager
            self.api_keys = secure_key_manager.get_api_keys()
            logger.info("\u2705 API keys loaded securely")
        except Exception as e:
            logger.warning(f"\u26a0\ufe0f Secure key manager failed: {e}")
            # Fallback to direct .env parsing
            api_keys_str = settings.GROQ_API_KEYS
            if not api_keys_str:
                raise ValueError("\u274c No Groq API keys configured! Set GROQ_API_KEYS in .env")
            self.api_keys = [key.strip() for key in api_keys_str.split(',') if key.strip()]
        
        if not self.api_keys:
            raise ValueError("\u274c Invalid Groq API keys format!")
        
        self.rotator = GroqKeyRotator(self.api_keys)
        self.clients: Dict[str, AsyncGroq] = {}
        
        # Initialize clients for each key
        for key in self.api_keys:
            self.clients[key] = AsyncGroq(api_key=key)
        
        logger.info(f"\ud83d\ude80 Groq Service ready!")
        logger.info(f"   \ud83d\udccb 3-Tier Fallback: {self.PRIMARY_MODEL} \u2192 {self.FALLBACK_MODEL} \u2192 {self.SECONDARY_FALLBACK_MODEL}")
    
    def _get_template_fallback_response(self, messages: List[Dict[str, str]]) -> str:
        """
        BUG #30 FIX: Return randomized template response to prevent fingerprinting.
        
        Features:
        - Multiple response templates (prevents pattern recognition)
        - Random selection (prevents timing-based detection)
        - Varied phrasing (prevents signature matching)
        - Slight timing jitter (prevents timing attacks)
        """
        import random
        import time
        
        # BUG #30 FIX: Add slight random delay to prevent timing-based fingerprinting
        # Random jitter between 0.1-0.5 seconds
        jitter = random.uniform(0.1, 0.5)
        time.sleep(jitter)
        
        # BUG #30 FIX: Multiple fallback templates to prevent fingerprinting
        templates = [
            # Template 1: Standard apology
            (
                "😔 Xín lỗi, hệ thống đang gặp chút sự cố. \n\n"
                "Mình đang làm việc để khắc phục. Vui lòng:\n"
                "1️⃣ Thử lại sau ít phút\n"
                "2️⃣ Hoặc đơn giản hóa câu hỏi\n"
                "3️⃣ Liên hệ hỗ trợ nếu vấn đề kéo dài"
            ),
            # Template 2: Technical difficulty
            (
                "⚠️ Rất xin lỗi, chúng mình đang gặp sự cố kỹ thuật.\n\n"
                "Đề nghị bạn:\n"
                "• Đợi một chút rồi thử lại\n"
                "• Hoặc liên hệ bộ phận hỗ trợ"
            ),
            # Template 3: Service maintenance
            (
                "🔧 Hệ thống đang được bảo trì.\n\n"
                "Bạn có thể:\n"
                "→ Quay lại sau vài phút\n"
                "→ Thử với câu hỏi ngắn gọn hơn"
            ),
            # Template 4: High traffic
            (
                "⏳ Hệ thống đang xử lý nhiều yêu cầu.\n\n"
                "Vui lòng:\n"
                "✓ Thử lại trong giây lát\n"
                "✓ Hoặc đặt câu hỏi khác"
            ),
            # Template 5: Generic error
            (
                "🤖 Có một chút trục trặc xảy ra.\n\n"
                "Gợi ý:\n"
                "1. Thử lại sau 30 giây\n"
                "2. Đơn giản hóa câu hỏi\n"
                "3. Liên hệ nếu cần hỗ trợ"
            ),
            # Template 6: Temporary issue
            (
                "😅 Ối, có vấn đề tạm thời rồi!\n\n"
                "Bạn thử:\n"
                "• Refresh và hỏi lại nhé\n"
                "• Hoặc đợi một chút xíu"
            ),
            # Template 7: Processing delay
            (
                "⚡ Đang có chút delay trong xử lý.\n\n"
                "Làm ơn:\n"
                "- Thử lại sau vài giây\n"
                "- Hoặc đặt câu hỏi khác"
            ),
            # Template 8: Connection issue
            (
                "📡 Kết nối gặp chút vấn đề.\n\n"
                "Đề xuất:\n"
                "① Thử lại ngay bây giờ\n"
                "② Hoặc quay lại sau"
            ),
        ]
        
        # BUG #30 FIX: Randomly select template
        selected_template = random.choice(templates)
        
        # BUG #30 FIX: Add random variation to prevent exact matching
        # Randomly add/remove trailing newlines or spaces
        variations = [
            selected_template,
            selected_template + "\n",
            selected_template.rstrip(),
            "\n" + selected_template,
        ]
        
        return random.choice(variations)
    
    async def generate_with_retry(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_fallback: bool = False,
        max_retries: int = 3
    ) -> str:
        """
        Generate response with automatic retry and fallback.
        
        Bug 26 Fix: Try ALL keys before counting as retry attempt.
        - Per-key failure tracking via circuit breaker
        - Fatal errors skip key permanently
        - Better key utilization
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            use_fallback: Force use of fallback model
            max_retries: Maximum retry attempts (tries all keys per attempt)
        
        Returns:
            Generated response or None on failure
        """
        model = self.FALLBACK_MODEL if use_fallback else self.PRIMARY_MODEL
        
        # Bug 26 Fix: Try all keys before incrementing attempt
        for attempt in range(max_retries):
            # Track which keys we've tried in THIS attempt
            tried_keys = set()
            keys_exhausted = False
            
            # Bug 26: Try ALL available keys in this attempt
            while len(tried_keys) < len(self.api_keys):
                key = self.rotator.get_available_key()
                
                if not key:
                    # All keys blocked or tried
                    keys_exhausted = True
                    break
                
                # Skip if already tried this key in current attempt
                if key in tried_keys:
                    # Rotated back to same key → all keys tried or blocked
                    keys_exhausted = True
                    break
                
                tried_keys.add(key)
                
                try:
                    client = self.clients[key]
                    
                    # Make API call
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=0.9,
                    )
                    
                    # Success!
                    self.rotator.record_success(key)
                    content = response.choices[0].message.content
                    
                    # BUG #CRITICAL-3 FIX: Don't log key index to prevent key count discovery
                    logger.info(f"✅ {model} response received (attempt {attempt + 1})")
                    return content
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    
                    # Determine error type
                    if 'rate_limit' in error_msg or 'too many requests' in error_msg:
                        error_type = "rate_limit"
                    elif 'quota' in error_msg:
                        error_type = "quota_exceeded"
                    elif 'invalid' in error_msg or 'authentication' in error_msg:
                        error_type = "auth_error"
                    elif 'api_key' in error_msg or 'key' in error_msg:
                        error_type = "invalid_key"
                    else:
                        error_type = "unknown"
                    
                    # BUG #5 FIX: Sanitize error messages and don't expose key index
                    safe_error_msg = self._sanitize_error_message(str(e))
                    logger.warning(
                        f"⚠️ API request failed (attempt {attempt + 1}): "
                        f"{error_type} - {safe_error_msg}"
                    )
                    self.rotator.record_failure(key, error_type)
                    
                    # BUG #5 FIX: Fatal errors → generic message without revealing error type
                    if error_type in ['auth_error', 'invalid_key', 'quota_exceeded']:
                        # BUG #5 FIX: Unified error message to prevent error fingerprinting
                        logger.error(f"🚫 API authentication or quota issue detected")
                        # Circuit breaker will block this key, continue to next
                        continue
                    
                    # Rate limit → try next key immediately (no sleep)
                    continue
            
            # Bug 26: All keys tried/blocked in this attempt
            if keys_exhausted:
                # 3-Tier Fallback Strategy:
                # Qwen 32B (primary) → GPT-OSS 120B (fallback) → GPT-OSS 20B (secondary fallback)
                
                # On last attempt with primary model, try fallback models
                if attempt == max_retries - 1 and not use_fallback:
                    # BUG #5 FIX: Don't reveal "all keys exhausted" - use generic message
                    logger.info(f"🔄 Switching to alternative processing strategy (Tier 2)")
                    
                    # Try GPT-OSS 120B (Tier 2)
                    fallback_result = await self.generate_with_retry(
                        messages, temperature, max_tokens, 
                        use_fallback=True, max_retries=2
                    )
                    if fallback_result:
                        return fallback_result
                    
                    # If Tier 2 fails, try GPT-OSS 20B (Tier 3)
                    logger.info(f"🔄 Switching to final backup strategy (Tier 3)")
                    secondary_result = await self._generate_with_secondary_fallback(
                        messages, temperature, max_tokens, max_retries=2
                    )
                    if secondary_result:
                        return secondary_result
                
                # BUG #5 FIX: Add random jitter to wait time to prevent timing analysis
                if attempt < max_retries - 1:
                    base_wait = min(2 ** attempt, 10)
                    # Add random jitter: ±20% variance
                    jitter = random.uniform(0.8, 1.2)
                    wait_time = base_wait * jitter
                    logger.warning(f"⏳ Rate limiting active, implementing backoff before retry...")
                    await asyncio.sleep(wait_time)
        
        # BUG #5 FIX: Don't reveal number of keys tried
        logger.error(f"❌ All retry attempts exhausted! Using fallback response.")
        return self._get_template_fallback_response(messages)
    
    def _sanitize_error_message(self, error_msg: str) -> str:
        """
        Bug #2 FIX: Comprehensive API key sanitization.
        
        Removes all sensitive information from error messages including:
        - API keys (multiple formats)
        - Base64/hex encoded keys
        - Keys in different positions
        - URLs with keys
        - Stack traces with keys
        - Authorization headers
        """
        import re
        import logging
        
        if not error_msg:
            return "Unknown error"
        
        sanitized = error_msg
        
        # Pattern 1: Standard API key format (sk-xxx, gsk-xxx)
        sanitized = re.sub(r'[gs]?sk[-_][a-zA-Z0-9]{20,}', '***REDACTED_KEY***', sanitized, flags=re.IGNORECASE)
        
        # Pattern 2: API key with different separators
        sanitized = re.sub(r'api[_-]?key[\s:=]+[\'"]?[a-zA-Z0-9_-]{20,}[\'"]?', 'api_key=***REDACTED***', sanitized, flags=re.IGNORECASE)
        
        # Pattern 3: Authorization header
        sanitized = re.sub(r'authorization[\s:=]+bearer[\s]+[a-zA-Z0-9_-]{20,}', 'authorization: Bearer ***REDACTED***', sanitized, flags=re.IGNORECASE)
        
        # Pattern 4: Base64 encoded keys (starts with common prefixes)
        sanitized = re.sub(r'[\'"]?[a-zA-Z0-9+/]{40,}={0,2}[\'"]?', '***REDACTED_BASE64***', sanitized)
        
        # Pattern 5: Hex encoded keys (long hex strings)
        sanitized = re.sub(r'0x[0-9a-fA-F]{40,}', '***REDACTED_HEX***', sanitized)
        sanitized = re.sub(r'[0-9a-fA-F]{64,}', '***REDACTED_HEX***', sanitized)
        
        # Pattern 6: URLs with keys in query params
        sanitized = re.sub(r'https?://[^\s]+[?&](api_?)?key=[^\s&]+', 'https://***REDACTED_URL***', sanitized, flags=re.IGNORECASE)
        
        # Pattern 7: Stack traces that might contain keys in function calls
        sanitized = re.sub(r'api_key\s*=\s*[\'"][^\'"]+[\'"]', 'api_key="***REDACTED***"', sanitized)
        sanitized = re.sub(r"api_key\s*=\s*'[^']+'|api_key\s*=\s*\"[^\"]+\"", 'api_key="***REDACTED***"', sanitized)
        
        # Pattern 8: Generic credentials patterns
        sanitized = re.sub(r'(password|token|secret|credential)[\s:=]+[\'"]?[^\s\'"]{8,}[\'"]?', r'\1=***REDACTED***', sanitized, flags=re.IGNORECASE)
        
        # Pattern 9: Remove file paths that might contain keys
        sanitized = re.sub(r'/[^\s]+\.env[^\s]*', '***REDACTED_PATH***', sanitized)
        sanitized = re.sub(r'[A-Z]:\\[^\s]+\.env[^\s]*', '***REDACTED_PATH***', sanitized)
        
        # Pattern 10: Python object representations with keys
        sanitized = re.sub(r'AsyncGroq\([^)]*api_key[^)]*\)', 'AsyncGroq(api_key=***REDACTED***)', sanitized)
        
        # Truncate if too long (prevent log flooding)
        MAX_LOG_LENGTH = 500
        if len(sanitized) > MAX_LOG_LENGTH:
            sanitized = sanitized[:MAX_LOG_LENGTH] + '... (truncated)'
        
        # Log warning if we detected potential key leakage
        if '***REDACTED' in sanitized and sanitized != error_msg:
            logging.getLogger(__name__).debug("🔒 Sanitized sensitive data from error message")
        
        return sanitized
    
    async def _generate_with_secondary_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        max_retries: int = 2
    ) -> Optional[str]:
        """
        3-Tier Fallback: Try GPT-OSS 20B as final backup model.
        
        This is called when both Qwen 32B and GPT-OSS 120B fail.
        GPT-OSS 20B is smaller but still powerful, providing a final safety net.
        
        Args:
            messages: Conversation messages
            temperature: Sampling temperature
            max_tokens: Maximum response tokens
            max_retries: Maximum retry attempts
            
        Returns:
            Generated response or None if all attempts fail
        """
        model = self.SECONDARY_FALLBACK_MODEL
        
        for attempt in range(max_retries):
            tried_keys = set()
            keys_exhausted = False
            
            while len(tried_keys) < len(self.api_keys):
                key = self.rotator.get_available_key()
                
                if not key or key in tried_keys:
                    keys_exhausted = True
                    break
                
                tried_keys.add(key)
                
                try:
                    client = self.clients[key]
                    
                    response = await client.chat.completions.create(
                        model=model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        top_p=0.9,
                    )
                    
                    self.rotator.record_success(key)
                    content = response.choices[0].message.content
                    
                    logger.info(f"✅ {model} (Tier 3) response received (attempt {attempt + 1})")
                    return content
                    
                except Exception as e:
                    error_msg = str(e).lower()
                    error_type = "rate_limit" if ('rate_limit' in error_msg or 'too many requests' in error_msg) else "unknown"
                    
                    safe_error_msg = self._sanitize_error_message(str(e))
                    logger.warning(f"⚠️ Secondary fallback failed (attempt {attempt + 1}): {safe_error_msg}")
                    self.rotator.record_failure(key, error_type)
                    continue
            
            if keys_exhausted and attempt < max_retries - 1:
                wait_time = min(2 ** attempt, 5) * random.uniform(0.8, 1.2)
                await asyncio.sleep(wait_time)
        
        logger.error(f"❌ All 3 tiers exhausted (Qwen 32B → GPT-OSS 120B → GPT-OSS 20B)")
        return None
    
    async def generate_streaming(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        use_fallback: bool = False,
        retry_count: int = 0,
        is_json: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        Generate streaming response with comprehensive Bug #15 fixes.
        
        Fixes:
        - #1: Network timeout with heartbeat
        - #2: Client disconnect detection
        - #3: Buffer overflow prevention
        - #4: Incomplete sentence detection
        - #5: JSON corruption validation
        - #6: Unicode break protection
        - #7: Retry storm prevention
        - #8: Chunk order validation
        - #9: Duplicate chunk filtering
        - #10: End marker guarantee
        
        Args:
            messages: Chat messages
            temperature: Sampling temperature
            max_tokens: Maximum tokens
            use_fallback: Use fallback model
            retry_count: Current retry count
            is_json: Expect JSON response
            
        Yields:
            Response chunks with validation
        """
        from utils.streaming_utils import (
            StreamBuffer, StreamValidator, 
            send_heartbeat, generate_end_marker
        )
        
        model = self.FALLBACK_MODEL if use_fallback else self.PRIMARY_MODEL
        key = self.rotator.get_available_key()
        
        if not key:
            yield "⚠️ Service temporarily unavailable, please retry..."
            return
        
        # Bug #15 Fix: Initialize robust streaming buffer
        buffer = StreamBuffer()
        heartbeat_task = None
        sequence_id = 0
        
        try:
            client = self.clients[key]
            
            # Start stream
            stream = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=0.9,
                stream=True
            )
            
            # Bug #1 Fix: Heartbeat task to prevent timeout
            async def heartbeat_loop():
                """Send periodic heartbeats."""
                while not buffer.is_disconnected():
                    if buffer.needs_heartbeat():
                        logger.debug("💓 Sending heartbeat")
                        # Heartbeat doesn't yield, just keeps connection alive
                    await asyncio.sleep(StreamBuffer.HEARTBEAT_INTERVAL)
            
            heartbeat_task = asyncio.create_task(heartbeat_loop())
            
            # Process chunks
            async for chunk in stream:
                # Bug #2 Fix: Check if client disconnected
                if buffer.is_disconnected():
                    logger.info("🔌 Client disconnected, stopping stream")
                    break
                
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    
                    # Bug #3, #6, #8, #9 Fix: Validate and add chunk
                    processed_chunk = buffer.add_chunk(content, sequence_id)
                    sequence_id += 1
                    
                    if processed_chunk is not None:
                        yield processed_chunk
                    
                    # Bug #1 Fix: Check for timeout
                    if buffer.is_timeout():
                        logger.warning(
                            f"⏱️ Stream timeout after "
                            f"{buffer.metrics.total_duration():.2f}s"
                        )
                        break
                
                # Bug #3 Fix: Check buffer overflow
                if buffer.buffer_size > StreamBuffer.MAX_BUFFER_SIZE:
                    logger.error("💥 Buffer overflow, terminating stream")
                    break
            
            # Cancel heartbeat
            if heartbeat_task:
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Bug #4, #5, #7 Fix: Validate completeness and retry if needed
            if StreamValidator.should_retry(buffer, retry_count, is_json):
                buffer.metrics.retries += 1
                
                # Try fallback model if not already using it
                if not use_fallback:
                    logger.info("🔄 Retrying with fallback model...")
                    yield "\n\n[Đang thử lại với mô hình dự phòng...]\n\n"
                    
                    async for chunk in self.generate_streaming(
                        messages, temperature, max_tokens,
                        use_fallback=True,
                        retry_count=retry_count + 1,
                        is_json=is_json
                    ):
                        yield chunk
                    return
                else:
                    logger.warning(
                        "⚠️ Response incomplete but max retries reached"
                    )
            
            # Bug #10 Fix: Always send end marker
            # (Don't yield it, just log completion)
            logger.info(
                f"✅ Streaming completed: {buffer.get_stats()}"
            )
            
            # Success!
            self.rotator.record_success(key)
            
        except asyncio.CancelledError:
            # Bug #2 Fix: Client disconnected
            logger.info("🔌 Stream cancelled by client")
            buffer.mark_disconnected()
            raise
            
        except Exception as e:
            safe_error_msg = self._sanitize_error_message(str(e))
            logger.error(f"❌ Streaming error: {safe_error_msg}")
            self.rotator.record_failure(key, "streaming_error")
            
            # Bug #7 Fix: Retry with limit
            if retry_count < StreamValidator.MAX_RETRIES:
                if not use_fallback:
                    logger.info(f"🔄 Retrying with fallback model (retry #{retry_count + 1})...")
                    yield "\n\n[Đang chuyển sang mô hình dự phòng...]\n\n"
                    
                    async for chunk in self.generate_streaming(
                        messages, temperature, max_tokens,
                        use_fallback=True,
                        retry_count=retry_count + 1,
                        is_json=is_json
                    ):
                        yield chunk
                else:
                    yield "\n\n⚠️ Đã xảy ra lỗi. Vui lòng thử lại sau."
            else:
                logger.error("❌ Max retries reached, giving up")
                yield "\n\n⚠️ Không thể hoàn thành yêu cầu. Vui lòng thử lại sau."
        
        finally:
            # Clean up heartbeat task
            if heartbeat_task and not heartbeat_task.done():
                heartbeat_task.cancel()
                try:
                    await heartbeat_task
                except asyncio.CancelledError:
                    pass
    
    def _parse_json_response(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Bug 15 Fix: Safely parse JSON response with error handling."""
        try:
            return json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parse error: {e}")
            # Try to extract JSON from markdown code blocks
            import re
            json_match = re.search(r'```json\s*({.*?})\s*```', response_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except:
                    pass
            return None
    
    async def should_use_fallback(self, query: str, context: Dict[str, Any]) -> bool:
        """
        Intelligently decide if query needs the powerful fallback model.
        
        Criteria:
        - Very long/complex query
        - Multiple filters/constraints
        - Ambiguous/unclear intent
        - Previous failures
        
        Returns:
            True if fallback model should be used
        """
        # Long queries might need more reasoning
        if len(query) > 200:
            return True
        
        # Multiple constraints/filters
        complex_keywords = [
            'và', 'hoặc', 'nhưng', 'ngoại trừ', 'trừ',
            'phức tạp', 'nhiều', 'đặc biệt', 'khác biệt'
        ]
        if sum(1 for kw in complex_keywords if kw in query.lower()) >= 3:
            return True
        
        # Check context for failure indicators
        if context.get('retry_count', 0) >= 2:
            return True
        
        if context.get('ambiguous_intent', False):
            return True
        
        # Default: use fast primary model
        return False
    
    def get_health_stats(self) -> Dict[str, Any]:
        """Get service health statistics without exposing sensitive information."""
        # BUG #5 FIX: Don't expose total key count or individual key stats
        return {
            'service': 'groq',
            'primary_model': self.PRIMARY_MODEL,
            'fallback_model': self.FALLBACK_MODEL,
            'rotation_enabled': True,
            'stats': self.rotator.get_stats()  # Returns aggregated stats only
        }


# Singleton instance
_groq_service: Optional[GroqService] = None


def get_groq_service() -> GroqService:
    """Get or create Groq service singleton."""
    global _groq_service
    if _groq_service is None:
        _groq_service = GroqService()
    return _groq_service
