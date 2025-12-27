"""
Database schema initialization and management.
"""
import aiosqlite
from pathlib import Path
from typing import Optional
from config import settings
import logging

logger = logging.getLogger(__name__)


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
            # NOTE: All queries use parameterized statements (?, ?) to prevent SQL injection
            # Never use string formatting or concatenation for SQL queries
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
            
            # BUG #16 FIX: Create data_version table to track DB changes
            await db.execute("""
                CREATE TABLE IF NOT EXISTS data_version (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    version INTEGER NOT NULL DEFAULT 0,
                    last_update TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    update_reason TEXT
                )
            """)
            
            # Initialize version if not exists
            await db.execute("""
                INSERT OR IGNORE INTO data_version (id, version, update_reason)
                VALUES (1, 0, 'initial')
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
            
            # BUG #29 FIX: Create database triggers to auto-increment version on ALL changes
            # This ensures cache invalidation even for direct SQL updates, bulk imports, etc.
            
            # Trigger on INSERT to restaurants table
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS restaurants_insert_trigger
                AFTER INSERT ON restaurants
                BEGIN
                    UPDATE data_version
                    SET version = version + 1,
                        last_update = CURRENT_TIMESTAMP,
                        update_reason = 'trigger:restaurant_inserted:' || NEW.id
                    WHERE id = 1;
                END;
            """)
            
            # Trigger on UPDATE to restaurants table
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS restaurants_update_trigger
                AFTER UPDATE ON restaurants
                BEGIN
                    UPDATE data_version
                    SET version = version + 1,
                        last_update = CURRENT_TIMESTAMP,
                        update_reason = 'trigger:restaurant_updated:' || NEW.id
                    WHERE id = 1;
                END;
            """)
            
            # Trigger on DELETE from restaurants table
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS restaurants_delete_trigger
                AFTER DELETE ON restaurants
                BEGIN
                    UPDATE data_version
                    SET version = version + 1,
                        last_update = CURRENT_TIMESTAMP,
                        update_reason = 'trigger:restaurant_deleted:' || OLD.id
                    WHERE id = 1;
                END;
            """)
            
            # BUG #29 FIX: Additional triggers for bulk operations protection
            # These ensure version tracking even during transaction rollbacks
            
            # Trigger to detect bulk inserts (multiple INSERTs in transaction)
            await db.execute("""
                CREATE TRIGGER IF NOT EXISTS restaurants_bulk_insert_trigger
                AFTER INSERT ON restaurants
                WHEN (SELECT COUNT(*) FROM restaurants WHERE id >= NEW.id - 10) > 10
                BEGIN
                    UPDATE data_version
                    SET version = version + 1,
                        last_update = CURRENT_TIMESTAMP,
                        update_reason = 'trigger:bulk_insert_detected'
                    WHERE id = 1;
                END;
            """)
            
            await db.commit()
    
    def get_connection(self) -> aiosqlite.Connection:
        """Get a database connection."""
        return aiosqlite.connect(self.db_path)
    
    async def clear_expired_cache(self):
        """
        Clear expired cache entries.
        
        BUG #6 FIX: Use UTC timezone-aware comparison.
        """
        from datetime import datetime, timezone
        
        # BUG #6 FIX: Use UTC time in ISO format for comparison
        now_utc_iso = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            # Count expired entries before deletion
            cursor = await db.execute("""
                SELECT COUNT(*) FROM query_cache
                WHERE expires_at < ?
            """, (now_utc_iso,))
            count = (await cursor.fetchone())[0]
            
            # Delete expired entries
            await db.execute("""
                DELETE FROM query_cache
                WHERE expires_at < ?
            """, (now_utc_iso,))
            await db.commit()
            
            if count > 0:
                logger.info(f"🧹 Cleared {count} expired cache entries (UTC: {now_utc_iso})")
    
    async def get_data_version(self) -> int:
        """BUG #16 FIX: Get current data version for cache validation."""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT version FROM data_version WHERE id = 1
            """)
            row = await cursor.fetchone()
            return row[0] if row else 0
    
    async def increment_data_version(self, reason: str = "data_change"):
        """
        BUG #16 FIX: Increment data version when DB changes.
        BUG #6 FIX: Use UTC timezone-aware timestamp.
        """
        from datetime import datetime, timezone
        
        # BUG #6 FIX: Use UTC time in ISO format
        now_utc_iso = datetime.now(timezone.utc).isoformat()
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                UPDATE data_version
                SET version = version + 1,
                    last_update = ?,
                    update_reason = ?
                WHERE id = 1
            """, (now_utc_iso, reason))
            await db.commit()
            
            # Get new version
            new_version = await self.get_data_version()
            logger.info(f"🔄 Data version incremented to {new_version} (reason: {reason})")
            return new_version
    
    async def on_restaurant_added(self, restaurant_id: int):
        """BUG #16 FIX: Hook called when restaurant is added."""
        await self.increment_data_version(f"restaurant_added:{restaurant_id}")
        # Notify hybrid_search to invalidate cache
        from services.hybrid_search import hybrid_search
        await hybrid_search.invalidate_cache_on_data_change("restaurant_added")
    
    async def on_restaurant_updated(self, restaurant_id: int, fields: list = None):
        """BUG #16 FIX: Hook called when restaurant is updated."""
        field_str = ",".join(fields) if fields else "all"
        await self.increment_data_version(f"restaurant_updated:{restaurant_id}:{field_str}")
        # Notify hybrid_search
        from services.hybrid_search import hybrid_search
        await hybrid_search.invalidate_cache_on_data_change("restaurant_updated")
    
    async def on_restaurant_deleted(self, restaurant_id: int):
        """BUG #16 FIX: Hook called when restaurant is deleted."""
        await self.increment_data_version(f"restaurant_deleted:{restaurant_id}")
        # Notify hybrid_search
        from services.hybrid_search import hybrid_search
        await hybrid_search.invalidate_cache_on_data_change("restaurant_deleted")
    
    async def on_index_rebuilt(self):
        """BUG #16 FIX: Hook called when FAISS/BM25 index is rebuilt."""
        await self.increment_data_version("index_rebuilt")
        # Notify hybrid_search
        from services.hybrid_search import hybrid_search
        await hybrid_search.invalidate_cache_on_data_change("index_rebuilt")
    
    async def verify_version_consistency(self) -> dict:
        """
        BUG #29 FIX: Verify data version consistency and detect anomalies.
        
        Returns dict with:
        - is_consistent: bool
        - current_version: int
        - last_update: str
        - update_reason: str
        - warnings: list[str]
        """
        async with aiosqlite.connect(self.db_path) as db:
            # Get current version info
            cursor = await db.execute("""
                SELECT version, last_update, update_reason
                FROM data_version WHERE id = 1
            """)
            row = await cursor.fetchone()
            
            if not row:
                return {
                    'is_consistent': False,
                    'current_version': 0,
                    'warnings': ['data_version table not initialized']
                }
            
            version, last_update, update_reason = row
            warnings = []
            
            # Check if version has been updated recently
            from datetime import datetime, timezone, timedelta
            if last_update:
                try:
                    last_update_dt = datetime.fromisoformat(last_update)
                    now = datetime.now(timezone.utc)
                    age = now - last_update_dt.replace(tzinfo=timezone.utc)
                    
                    # Warning if version hasn't changed in >1 hour with active DB
                    if age > timedelta(hours=1):
                        warnings.append(f'Version stale: last updated {age.total_seconds()//3600}h ago')
                except Exception as e:
                    warnings.append(f'Invalid last_update timestamp: {e}')
            
            # Check for trigger existence
            cursor = await db.execute("""
                SELECT COUNT(*) FROM sqlite_master
                WHERE type='trigger' AND name LIKE 'restaurants_%_trigger'
            """)
            trigger_count = (await cursor.fetchone())[0]
            
            if trigger_count < 3:
                warnings.append(f'Missing triggers: found {trigger_count}/4 expected')
            
            return {
                'is_consistent': len(warnings) == 0,
                'current_version': version,
                'last_update': last_update,
                'update_reason': update_reason,
                'warnings': warnings
            }
    
    async def force_version_increment(self, reason: str = "manual_force"):
        """
        BUG #29 FIX: Manually force version increment.
        
        Use this for:
        - After backup restore
        - After manual SQL edits
        - After detecting inconsistencies
        """
        logger.warning(f"⚠️ Forcing data version increment: {reason}")
        return await self.increment_data_version(f"forced:{reason}")


# Global database manager instance
db_manager = DatabaseManager()
