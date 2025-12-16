"""
Database schema initialization and management.
"""
import aiosqlite
from pathlib import Path
from typing import Optional
from config import settings


class DatabaseManager:
    """Manages database connections and schema initialization."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or settings.DATABASE_PATH
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
    
    async def init_db(self):
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Create restaurants table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS restaurants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    category TEXT,
                    rating REAL,
                    rating_count INTEGER,
                    price_level TEXT,
                    food_tags TEXT,
                    coordinates_lat REAL,
                    coordinates_lon REAL,
                    opening_hours TEXT,
                    comments TEXT,
                    location_summary TEXT,
                    type_summary TEXT,
                    contact_summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create users table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    username TEXT,
                    password_hash TEXT,
                    is_guest INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create guest_sessions table for tracking guest message limits
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guest_sessions (
                    session_id TEXT PRIMARY KEY,
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create sessions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    language TEXT DEFAULT 'vi',
                    message_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE SET NULL
                )
            """)
            
            # Create messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            """)
            
            # Create user_feedback table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS user_feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    message_id INTEGER,
                    restaurant_id INTEGER,
                    feedback_type TEXT,
                    rating INTEGER,
                    comment TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE,
                    FOREIGN KEY (message_id) REFERENCES messages (id) ON DELETE SET NULL,
                    FOREIGN KEY (restaurant_id) REFERENCES restaurants (id) ON DELETE SET NULL
                )
            """)
            
            # Create query_cache table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS query_cache (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_hash TEXT UNIQUE NOT NULL,
                    query_text TEXT NOT NULL,
                    response TEXT NOT NULL,
                    language TEXT,
                    hit_count INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL
                )
            """)
            
            # Create indexes
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_users_is_guest ON users(is_guest)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON user_feedback(session_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_feedback_restaurant_id ON user_feedback(restaurant_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_query_hash ON query_cache(query_hash)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_cache_expires_at ON query_cache(expires_at)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_rating ON restaurants(rating)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_restaurants_price_level ON restaurants(price_level)")
            
            await db.commit()
    
    def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection."""
        return aiosqlite.connect(self.db_path)
    
    async def clear_expired_cache(self):
        """Clear expired cache entries."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM query_cache
                WHERE expires_at < datetime('now')
            """)
            await db.commit()


# Global database manager instance
db_manager = DatabaseManager()
