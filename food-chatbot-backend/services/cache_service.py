"""
Cache service for query results.
"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cachetools import TTLCache
from config import settings
from database import db_manager


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
        Create hash for query.
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Hash string
        """
        content = f"{query}:{language}".lower()
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
        
        Args:
            query: Query text
            language: Language code
            
        Returns:
            Cached result or None
        """
        query_hash = self._hash_query(query, language)
        
        async with db_manager.get_connection() as db:
            async with db.execute("""
                SELECT response, hit_count
                FROM query_cache
                WHERE query_hash = ? AND expires_at > datetime('now')
            """, (query_hash,)) as cursor:
                row = await cursor.fetchone()
                
                if row:
                    # Update hit count
                    await db.execute("""
                        UPDATE query_cache
                        SET hit_count = hit_count + 1
                        WHERE query_hash = ?
                    """, (query_hash,))
                    await db.commit()
                    
                    import json
                    return json.loads(row[0])
        
        return None
    
    async def set_in_db(self, query: str, result: Dict[str, Any], language: str = "vi"):
        """
        Store result in database cache.
        
        Args:
            query: Query text
            result: Result to cache
            language: Language code
        """
        query_hash = self._hash_query(query, language)
        expires_at = datetime.now() + timedelta(seconds=settings.CACHE_TTL)
        
        import json
        response_json = json.dumps(result, ensure_ascii=False)
        
        async with db_manager.get_connection() as db:
            # Insert or replace
            await db.execute("""
                INSERT OR REPLACE INTO query_cache
                (query_hash, query_text, response, language, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """, (query_hash, query, response_json, language, expires_at))
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


# Global instance
cache_service = CacheService()
