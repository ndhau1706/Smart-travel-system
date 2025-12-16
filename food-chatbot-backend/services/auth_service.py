"""
Authentication service for user login/register and guest tracking.
"""
import hashlib
import uuid
from typing import Optional, Dict, Any
from database import db_manager


class AuthService:
    """Handle authentication and user management."""
    
    GUEST_MESSAGE_LIMIT = 10
    
    async def create_guest_user(self) -> str:
        """
        Create a guest user with limited message quota.
        
        Returns:
            guest_user_id: UUID for guest user
        """
        guest_id = f"guest-{uuid.uuid4().hex[:12]}"
        
        async with db_manager.get_connection() as db:
            await db.execute("""
                INSERT INTO users (id, username, is_guest)
                VALUES (?, ?, 1)
            """, (guest_id, f"Guest {guest_id[:8]}"))
            await db.commit()
        
        return guest_id
    
    async def register_user(self, email: str, username: str, password: str) -> Dict[str, Any]:
        """
        Register a new user account.
        
        Args:
            email: User email
            username: Display name
            password: Plain password (will be hashed)
            
        Returns:
            Dict with user info or error
        """
        # Check if email already exists
        async with db_manager.get_connection() as db:
            async with db.execute("""
                SELECT id FROM users WHERE email = ?
            """, (email,)) as cursor:
                existing = await cursor.fetchone()
                if existing:
                    return {"error": "Email already registered"}
            
            # Create user
            user_id = f"user-{uuid.uuid4().hex[:12]}"
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            await db.execute("""
                INSERT INTO users (id, email, username, password_hash, is_guest)
                VALUES (?, ?, ?, ?, 0)
            """, (user_id, email, username, password_hash))
            await db.commit()
        
        return {
            "user_id": user_id,
            "email": email,
            "username": username,
            "is_guest": False
        }
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login user with email and password.
        
        Returns:
            Dict with user info or error
        """
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        async with db_manager.get_connection() as db:
            async with db.execute("""
                SELECT id, email, username, is_guest
                FROM users
                WHERE email = ? AND password_hash = ?
            """, (email, password_hash)) as cursor:
                user = await cursor.fetchone()
                
                if not user:
                    return {"error": "Invalid email or password"}
                
                return {
                    "user_id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "is_guest": bool(user[3])
                }
    
    async def check_guest_limit(self, session_id: str) -> Dict[str, Any]:
        """
        Check if guest has exceeded message limit.
        
        Returns:
            Dict with can_send and messages_left
        """
        async with db_manager.get_connection() as db:
            # Check if this is a guest session
            async with db.execute("""
                SELECT s.user_id, u.is_guest, COALESCE(g.message_count, 0)
                FROM sessions s
                LEFT JOIN users u ON s.user_id = u.id
                LEFT JOIN guest_sessions g ON s.id = g.session_id
                WHERE s.id = ?
            """, (session_id,)) as cursor:
                result = await cursor.fetchone()
                
                if not result:
                    return {"can_send": False, "error": "Session not found"}
                
                user_id, is_guest, message_count = result
                
                # If not guest, no limit
                if not is_guest:
                    return {"can_send": True, "is_guest": False, "unlimited": True}
                
                # Check guest limit
                messages_left = self.GUEST_MESSAGE_LIMIT - message_count
                can_send = messages_left > 0
                
                return {
                    "can_send": can_send,
                    "is_guest": True,
                    "message_count": message_count,
                    "messages_left": messages_left,
                    "limit": self.GUEST_MESSAGE_LIMIT
                }
    
    async def increment_guest_message_count(self, session_id: str):
        """Increment message count for guest session."""
        async with db_manager.get_connection() as db:
            # Upsert guest_sessions
            await db.execute("""
                INSERT INTO guest_sessions (session_id, message_count)
                VALUES (?, 1)
                ON CONFLICT(session_id) DO UPDATE SET
                    message_count = message_count + 1
            """, (session_id,))
            await db.commit()
    
    async def get_user_info(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user information."""
        async with db_manager.get_connection() as db:
            async with db.execute("""
                SELECT id, email, username, is_guest, created_at
                FROM users
                WHERE id = ?
            """, (user_id,)) as cursor:
                user = await cursor.fetchone()
                
                if not user:
                    return None
                
                return {
                    "user_id": user[0],
                    "email": user[1],
                    "username": user[2],
                    "is_guest": bool(user[3]),
                    "created_at": user[4]
                }


# Global auth service instance
auth_service = AuthService()
