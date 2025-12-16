"""
Session management service.
"""
import uuid
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
import aiosqlite
from database import db_manager


class SessionManager:
    """Manages chat sessions and messages."""
    
    async def create_session(
        self,
        user_id: Optional[str] = None,
        title: str = "New Chat",
        language: str = "vi"
    ) -> str:
        """
        Create a new chat session.
        
        Args:
            user_id: User identifier
            title: Session title
            language: Session language
            
        Returns:
            Session ID
        """
        session_id = str(uuid.uuid4())
        
        async with db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO sessions (id, user_id, title, language)
                VALUES (?, ?, ?, ?)
            """, (session_id, user_id, title, language))
            await db.commit()
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session information.
        
        Args:
            session_id: Session ID
            
        Returns:
            Session data or None
        """
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
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
        
        Args:
            session_id: Session ID
            role: Message role (user/assistant)
            content: Message content
            metadata: Additional metadata
            
        Returns:
            Message ID
        """
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
                    # Parse metadata JSON
                    if msg.get('metadata'):
                        try:
                            msg['metadata'] = json.loads(msg['metadata'])
                        except:
                            msg['metadata'] = None
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
