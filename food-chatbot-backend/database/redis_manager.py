"""
Redis Manager for Distributed Locking and Caching
Prevents race conditions and provides high-performance caching.
"""
import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
from config import settings


class RedisManager:
    """Manages Redis connections for distributed locking and caching."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
        self.redis_url = getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        
        # Cache TTLs
        self.SEARCH_CACHE_TTL = 300  # 5 minutes
        self.SESSION_CACHE_TTL = 1800  # 30 minutes
        self.USER_PROFILE_CACHE_TTL = 600  # 10 minutes
        
        # Lock settings
        self.LOCK_TIMEOUT = 10  # 10 seconds
        self.LOCK_SLEEP = 0.1  # 100ms
    
    async def init_redis(self):
        """Initialize Redis connection."""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )
    
    async def close_redis(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
    
    # ==================== Distributed Locking ====================
    
    async def acquire_lock(self, lock_key: str, timeout: int = None) -> bool:
        """
        Acquire a distributed lock.
        
        Args:
            lock_key: Unique key for the lock
            timeout: Lock timeout in seconds (default: self.LOCK_TIMEOUT)
            
        Returns:
            True if lock acquired, False otherwise
        """
        timeout = timeout or self.LOCK_TIMEOUT
        lock_name = f"lock:{lock_key}"
        
        # Use SET NX EX for atomic lock acquisition
        return await self.redis_client.set(
            lock_name, 
            "1", 
            nx=True,  # Only set if not exists
            ex=timeout  # Expire after timeout
        )
    
    async def release_lock(self, lock_key: str):
        """Release a distributed lock."""
        lock_name = f"lock:{lock_key}"
        await self.redis_client.delete(lock_name)
    
    async def with_lock(self, lock_key: str, timeout: int = None):
        """
        Context manager for distributed locking.
        
        Usage:
            async with redis_manager.with_lock("session:123"):
                # Critical section
                await update_session()
        """
        class LockContext:
            def __init__(self, manager, key, timeout):
                self.manager = manager
                self.key = key
                self.timeout = timeout
                self.acquired = False
            
            async def __aenter__(self):
                self.acquired = await self.manager.acquire_lock(self.key, self.timeout)
                if not self.acquired:
                    raise RuntimeError(f"Failed to acquire lock: {self.key}")
                return self
            
            async def __aexit__(self, exc_type, exc_val, exc_tb):
                if self.acquired:
                    await self.manager.release_lock(self.key)
        
        return LockContext(self, lock_key, timeout)
    
    # ==================== Caching ====================
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate a deterministic cache key using SHA256."""
        # Sort keys for consistency
        sorted_data = json.dumps(data, sort_keys=True)
        hash_value = hashlib.sha256(sorted_data.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    async def get_cached(self, key: str) -> Optional[Any]:
        """Get cached value."""
        value = await self.redis_client.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return None
    
    async def set_cached(self, key: str, value: Any, ttl: int = None):
        """Set cached value with TTL."""
        ttl = ttl or self.SEARCH_CACHE_TTL
        
        # Serialize value
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        
        await self.redis_client.setex(key, ttl, value)
    
    async def delete_cached(self, key: str):
        """Delete cached value."""
        await self.redis_client.delete(key)
    
    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        keys = []
        async for key in self.redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            await self.redis_client.delete(*keys)
    
    # ==================== Search Cache ====================
    
    async def get_search_cache(self, query: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Get cached search results."""
        cache_key = self._generate_cache_key("search", {
            "query": query,
            "params": params
        })
        return await self.get_cached(cache_key)
    
    async def set_search_cache(self, query: str, params: Dict[str, Any], 
                              results: Dict, ttl: int = None):
        """Cache search results."""
        cache_key = self._generate_cache_key("search", {
            "query": query,
            "params": params
        })
        ttl = ttl or self.SEARCH_CACHE_TTL
        await self.set_cached(cache_key, results, ttl)
    
    async def invalidate_search_cache(self):
        """Invalidate all search caches."""
        await self.delete_pattern("search:*")
    
    # ==================== Session Cache ====================
    
    async def get_session_cache(self, session_id: str) -> Optional[Dict]:
        """Get cached session data."""
        key = f"session:{session_id}"
        return await self.get_cached(key)
    
    async def set_session_cache(self, session_id: str, session_data: Dict, 
                               ttl: int = None):
        """Cache session data."""
        key = f"session:{session_id}"
        ttl = ttl or self.SESSION_CACHE_TTL
        await self.set_cached(key, session_data, ttl)
    
    async def delete_session_cache(self, session_id: str):
        """Delete session cache."""
        key = f"session:{session_id}"
        await self.delete_cached(key)
    
    async def extend_session_ttl(self, session_id: str, ttl: int = None):
        """Extend session TTL."""
        key = f"session:{session_id}"
        ttl = ttl or self.SESSION_CACHE_TTL
        await self.redis_client.expire(key, ttl)
    
    # ==================== User Profile Cache ====================
    
    async def get_user_profile_cache(self, user_id: str) -> Optional[Dict]:
        """Get cached user profile."""
        key = f"user_profile:{user_id}"
        return await self.get_cached(key)
    
    async def set_user_profile_cache(self, user_id: str, profile: Dict, 
                                    ttl: int = None):
        """Cache user profile."""
        key = f"user_profile:{user_id}"
        ttl = ttl or self.USER_PROFILE_CACHE_TTL
        await self.set_cached(key, profile, ttl)
    
    async def invalidate_user_profile_cache(self, user_id: str):
        """Invalidate user profile cache."""
        key = f"user_profile:{user_id}"
        await self.delete_cached(key)
    
    # ==================== Popular Query Cache ====================
    
    async def increment_query_count(self, query: str):
        """Increment query popularity counter."""
        key = f"query_count:{query.lower()}"
        await self.redis_client.incr(key)
        await self.redis_client.expire(key, 86400)  # 24 hours
    
    async def get_popular_queries(self, limit: int = 20) -> list[tuple[str, int]]:
        """Get most popular queries."""
        results = []
        async for key in self.redis_client.scan_iter(match="query_count:*"):
            count = await self.redis_client.get(key)
            query = key.replace("query_count:", "")
            results.append((query, int(count)))
        
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]
    
    async def warm_cache_for_popular_queries(self, search_func):
        """Warm cache for popular queries (run periodically)."""
        popular = await self.get_popular_queries(10)
        
        for query, count in popular:
            # Check if already cached
            cache_key = self._generate_cache_key("search", {
                "query": query,
                "params": {}
            })
            
            cached = await self.get_cached(cache_key)
            if not cached:
                # Execute search and cache
                try:
                    results = await search_func(query, {})
                    await self.set_search_cache(query, {}, results, 
                                               ttl=3600)  # 1 hour for popular
                except Exception as e:
                    print(f"Failed to warm cache for '{query}': {e}")
    
    # ==================== Rate Limiting ====================
    
    async def check_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """
        Check if rate limit is exceeded.
        
        Args:
            key: Rate limit key (e.g., "user:123", "ip:1.2.3.4")
            limit: Maximum requests allowed
            window: Time window in seconds
            
        Returns:
            True if under limit, False if exceeded
        """
        rate_key = f"rate:{key}"
        
        # Increment counter
        current = await self.redis_client.incr(rate_key)
        
        # Set expiry on first request
        if current == 1:
            await self.redis_client.expire(rate_key, window)
        
        return current <= limit
    
    async def get_rate_limit_remaining(self, key: str, limit: int) -> int:
        """Get remaining requests in current window."""
        rate_key = f"rate:{key}"
        current = await self.redis_client.get(rate_key)
        
        if current is None:
            return limit
        
        return max(0, limit - int(current))
    
    # ==================== Health Check ====================
    
    async def health_check(self) -> bool:
        """Check if Redis is healthy."""
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False


# Global instance
redis_manager = RedisManager()
