"""
Rate Limiting Middleware for API protection.
Prevents abuse and DDoS attacks.

BUG #13 FIX: Added manual reset, bypass for admin/internal, and per-user/session identification.
BUG #CRITICAL-5 FIX: Added Redis support for distributed rate limiting across multiple servers.
"""
from fastapi import Request, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, Set
import time
import logging
import os

# BUG #CRITICAL-5 FIX: Redis support for distributed rate limiting
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Enhanced rate limiter with reset capability and bypass options.
    
    BUG #13 FIX:
    - Manual reset for specific IPs/users/sessions
    - Bypass list for admin/internal requests
    - Per-user and per-session tracking (not just IP)
    - Premium user support with higher limits
    
    BUG #CRITICAL-5 FIX:
    - Redis-based distributed rate limiting for multi-server deployments
    - Automatic fallback to in-memory if Redis unavailable
    - Shared state across load-balanced servers
    - Persistent rate limits across server restarts
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 5000,
        redis_url: Optional[str] = None
    ):
        self.rpm = requests_per_minute
        self.rph = requests_per_hour
        self.rpd = requests_per_day
        
        # BUG #CRITICAL-5 FIX: Initialize Redis connection
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        
        if REDIS_AVAILABLE and redis_url:
            try:
                # Create Redis client (connection is lazy, will connect on first operation)
                redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.use_redis = True  # Will fallback if actual operation fails
                logger.info(f"✅ BUG #CRITICAL-5 FIX: Redis rate limiting enabled at {redis_url}")
            except Exception as e:
                logger.warning(f"⚠️ Redis initialization failed, falling back to in-memory: {e}")
                self.redis_client = None
                self.use_redis = False
        else:
            if not REDIS_AVAILABLE:
                logger.warning("⚠️ redis.asyncio not installed, using in-memory rate limiting")
            else:
                logger.info("ℹ️ Redis URL not provided, using in-memory rate limiting")
        
        # Storage: {identifier: {window: [timestamps]}}
        # BUG #CRITICAL-5 FIX: In-memory fallback only used if Redis unavailable
        self._requests: Dict[str, Dict[str, list]] = {}
        
        # BUG #13 FIX: Bypass and premium tracking
        self._bypass_ips: Set[str] = set()  # Admin/internal IPs
        self._bypass_users: Set[str] = set()  # Admin users
        self._bypass_sessions: Set[str] = set()  # Admin sessions
        self._premium_users: Set[str] = set()  # Premium users (10x limits)
        self._whitelisted_ips: Set[str] = {'127.0.0.1', 'localhost'}  # Local testing
        
        # USER RATE LIMIT: Time-based limit for registered users (1-2 phút/prompt)
        self._user_last_request: Dict[str, datetime] = {}  # user_id -> last_request_time
        self.USER_MIN_INTERVAL = 60  # 60 seconds = 1 minute (configurable to 120 for 2 minutes)
    
    async def check_rate_limit(self, request: Request) -> None:
        """
        BUG #13 FIX: Enhanced rate limit check with bypass and per-user tracking.
        BUG #CRITICAL-5 FIX: Use Redis for distributed rate limiting if available.
        
        Priority order:
        1. Check bypass lists (admin/internal)
        2. Check per-user limits (if user_id in header/query)
        3. Check per-session limits (if session_id in header/query)
        4. Fall back to IP-based limits
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        # Get identifiers
        client_ip = self._get_client_ip(request)
        user_id = self._get_user_id(request)
        session_id = self._get_session_id(request)
        
        # BUG #13 FIX: Check bypass lists
        if self._should_bypass(client_ip, user_id, session_id):
            return  # Skip rate limiting for admin/internal
        
        # USER RATE LIMIT: Check time-based limit for registered users (1-2 phút/prompt)
        if user_id and not user_id.startswith('guest-'):
            await self._check_user_time_limit(user_id)
        
        # Determine primary identifier (prefer user > session > IP)
        identifier = user_id or session_id or client_ip
        is_premium = user_id and user_id in self._premium_users
        
        # BUG #CRITICAL-5 FIX: Use Redis if available, otherwise fall back to in-memory
        if self.use_redis and self.redis_client:
            await self._check_rate_limit_redis(identifier, is_premium)
        else:
            await self._check_rate_limit_memory(identifier, is_premium)
    
    async def _check_rate_limit_redis(self, identifier: str, is_premium: bool):
        """
        BUG #CRITICAL-5 FIX: Redis-based distributed rate limiting.
        
        Uses Redis INCR + EXPIRE for atomic operations.
        Shared across all server instances.
        """
        # Adjust limits for premium users
        rpm_limit = self.rpm * 10 if is_premium else self.rpm
        rph_limit = self.rph * 10 if is_premium else self.rph
        rpd_limit = self.rpd * 10 if is_premium else self.rpd
        
        now = time.time()
        
        # Redis keys with time windows
        minute_key = f"ratelimit:{identifier}:minute"
        hour_key = f"ratelimit:{identifier}:hour"
        day_key = f"ratelimit:{identifier}:day"
        
        try:
            # Use pipeline for atomic operations
            pipe = self.redis_client.pipeline()
            
            # Increment counters
            pipe.incr(minute_key)
            pipe.incr(hour_key)
            pipe.incr(day_key)
            
            # Set TTL if first request in window
            pipe.expire(minute_key, 60, nx=True)
            pipe.expire(hour_key, 3600, nx=True)
            pipe.expire(day_key, 86400, nx=True)
            
            # Get TTL for retry-after headers
            pipe.ttl(minute_key)
            pipe.ttl(hour_key)
            pipe.ttl(day_key)
            
            # Execute all commands atomically
            results = await pipe.execute()
            
            minute_count = results[0]
            hour_count = results[1]
            day_count = results[2]
            minute_ttl = results[6]
            hour_ttl = results[7]
            day_ttl = results[8]
            
            # Check minute limit
            if minute_count > rpm_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {rpm_limit} requests per minute. Try again in {minute_ttl} seconds.",
                    headers={"Retry-After": str(minute_ttl)}
                )
            
            # Check hour limit
            if hour_count > rph_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {rph_limit} requests per hour.",
                    headers={"Retry-After": str(hour_ttl)}
                )
            
            # Check day limit
            if day_count > rpd_limit:
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded: {rpd_limit} requests per day.",
                    headers={"Retry-After": str(day_ttl)}
                )
            
        except HTTPException:
            raise  # Re-raise rate limit errors
        except Exception as e:
            # BUG #CRITICAL-5 FIX: If Redis fails, fall back to in-memory
            logger.error(f"🔴 Redis rate limiting failed, falling back to in-memory: {e}")
            self.use_redis = False
            await self._check_rate_limit_memory(identifier, is_premium)
    
    async def _check_rate_limit_memory(self, identifier: str, is_premium: bool):
        """
        BUG #CRITICAL-5 FIX: In-memory fallback rate limiting.
        
        Note: This is NOT distributed - use Redis for production multi-server deployments.
        """
        # Initialize if new identifier
        if identifier not in self._requests:
            self._requests[identifier] = {
                'minute': [],
                'hour': [],
                'day': []
            }
        
        now = time.time()
        user_requests = self._requests[identifier]
        
        # Clean old requests
        self._cleanup_old_requests(user_requests, now)
        
        # BUG #13 FIX: Adjust limits for premium users
        rpm_limit = self.rpm * 10 if is_premium else self.rpm
        rph_limit = self.rph * 10 if is_premium else self.rph
        rpd_limit = self.rpd * 10 if is_premium else self.rpd
        
        # Check minute limit
        minute_count = len(user_requests['minute'])
        if minute_count >= rpm_limit:
            wait_time = 60 - (now - user_requests['minute'][0])
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rpm_limit} requests per minute. Try again in {wait_time:.0f} seconds.",
                headers={"Retry-After": str(int(wait_time))}
            )
        
        # Check hour limit
        hour_count = len(user_requests['hour'])
        if hour_count >= rph_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rph_limit} requests per hour.",
                headers={"Retry-After": "3600"}
            )
        
        # Check day limit
        day_count = len(user_requests['day'])
        if day_count >= rpd_limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {rpd_limit} requests per day.",
                headers={"Retry-After": "86400"}
            )
        
        # Record this request
        user_requests['minute'].append(now)
        user_requests['hour'].append(now)
        user_requests['day'].append(now)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For header (for proxies)
        forwarded = request.headers.get('X-Forwarded-For')
        if forwarded:
            return forwarded.split(',')[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get('X-Real-IP')
        if real_ip:
            return real_ip
        
        # Fallback to direct client
        return request.client.host if request.client else 'unknown'
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """BUG #13 FIX: Extract user_id from request."""
        # Check header
        user_id = request.headers.get('X-User-ID')
        if user_id:
            return user_id
        
        # Check query params
        if hasattr(request, 'query_params'):
            user_id = request.query_params.get('user_id')
            if user_id:
                return user_id
        
        return None
    
    def _get_session_id(self, request: Request) -> Optional[str]:
        """BUG #13 FIX: Extract session_id from request."""
        # Check header
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            return session_id
        
        # Check query params
        if hasattr(request, 'query_params'):
            session_id = request.query_params.get('session_id')
            if session_id:
                return session_id
        
        return None
    
    def _should_bypass(self, ip: str, user_id: Optional[str], session_id: Optional[str]) -> bool:
        """BUG #13 FIX: Check if request should bypass rate limiting."""
        # Check IP bypass (admin/internal)
        if ip in self._bypass_ips or ip in self._whitelisted_ips:
            return True
        
        # Check user bypass
        if user_id and user_id in self._bypass_users:
            return True
        
        # Check session bypass
        if session_id and session_id in self._bypass_sessions:
            return True
        
        return False
    
    def _cleanup_old_requests(self, user_requests: Dict[str, list], now: float):
        """Remove expired request timestamps."""
        # Minute: keep only last 60 seconds
        user_requests['minute'] = [
            t for t in user_requests['minute']
            if now - t < 60
        ]
        
        # Hour: keep only last 3600 seconds
        user_requests['hour'] = [
            t for t in user_requests['hour']
            if now - t < 3600
        ]
        
        # Day: keep only last 86400 seconds
        user_requests['day'] = [
            t for t in user_requests['day']
            if now - t < 86400
        ]
    
    def cleanup_all(self):
        """Cleanup all expired entries (call periodically)."""
        now = time.time()
        for identifier in list(self._requests.keys()):
            self._cleanup_old_requests(self._requests[identifier], now)
            # Remove identifier if no recent requests
            if not any(self._requests[identifier].values()):
                del self._requests[identifier]
    
    # BUG #13 FIX: Manual reset methods
    def reset_limit(self, identifier: str):
        """
        Manually reset rate limit for specific identifier (IP/user/session).
        Use case: User verified email, premium upgrade, testing, etc.
        """
        if identifier in self._requests:
            del self._requests[identifier]
    
    def reset_all_limits(self):
        """Reset all rate limits. Use with caution (e.g., system maintenance)."""
        self._requests.clear()
    
    # BUG #13 FIX: Bypass management
    def add_bypass_ip(self, ip: str):
        """Add IP to bypass list (admin/internal IPs)."""
        self._bypass_ips.add(ip)
    
    def remove_bypass_ip(self, ip: str):
        """Remove IP from bypass list."""
        self._bypass_ips.discard(ip)
    
    def add_bypass_user(self, user_id: str):
        """Add user to bypass list (admin users)."""
        self._bypass_users.add(user_id)
    
    def remove_bypass_user(self, user_id: str):
        """Remove user from bypass list."""
        self._bypass_users.discard(user_id)
    
    def add_bypass_session(self, session_id: str):
        """Add session to bypass list (temporary admin access)."""
        self._bypass_sessions.add(session_id)
    
    def remove_bypass_session(self, session_id: str):
        """Remove session from bypass list."""
        self._bypass_sessions.discard(session_id)
    
    # BUG #13 FIX: Premium user management
    def add_premium_user(self, user_id: str):
        """Add user to premium list (10x higher limits)."""
        self._premium_users.add(user_id)
    
    def remove_premium_user(self, user_id: str):
        """Remove user from premium list."""
        self._premium_users.discard(user_id)
    
    async def _check_user_time_limit(self, user_id: str):
        """
        USER RATE LIMIT: Check time-based limit for registered users.
        
        Registered users (not guests) can only send 1 prompt per 60-120 seconds
        to prevent spam while allowing genuine conversation.
        
        Args:
            user_id: User identifier
            
        Raises:
            HTTPException: If user sent request too quickly
        """
        # Skip for premium users
        if user_id in self._premium_users:
            return
        
        now = datetime.now()
        last_time = self._user_last_request.get(user_id)
        
        if last_time:
            elapsed = (now - last_time).total_seconds()
            if elapsed < self.USER_MIN_INTERVAL:
                wait_time = self.USER_MIN_INTERVAL - elapsed
                raise HTTPException(
                    status_code=429,
                    detail=f"Vui lòng đợi {int(wait_time)} giây trước khi gửi prompt tiếp. (Please wait {int(wait_time)} seconds before sending next prompt.)",
                    headers={"Retry-After": str(int(wait_time))}
                )
        
        # Update last request time
        self._user_last_request[user_id] = now
        
        # Cleanup old entries (keep only last 1 hour)
        cutoff_time = now - timedelta(hours=1)
        self._user_last_request = {
            uid: t for uid, t in self._user_last_request.items()
            if t > cutoff_time
        }
    
    # BUG #13 FIX: Query methods
    def get_remaining_requests(self, identifier: str) -> Dict[str, int]:
        """Get remaining requests for identifier."""
        if identifier not in self._requests:
            is_premium = identifier in self._premium_users
            rpm_limit = self.rpm * 10 if is_premium else self.rpm
            rph_limit = self.rph * 10 if is_premium else self.rph
            rpd_limit = self.rpd * 10 if is_premium else self.rpd
            
            return {
                'minute': rpm_limit,
                'hour': rph_limit,
                'day': rpd_limit
            }
        
        now = time.time()
        self._cleanup_old_requests(self._requests[identifier], now)
        
        is_premium = identifier in self._premium_users
        rpm_limit = self.rpm * 10 if is_premium else self.rpm
        rph_limit = self.rph * 10 if is_premium else self.rph
        rpd_limit = self.rpd * 10 if is_premium else self.rpd
        
        return {
            'minute': max(0, rpm_limit - len(self._requests[identifier]['minute'])),
            'hour': max(0, rph_limit - len(self._requests[identifier]['hour'])),
            'day': max(0, rpd_limit - len(self._requests[identifier]['day']))
        }


# Global instance
rate_limiter = RateLimiter(
    requests_per_minute=60,
    requests_per_hour=1000,
    requests_per_day=5000
)
