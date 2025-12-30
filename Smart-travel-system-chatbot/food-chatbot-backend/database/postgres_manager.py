"""
PostgreSQL Database Manager for Long-term Memory
Handles persistent user profiles, conversation history, and learned preferences.
"""
import asyncpg
from typing import Optional, Dict, List, Any
from datetime import datetime, timedelta
import json
from config import settings


class PostgresManager:
    """Manages PostgreSQL connections for long-term storage."""
    
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None
        self.db_url = getattr(settings, 'POSTGRES_URL', 
                              'postgresql://chatbot:chatbot@localhost:5432/chatbot_db')
    
    async def init_pool(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.db_url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )
        await self.init_schema()
    
    async def close_pool(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
    
    async def init_schema(self):
        """Create tables for long-term memory."""
        async with self.pool.acquire() as conn:
            # User profiles with extended information
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_profiles (
                    user_id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    username TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_searches INTEGER DEFAULT 0,
                    successful_searches INTEGER DEFAULT 0,
                    preferences JSONB DEFAULT '{}',
                    learned_patterns JSONB DEFAULT '{}',
                    metadata JSONB DEFAULT '{}'
                )
            """)
            
            # Conversation history with full context
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS conversation_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    intent TEXT,
                    entities JSONB,
                    restaurants_shown JSONB,
                    user_feedback TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
                )
            """)
            
            # Search history with detailed parameters
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS search_history (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    query TEXT NOT NULL,
                    intent TEXT,
                    cuisines TEXT[],
                    price_range TEXT,
                    max_budget INTEGER,
                    max_distance REAL,
                    atmosphere TEXT[],
                    user_location JSONB,
                    results_count INTEGER,
                    clicked_restaurants INTEGER[],
                    time_spent_seconds INTEGER,
                    was_successful BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
                )
            """)
            
            # Restaurant interactions (clicks, views, implicit signals)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS restaurant_interactions (
                    id SERIAL PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    restaurant_id INTEGER NOT NULL,
                    interaction_type TEXT NOT NULL,
                    context JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
                )
            """)
            
            # User preferences (explicit and learned)
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS user_preferences (
                    user_id TEXT PRIMARY KEY,
                    favorite_cuisines TEXT[],
                    disliked_cuisines TEXT[],
                    preferred_price_range TEXT,
                    max_typical_distance REAL,
                    min_rating REAL,
                    favorite_atmospheres TEXT[],
                    dietary_restrictions TEXT[],
                    cuisine_weights JSONB DEFAULT '{}',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES user_profiles(user_id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes for fast queries
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_user_session 
                ON conversation_history(user_id, session_id, created_at DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_search_user_created 
                ON search_history(user_id, created_at DESC)
            """)
            await conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_interactions_user_restaurant 
                ON restaurant_interactions(user_id, restaurant_id, created_at DESC)
            """)
    
    # ==================== User Profile Methods ====================
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with full history."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM user_profiles WHERE user_id = $1
            """, user_id)
            
            if not row:
                return None
            
            profile = dict(row)
            
            # Get preferences
            prefs = await conn.fetchrow("""
                SELECT * FROM user_preferences WHERE user_id = $1
            """, user_id)
            
            if prefs:
                profile['preferences'] = dict(prefs)
            
            return profile
    
    async def create_or_update_profile(self, user_id: str, email: Optional[str] = None,
                                      username: Optional[str] = None) -> Dict[str, Any]:
        """Create or update user profile."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO user_profiles (user_id, email, username, last_active)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (user_id) DO UPDATE
                SET last_active = $4, email = COALESCE($2, user_profiles.email),
                    username = COALESCE($3, user_profiles.username)
            """, user_id, email, username, datetime.now())
            
            # Initialize preferences if new user
            await conn.execute("""
                INSERT INTO user_preferences (user_id)
                VALUES ($1)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id)
            
            return await self.get_user_profile(user_id)
    
    async def update_user_activity(self, user_id: str, search_success: bool = False):
        """Update user activity counters."""
        async with self.pool.acquire() as conn:
            if search_success:
                await conn.execute("""
                    UPDATE user_profiles
                    SET total_searches = total_searches + 1,
                        successful_searches = successful_searches + 1,
                        last_active = $2
                    WHERE user_id = $1
                """, user_id, datetime.now())
            else:
                await conn.execute("""
                    UPDATE user_profiles
                    SET total_searches = total_searches + 1,
                        last_active = $2
                    WHERE user_id = $1
                """, user_id, datetime.now())
    
    # ==================== Conversation History Methods ====================
    
    async def save_conversation_turn(self, user_id: str, session_id: str,
                                    role: str, content: str,
                                    intent: Optional[str] = None,
                                    entities: Optional[Dict] = None,
                                    restaurants_shown: Optional[List[int]] = None,
                                    user_feedback: Optional[str] = None):
        """Save a conversation turn."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO conversation_history 
                (user_id, session_id, role, content, intent, entities, 
                 restaurants_shown, user_feedback)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """, user_id, session_id, role, content, intent,
            json.dumps(entities) if entities else None,
            json.dumps(restaurants_shown) if restaurants_shown else None,
            user_feedback)
    
    async def get_conversation_history(self, user_id: str, session_id: str,
                                      limit: int = 50) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT * FROM conversation_history
                WHERE user_id = $1 AND session_id = $2
                ORDER BY created_at DESC
                LIMIT $3
            """, user_id, session_id, limit)
            
            return [dict(row) for row in reversed(rows)]
    
    async def get_user_all_conversations(self, user_id: str, days: int = 30,
                                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get all recent conversations for a user."""
        async with self.pool.acquire() as conn:
            cutoff = datetime.now() - timedelta(days=days)
            rows = await conn.fetch("""
                SELECT * FROM conversation_history
                WHERE user_id = $1 AND created_at > $2
                ORDER BY created_at DESC
                LIMIT $3
            """, user_id, cutoff, limit)
            
            return [dict(row) for row in rows]
    
    # ==================== Search History Methods ====================
    
    async def save_search(self, user_id: str, session_id: str, query: str,
                         intent: Optional[str] = None,
                         cuisines: Optional[List[str]] = None,
                         price_range: Optional[str] = None,
                         max_budget: Optional[int] = None,
                         max_distance: Optional[float] = None,
                         atmosphere: Optional[List[str]] = None,
                         user_location: Optional[Dict] = None,
                         results_count: int = 0,
                         clicked_restaurants: Optional[List[int]] = None,
                         time_spent: Optional[int] = None,
                         was_successful: bool = False):
        """Save a search record."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO search_history
                (user_id, session_id, query, intent, cuisines, price_range,
                 max_budget, max_distance, atmosphere, user_location,
                 results_count, clicked_restaurants, time_spent_seconds, was_successful)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
            """, user_id, session_id, query, intent, cuisines, price_range,
            max_budget, max_distance, atmosphere,
            json.dumps(user_location) if user_location else None,
            results_count, clicked_restaurants, time_spent, was_successful)
    
    async def get_search_history(self, user_id: str, days: int = 90,
                                limit: int = 100) -> List[Dict[str, Any]]:
        """Get user's search history."""
        async with self.pool.acquire() as conn:
            cutoff = datetime.now() - timedelta(days=days)
            rows = await conn.fetch("""
                SELECT * FROM search_history
                WHERE user_id = $1 AND created_at > $2
                ORDER BY created_at DESC
                LIMIT $3
            """, user_id, cutoff, limit)
            
            return [dict(row) for row in rows]
    
    # ==================== Restaurant Interactions Methods ====================
    
    async def save_interaction(self, user_id: str, restaurant_id: int,
                              interaction_type: str, context: Optional[Dict] = None):
        """Save a restaurant interaction (click, view, etc)."""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO restaurant_interactions
                (user_id, restaurant_id, interaction_type, context)
                VALUES ($1, $2, $3, $4)
            """, user_id, restaurant_id, interaction_type,
            json.dumps(context) if context else None)
    
    async def get_user_interactions(self, user_id: str, days: int = 180) -> List[Dict[str, Any]]:
        """Get user's restaurant interactions."""
        async with self.pool.acquire() as conn:
            cutoff = datetime.now() - timedelta(days=days)
            rows = await conn.fetch("""
                SELECT * FROM restaurant_interactions
                WHERE user_id = $1 AND created_at > $2
                ORDER BY created_at DESC
            """, user_id, cutoff)
            
            return [dict(row) for row in rows]
    
    async def get_user_favorite_restaurants(self, user_id: str, limit: int = 20) -> List[int]:
        """Get user's most interacted restaurants."""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT restaurant_id, COUNT(*) as interaction_count
                FROM restaurant_interactions
                WHERE user_id = $1
                GROUP BY restaurant_id
                ORDER BY interaction_count DESC
                LIMIT $2
            """, user_id, limit)
            
            return [row['restaurant_id'] for row in rows]
    
    # ==================== Preferences Methods ====================
    
    async def update_preferences(self, user_id: str,
                                favorite_cuisines: Optional[List[str]] = None,
                                disliked_cuisines: Optional[List[str]] = None,
                                preferred_price_range: Optional[str] = None,
                                max_typical_distance: Optional[float] = None,
                                min_rating: Optional[float] = None,
                                favorite_atmospheres: Optional[List[str]] = None,
                                dietary_restrictions: Optional[List[str]] = None,
                                cuisine_weights: Optional[Dict[str, float]] = None):
        """Update user preferences."""
        async with self.pool.acquire() as conn:
            updates = []
            params = [user_id]
            param_idx = 2
            
            if favorite_cuisines is not None:
                updates.append(f"favorite_cuisines = ${param_idx}")
                params.append(favorite_cuisines)
                param_idx += 1
            
            if disliked_cuisines is not None:
                updates.append(f"disliked_cuisines = ${param_idx}")
                params.append(disliked_cuisines)
                param_idx += 1
            
            if preferred_price_range is not None:
                updates.append(f"preferred_price_range = ${param_idx}")
                params.append(preferred_price_range)
                param_idx += 1
            
            if max_typical_distance is not None:
                updates.append(f"max_typical_distance = ${param_idx}")
                params.append(max_typical_distance)
                param_idx += 1
            
            if min_rating is not None:
                updates.append(f"min_rating = ${param_idx}")
                params.append(min_rating)
                param_idx += 1
            
            if favorite_atmospheres is not None:
                updates.append(f"favorite_atmospheres = ${param_idx}")
                params.append(favorite_atmospheres)
                param_idx += 1
            
            if dietary_restrictions is not None:
                updates.append(f"dietary_restrictions = ${param_idx}")
                params.append(dietary_restrictions)
                param_idx += 1
            
            if cuisine_weights is not None:
                updates.append(f"cuisine_weights = ${param_idx}")
                params.append(json.dumps(cuisine_weights))
                param_idx += 1
            
            if updates:
                updates.append(f"updated_at = ${param_idx}")
                params.append(datetime.now())
                
                query = f"""
                    UPDATE user_preferences
                    SET {', '.join(updates)}
                    WHERE user_id = $1
                """
                await conn.execute(query, *params)
    
    async def get_preferences(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user preferences."""
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                SELECT * FROM user_preferences WHERE user_id = $1
            """, user_id)
            
            return dict(row) if row else None
    
    # ==================== Analytics Methods ====================
    
    async def get_user_stats(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user statistics."""
        async with self.pool.acquire() as conn:
            # Basic stats
            profile = await conn.fetchrow("""
                SELECT total_searches, successful_searches, created_at
                FROM user_profiles WHERE user_id = $1
            """, user_id)
            
            # Top cuisines
            top_cuisines = await conn.fetch("""
                SELECT UNNEST(cuisines) as cuisine, COUNT(*) as count
                FROM search_history
                WHERE user_id = $1
                GROUP BY cuisine
                ORDER BY count DESC
                LIMIT 10
            """, user_id)
            
            # Average budget
            avg_budget = await conn.fetchval("""
                SELECT AVG(max_budget)
                FROM search_history
                WHERE user_id = $1 AND max_budget IS NOT NULL
            """, user_id)
            
            # Favorite restaurants
            fav_restaurants = await self.get_user_favorite_restaurants(user_id, 10)
            
            return {
                'total_searches': profile['total_searches'] if profile else 0,
                'successful_searches': profile['successful_searches'] if profile else 0,
                'member_since': profile['created_at'].isoformat() if profile else None,
                'top_cuisines': [{'cuisine': r['cuisine'], 'count': r['count']} 
                               for r in top_cuisines],
                'average_budget': float(avg_budget) if avg_budget else None,
                'favorite_restaurants': fav_restaurants
            }


# Global instance
postgres_manager = PostgresManager()
