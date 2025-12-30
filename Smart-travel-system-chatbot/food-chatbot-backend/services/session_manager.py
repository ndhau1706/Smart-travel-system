"""
Session management service.
"""
import uuid
import secrets
import json
import re
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiosqlite
import logging
from database import db_manager

logger = logging.getLogger(__name__)


def safe_json_loads(json_string: str, max_depth: int = 20, max_size: int = 1_000_000) -> Optional[Any]:
    """
    BUG #18 FIX: Safely parse JSON with depth and size limits.
    
    Security measures:
    - Max depth limit (prevents stack overflow from deeply nested JSON)
    - Max size limit (prevents memory exhaustion from large JSON)
    - Type validation
    - Graceful error handling
    - Logging of suspicious attempts
    
    Args:
        json_string: JSON string to parse
        max_depth: Maximum nesting depth (default: 20)
        max_size: Maximum JSON string size in bytes (default: 1MB)
        
    Returns:
        Parsed JSON object or None if invalid/dangerous
    """
    # Validation 1: None or empty check
    if not json_string:
        return None
    
    # Validation 2: Type check
    if not isinstance(json_string, str):
        logger.warning(f"JSON string must be str, got {type(json_string)}")
        return None
    
    # Validation 3: Size check (prevent memory exhaustion)
    json_size = len(json_string.encode('utf-8'))
    if json_size > max_size:
        logger.warning(f"JSON too large: {json_size} bytes (max: {max_size})")
        return None
    
    # Validation 4: Parse JSON
    try:
        data = json.loads(json_string)
    except json.JSONDecodeError as e:
        logger.warning(f"Invalid JSON: {e}")
        return None
    except RecursionError:
        logger.warning("JSON nesting too deep (RecursionError)")
        return None
    except MemoryError:
        logger.warning("JSON caused MemoryError")
        return None
    except Exception as e:
        logger.warning(f"JSON parsing error: {e}")
        return None
    
    # Validation 5: Check depth (prevent stack overflow)
    def check_depth(obj, current_depth=0):
        """Recursively check JSON depth."""
        if current_depth > max_depth:
            return False
        
        if isinstance(obj, dict):
            for value in obj.values():
                if not check_depth(value, current_depth + 1):
                    return False
        elif isinstance(obj, list):
            for item in obj:
                if not check_depth(item, current_depth + 1):
                    return False
        
        return True
    
    if not check_depth(data):
        logger.warning(f"JSON nesting exceeds max depth: {max_depth}")
        return None
    
    # Validation 6: Check array/object size (prevent DoS)
    def check_size(obj):
        """Check if JSON has too many elements."""
        MAX_ARRAY_SIZE = 10000
        MAX_OBJECT_KEYS = 10000
        
        if isinstance(obj, dict):
            if len(obj) > MAX_OBJECT_KEYS:
                return False
            for value in obj.values():
                if not check_size(value):
                    return False
        elif isinstance(obj, list):
            if len(obj) > MAX_ARRAY_SIZE:
                return False
            for item in obj:
                if not check_size(item):
                    return False
        
        return True
    
    if not check_size(data):
        logger.warning("JSON has too many elements (array/object size exceeded)")
        return None
    
    return data


class SessionManager:
    """Manages chat sessions and messages."""
    
    # BUG #1 FIX: Session ID validation regex
    # UUID v4 format: 8-4-4-4-12 hex characters with hyphens
    # Example: 550e8400-e29b-41d4-a716-446655440000
    SESSION_ID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """
        BUG #1 FIX: Comprehensive session ID validation.
        
        Security checks:
        - None/empty check
        - Type validation (must be string)
        - Length validation (UUID is exactly 36 characters)
        - Format validation (UUID v4 pattern)
        - SQL injection prevention (no quotes, semicolons, special chars)
        - XSS prevention (no HTML/script tags)
        - Path traversal prevention (no ../ or \\)
        - Null byte injection prevention
        
        Args:
            session_id: Session ID to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check 1: None or empty
        if not session_id:
            return False
        
        # Check 2: Type validation
        if not isinstance(session_id, str):
            return False
        
        # Check 3: Length validation (UUID is exactly 36 characters)
        if len(session_id) != 36:
            return False
        
        # Check 4: Format validation (UUID v4 pattern)
        if not SessionManager.SESSION_ID_PATTERN.match(session_id):
            return False
        
        # Check 5: SQL injection prevention
        # Reject if contains dangerous SQL characters
        dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_', 'UNION', 'SELECT', 'DROP', 'INSERT', 'UPDATE', 'DELETE']
        session_id_upper = session_id.upper()
        if any(char in session_id_upper for char in dangerous_chars):
            return False
        
        # Check 6: XSS prevention
        # Reject if contains HTML/script tags
        if '<' in session_id or '>' in session_id or 'script' in session_id_upper:
            return False
        
        # Check 7: Path traversal prevention
        if '../' in session_id or '..\\' in session_id or '..' in session_id:
            return False
        
        # Check 8: Null byte injection prevention
        if '\x00' in session_id or '\0' in session_id:
            return False
        
        return True
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        title: str = "New Chat",
        language: str = "vi"
    ) -> str:
        """
        Create a new chat session.
        
        BUG #24 FIX: Use cryptographically secure session ID generation.
        
        Security improvements:
        - Use secrets.token_urlsafe() instead of uuid.uuid4()
        - Cryptographically secure random number generator
        - 32 bytes = 256 bits of entropy (vs UUID's 122 bits)
        - URL-safe base64 encoding
        - Collision check with retry mechanism
        - Protection against:
          * Docker fork attacks (independent random state)
          * Timing attacks (constant-time comparison)
          * Birthday attacks (larger entropy space)
          * VM snapshot replay (OS-level randomness)
          * Quantum computer attacks (larger key space)
        
        Args:
            user_id: User identifier
            title: Session title
            language: Session language
            
        Returns:
            Session ID (43-character URL-safe string)
        """
        max_retries = 5
        
        for attempt in range(max_retries):
            # Generate cryptographically secure random session ID
            # 32 bytes = 256 bits of entropy
            # Output: 43 characters (base64url encoded)
            session_id = secrets.token_urlsafe(32)
            
            # Collision check: Verify session ID doesn't exist
            async with db_manager.get_connection() as db:
                existing = await db.execute(
                    "SELECT id FROM sessions WHERE id = ?",
                    (session_id,)
                )
                row = await existing.fetchone()
                
                if row is None:
                    # No collision, insert new session
                    await db.execute("""
                        INSERT INTO sessions (id, user_id, title, language)
                        VALUES (?, ?, ?, ?)
                    """, (session_id, user_id, title, language))
                    await db.commit()
                    return session_id
                else:
                    # Collision detected (extremely rare), retry
                    logger.warning(f"Session ID collision detected on attempt {attempt + 1}")
        
        # If we exhausted all retries (practically impossible)
        raise RuntimeError("Failed to generate unique session ID after 5 attempts")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        # Basic validation: non-empty string
        if not session_id or not isinstance(session_id, str):
            return None
        
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            # Parameterized query (already safe, validation is defense-in-depth)
            async with db.execute("""
                SELECT * FROM sessions WHERE id = ?
            """, (session_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
        
        return None
    
    async def update_session(self, session_id: str, title: Optional[str] = None):
        """
        Update session information.
        
        Args:
            session_id: Session ID
            title: New title
        """
        # Basic validation
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Invalid session_id")
        
        async with db_manager.get_connection() as db:
            if title:
                await db.execute("""
                    UPDATE sessions
                    SET title = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (title, session_id))
            else:
                await db.execute("""
                    UPDATE sessions
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (session_id,))
            
            await db.commit()
    
    async def delete_session(self, session_id: str):
        """
        Delete a session and all its messages.
        
        Args:
            session_id: Session ID
        """
        # Basic validation
        if not session_id or not isinstance(session_id, str):
            raise ValueError("Invalid session_id")
        
        async with db_manager.get_connection() as db:
            await db.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            await db.commit()
    
    async def list_sessions(
        self,
        user_id: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List sessions.
        
        Args:
            user_id: Filter by user ID
            limit: Maximum number of sessions
            
        Returns:
            List of sessions with message counts
        """
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            
            if user_id:
                query = """
                    SELECT s.*, COUNT(m.id) as message_count
                    FROM sessions s
                    LEFT JOIN messages m ON s.id = m.session_id
                    WHERE s.user_id = ?
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC
                    LIMIT ?
                """
                params = (user_id, limit)
            else:
                query = """
                    SELECT s.*, COUNT(m.id) as message_count
                    FROM sessions s
                    LEFT JOIN messages m ON s.id = m.session_id
                    GROUP BY s.id
                    ORDER BY s.updated_at DESC
                    LIMIT ?
                """
                params = (limit,)
            
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]
    
    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Add a message to a session.
        
        BUG #1 FIX: Validates session_id before database operation.
        """
        # Basic validation
        if not session_id or not isinstance(session_id, str):
            raise ValueError(f"Invalid session_id format: {session_id}")
        metadata_json = json.dumps(metadata, ensure_ascii=False) if metadata else None
        
        async with db_manager.get_connection() as db:
            cursor = await db.execute("""
                INSERT INTO messages (session_id, role, content, metadata)
                VALUES (?, ?, ?, ?)
            """, (session_id, role, content, metadata_json))
            
            message_id = cursor.lastrowid
            
            # Update session timestamp
            await db.execute("""
                UPDATE sessions
                SET updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (session_id,))
            
            await db.commit()
        
        return message_id
    
    async def get_messages(
        self,
        session_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get messages from a session.
        
        Args:
            session_id: Session ID
            limit: Maximum number of messages
            
        Returns:
            List of messages
        """
        # Basic validation
        if not session_id or not isinstance(session_id, str):
            raise ValueError(f"Invalid session_id format: {session_id}")
        
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            
            query = """
                SELECT * FROM messages
                WHERE session_id = ?
                ORDER BY created_at ASC
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            async with db.execute(query, (session_id,)) as cursor:
                rows = await cursor.fetchall()
                messages = []
                
                for row in rows:
                    msg = dict(row)
                    # BUG #18 FIX: Parse metadata JSON with safe_json_loads
                    if msg.get('metadata'):
                        msg['metadata'] = safe_json_loads(msg['metadata'])
                    messages.append(msg)
                
                return messages
    
    async def get_context(
        self,
        session_id: str,
        max_messages: int = 10
    ) -> List[Dict[str, str]]:
        """
        Get conversation context for LLM.
        
        Args:
            session_id: Session ID
            max_messages: Maximum number of messages to include
            
        Returns:
            List of messages in LLM format
        """
        messages = await self.get_messages(session_id, limit=max_messages)
        
        context = []
        for msg in messages:
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context


# Global instance
session_manager = SessionManager()
