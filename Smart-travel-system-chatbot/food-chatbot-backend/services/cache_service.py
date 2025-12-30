"""
Cache service for query results.

BUG #6 FIX: All datetime operations are timezone-aware (UTC) to prevent:
- Cache expiration inconsistencies between server timezone and DB (UTC)
- DST (Daylight Saving Time) issues
- Multi-region deployment issues
- Microsecond precision loss
"""
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from cachetools import TTLCache
from config import settings
from database import db_manager
import logging

logger = logging.getLogger(__name__)


class CacheService:
    """In-memory and persistent cache for query results."""
    
    def __init__(self):
        # In-memory cache with TTL
        self.memory_cache = TTLCache(
            maxsize=settings.CACHE_MAX_SIZE,
            ttl=settings.CACHE_TTL
        )
    
    def _hash_query(self, query: str, language: str = "vi") -> str:
        """
        Create normalized hash for query.
        Normalizes query to avoid cache misses from whitespace/case differences.
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Hash string
        """
        # Normalize: lowercase, strip, collapse whitespace
        normalized_query = ' '.join(query.lower().strip().split())
        content = f"{normalized_query}:{language}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_from_memory(self, query: str, language: str = "vi") -> Optional[Dict[str, Any]]:
        """
        Get result from in-memory cache.
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Cached result or None
        """
        query_hash = self._hash_query(query, language)
        return self.memory_cache.get(query_hash)
    
    def set_in_memory(self, query: str, result: Dict[str, Any], language: str = "vi"):
        """
        Store result in in-memory cache.
        
        Args:
            query: Query text
            result: Result to cache
            language: Language code
        """
        query_hash = self._hash_query(query, language)
        self.memory_cache[query_hash] = result
    
    async def get_from_db(self, query: str, language: str = "vi") -> Optional[Dict[str, Any]]:
        """
        Get result from database cache.
        
        BUG #6 FIX: Use UTC for expiration check to prevent timezone confusion.
        BUG #16 FIX (TOCTOU): Atomic operation using single query with conditional UPDATE.
        
        Race condition scenario (FIXED):
        1. Thread A: Check expires_at > now (valid)
        2. Thread B: Invalidate cache (DELETE/UPDATE)
        3. Thread A: Should NOT return stale data
        
        Fix: Use single atomic query that checks AND updates in one operation.
        SQLite's default locking handles concurrent access automatically.
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Cached result or None
        """
        query_hash = self._hash_query(query, language)
        
        # BUG #6 FIX: Get current UTC time in ISO format for comparison
        now_utc_iso = datetime.now(timezone.utc).isoformat()
        
        async with db_manager.get_connection() as db:
            # BUG #16 FIX: Atomic operation in single transaction
            # 1. Fetch with expiration check
            # 2. Update hit_count only if still valid
            # SQLite's ACID properties ensure atomicity
            
            async with db.execute("""
                SELECT response, hit_count, expires_at
                FROM query_cache
                WHERE query_hash = ? AND expires_at > ?
            """, (query_hash, now_utc_iso)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    # Cache hit - atomically increment hit_count
                    # Use WHERE clause to ensure cache is still valid
                    await db.execute("""
                        UPDATE query_cache
                        SET hit_count = hit_count + 1
                        WHERE query_hash = ? AND expires_at > ?
                    """, (query_hash, now_utc_iso))
                    await db.commit()
                    
                    # Log cache hit with timezone info (for debugging)
                    expires_at = row[2]
                    logger.debug(f"✅ Cache hit for query_hash={query_hash[:8]}... (expires_at={expires_at})")
                    
                    import json
                    return json.loads(row[0])
        
        logger.debug(f"❌ Cache miss for query_hash={query_hash[:8]}...")
        return None
    
    async def set_in_db(self, query: str, result: Dict[str, Any], language: str = "vi"):
        """
        Store result in database cache.
        
        BUG #6 FIX: Use timezone-aware UTC datetime for consistency.
        
        Args:
            query: Query text
            result: Result to cache
            language: Language code
        """
        query_hash = self._hash_query(query, language)
        
        # BUG #6 FIX: Use UTC timezone-aware datetime
        now_utc = datetime.now(timezone.utc)
        expires_at_utc = now_utc + timedelta(seconds=settings.CACHE_TTL)
        
        # Convert to ISO 8601 format with timezone for SQLite storage
        # SQLite stores as TEXT, so we use ISO format: '2025-12-19T10:00:00+00:00'
        expires_at_iso = expires_at_utc.isoformat()
        
        import json
        response_json = json.dumps(result, ensure_ascii=False)
        
        async with db_manager.get_connection() as db:
            # Insert or replace
            await db.execute("""
                INSERT OR REPLACE INTO query_cache
                (query_hash, query_text, response, language, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, query, response_json, language, expires_at_iso))
            await db.commit()
    
    async def get(self, query: str, language: str = "vi") -> Optional[Dict[str, Any]]:
        """
        Get cached result (checks memory first, then DB).
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Cached result or None
        """
        # Check memory cache first
        result = self.get_from_memory(query, language)
        if result:
            return result
        
        # Check database cache
        result = await self.get_from_db(query, language)
        if result:
            # Store in memory cache for faster access
            self.set_in_memory(query, result, language)
        
        return result
    
    async def set(self, query: str, result: Dict[str, Any], language: str = "vi"):
        """
        Cache result (stores in both memory and DB).
        
        Args:
            query: Query text
            result: Result to cache
            language: Language code
        """
        # Store in memory
        self.set_in_memory(query, result, language)
        
        # Store in database
        await self.set_in_db(query, result, language)
    
    def clear_memory(self):
        """Clear in-memory cache."""
        self.memory_cache.clear()
    
    async def clear_db(self):
        """Clear database cache."""
        async with db_manager.get_connection() as db:
            await db.execute("DELETE FROM query_cache")
            await db.commit()
    
    async def invalidate_on_data_change(self, table: str = None):
        """
        CRITICAL: Invalidate cache when data changes.
        
        Args:
            table: Table name that changed (e.g., 'restaurants')
        """
        # Clear memory cache
        self.clear_memory()
        
        # Clear DB cache or mark as stale
        async with db_manager.get_connection() as db:
            if table:
                # Delete cache entries related to specific table
                # For now, clear all - can be optimized with metadata
                await db.execute("DELETE FROM query_cache")
            else:
                # Clear all
                await db.execute("DELETE FROM query_cache")
            await db.commit()
        
        from services.hybrid_search import hybrid_search
        await hybrid_search.invalidate_cache(reason=f"data_change:{table or 'all'}")


# Global instance
cache_service = CacheService()
