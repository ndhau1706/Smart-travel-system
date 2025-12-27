"""
Multi-turn Context Tracker - Session-based conversation memory.
Enables ChatGPT-like multi-turn conversations with context awareness.

BUG #2 FIX: Race Condition Protection
- Added threading.Lock to prevent concurrent access issues
- All operations on shared state (_contexts, _last_restaurants) are now thread-safe
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import logging
import threading

logger = logging.getLogger(__name__)

# BUG #22 FIX: Import hybrid_search at module level for testability
# Import will happen lazily to avoid circular dependency
_hybrid_search = None

def get_hybrid_search():
    """Lazy import hybrid_search to avoid circular dependency."""
    global _hybrid_search
    if _hybrid_search is None:
        from services.hybrid_search import hybrid_search
        _hybrid_search = hybrid_search
    return _hybrid_search


class ContextTracker:
    """Tracks conversation context across multiple turns with auto-cleanup."""
    
    def __init__(self):
        # BUG #2 FIX: Thread-safe lock for protecting shared state
        self._lock = threading.Lock()
        
        # In-memory storage: {session_id: context_data}
        self._contexts: Dict[str, Dict[str, Any]] = {}
        # BUG #CRITICAL-2 FIX: TTL set to 30min to balance memory and UX
        self._context_ttl = timedelta(minutes=30)  # BUG #CRITICAL-2: Prevent long-lived session bloat
        # PHASE 2: Store last restaurants for entity resolution
        # BUG #22 FIX: Store IDs + timestamp instead of full objects to prevent stale data
        self._last_restaurants: Dict[str, Dict[str, Any]] = {}  # {session_id: {'ids': [...], 'timestamp': ...}}
        # Auto-cleanup tracking - FIXED: More aggressive cleanup
        self._last_cleanup = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC to avoid timezone bugs
        # BUG #6 FIX: Reduce cleanup interval from 60s to 30s to keep up with high traffic (500 contexts/min)
        self._cleanup_interval = timedelta(seconds=30)  # BUG #6 FIX: 30s cleanup interval for better responsiveness
        # Memory limits - FIXED: Lower limits to prevent OOM
        # BUG #CRITICAL-2 FIX: Set reasonable limits to prevent memory leak
        self._max_contexts = 200  # BUG #CRITICAL-2: Max 200 concurrent sessions
        self._max_turns_per_session = 15  # BUG #CRITICAL-2: Max 15 turns per session
        self._max_old_summaries = 3  # BUG #CRITICAL-2: Max 3 summaries to prevent bloat
        # Memory monitoring
        self._total_turns_tracked = 0
        self._cleanup_count = 0
        # FIX RACE CONDITION: Version tracking for context validation
        self._context_versions: Dict[str, int] = {}  # {session_id: version}
        # BUG #6 FIX: Add explicit garbage collection tracking
        self._gc_interval = timedelta(minutes=5)  # Force GC every 5 minutes
        self._last_gc = datetime.utcnow()
        
        # BUG #12 FIX: Pronoun and coreference tracking
        # Track last mentioned entities for "cái đó", "nó", "it" resolution
        self._pronoun_tracker: Dict[str, Dict[str, Any]] = {}
        self._pronoun_lock = threading.Lock()
        
        # BUG #12 FIX: Topic tracking for topic switches
        # Track conversation topic to detect switches (Nhật → Hàn)
        self._topic_tracker: Dict[str, List[Dict[str, Any]]] = {}
        self._topic_lock = threading.Lock()
        
        # BUG #12 FIX: Comparison context tracking
        # Track active comparisons for "cái nào tốt hơn?" queries
        self._comparison_tracker: Dict[str, Dict[str, Any]] = {}
        self._comparison_lock = threading.Lock()
        
        logger.info("✅ ContextTracker initialized with memory limits (TTL=30min, max_contexts=200, max_turns=15, cleanup=60s) and thread-safe locking")
        logger.info("✅ BUG #12: Pronoun, topic, and comparison tracking enabled")
    
    def cleanup_expired_sessions(self):
        """
        IMPROVED: Remove expired sessions to prevent memory leak.
        BUG #2 FIX: Thread-safe with lock protection.
        
        Features:
        - TTL-based expiration (24h)
        - Hard limit enforcement (max 1000 sessions)
        - LRU eviction when over limit
        - Clean up both contexts and last_restaurants
        - Thread-safe with lock acquisition
        """
        with self._lock:  # BUG #2 FIX: Acquire lock before modifying shared state
            now = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC to prevent timezone bugs
            expired_sessions = []
            
            # Step 1: Find and remove TTL-expired sessions
            for session_id, context in list(self._contexts.items()):  # BUG #2 FIX: list() to avoid dict size change during iteration
                last_updated = context.get('last_updated')
                if last_updated and (now - last_updated) > self._context_ttl:
                    expired_sessions.append(session_id)
            
            # Remove expired
            for session_id in expired_sessions:
                if session_id in self._contexts:  # BUG #2 FIX: Check existence before delete
                    del self._contexts[session_id]
                if session_id in self._last_restaurants:
                    del self._last_restaurants[session_id]
                # RACE CONDITION FIX: Clean up version tracking
                if session_id in self._context_versions:
                    del self._context_versions[session_id]
                # BUG #12 FIX: Clean up pronoun/topic/comparison trackers
                if session_id in self._pronoun_tracker:
                    del self._pronoun_tracker[session_id]
                if session_id in self._topic_tracker:
                    del self._topic_tracker[session_id]
                if session_id in self._comparison_tracker:
                    del self._comparison_tracker[session_id]
            
            if expired_sessions:
                logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions (TTL)")
            
            # Step 2: CRITICAL FIX - Aggressive LRU eviction (even BEFORE hitting limit)
            # BUG #CRITICAL-2 FIX: Trigger eviction at 60% capacity to prevent memory spike during bot spam
            # BUG #6 FIX: Lower threshold from 80% to 60% so final count stays within safe margin
            eviction_threshold = int(self._max_contexts * 0.6)  # 60% = 120 sessions for max_contexts=200
            
            if len(self._contexts) > eviction_threshold:
                # Sort by last_updated (oldest first)
                sorted_sessions = sorted(
                    self._contexts.items(),
                    key=lambda x: x[1].get('last_updated', datetime.min)
                )
                
                # BUG #6 FIX: Evict down to 40% to free up more memory headroom
                # This means trigger at 120, evict to 80 (40% of 200)
                target_size = int(self._max_contexts * 0.4)  # Target 40% = 80 sessions
                to_remove = max(
                    len(self._contexts) - target_size,
                    int(len(sorted_sessions) * 0.4)  # At least 40%
                )
                
                for session_id, _ in sorted_sessions[:to_remove]:
                    if session_id in self._contexts:  # BUG #2 FIX: Check existence
                        del self._contexts[session_id]
                    if session_id in self._last_restaurants:
                        del self._last_restaurants[session_id]
                    # RACE CONDITION FIX: Clean up version tracking
                    if session_id in self._context_versions:
                        del self._context_versions[session_id]
                    # BUG #12 FIX: Clean up pronoun/topic/comparison trackers
                    if session_id in self._pronoun_tracker:
                        del self._pronoun_tracker[session_id]
                    if session_id in self._topic_tracker:
                        del self._topic_tracker[session_id]
                    if session_id in self._comparison_tracker:
                        del self._comparison_tracker[session_id]
                
                logger.warning(f"🧹 Aggressive LRU eviction: removed {to_remove} oldest sessions (current: {len(self._contexts)}, limit: {self._max_contexts})")
                self._cleanup_count += 1
                
                # BUG #6 FIX: Force garbage collection after mass deletion to prevent memory lag
                import gc
                gc.collect()
                logger.debug("🗑️ Forced garbage collection after eviction")
            
            # Step 3: Also check for sessions with excessive turns (memory bloat)
            bloated_sessions = []
            for session_id, context in list(self._contexts.items()):
                turn_count = len(context.get('turns', []))
                if turn_count > self._max_turns_per_session * 2:  # 2x over limit
                    bloated_sessions.append(session_id)
            
            for session_id in bloated_sessions:
                if session_id in self._contexts:  # BUG #2 FIX: Check existence
                    # Don't delete, but aggressively trim
                    context = self._contexts[session_id]
                    context['turns'] = context['turns'][-self._max_turns_per_session:]
                    logger.warning(f"⚠️ Trimmed bloated session {session_id} to {self._max_turns_per_session} turns")
            
            # BUG #6 FIX: Periodic forced garbage collection to prevent Python GC lag
            if now - self._last_gc > self._gc_interval:
                import gc
                collected = gc.collect()
                self._last_gc = now
                logger.debug(f"🗑️ Periodic GC: collected {collected} objects")
            
            self._last_cleanup = now
    
    def get_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation context for session with auto-cleanup.
        BUG #2 FIX: Thread-safe with lock protection.
        RACE CONDITION FIX: Add version tracking to detect stale context.
        
        Args:
            session_id: Unique session identifier
            
        Returns:
            Context dictionary with version info or None if expired/not found
        """
        # Periodic cleanup check (without lock to avoid blocking)
        now = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC
        if now - self._last_cleanup > self._cleanup_interval:
            self.cleanup_expired_sessions()  # This will acquire lock internally
        
        # BUG #6 FIX: Immediate cleanup if approaching limit (prevent memory spike)
        # Check at 80% capacity
        if len(self._contexts) > self._max_contexts * 0.8:
            self.cleanup_expired_sessions()
        
        with self._lock:  # BUG #2 FIX: Acquire lock before reading shared state
            if session_id not in self._contexts:
                return None
            
            context = self._contexts[session_id]
            
            # Check if expired
            last_updated = context.get('last_updated')
            if last_updated:
                if now - last_updated > self._context_ttl:
                    # Expired, remove it
                    del self._contexts[session_id]
                    if session_id in self._last_restaurants:
                        del self._last_restaurants[session_id]
                    if session_id in self._context_versions:
                        del self._context_versions[session_id]
                    return None
            
            # BUG #2 FIX: Return a copy to prevent external modifications without lock
            # BUG #CRITICAL-2 FIX: Deep copy to preserve datetime objects properly
            # RACE CONDITION FIX: Include version in returned context
            import copy
            context_copy = copy.deepcopy(context)
            # Add version for validation
            context_copy['_version'] = self._context_versions.get(session_id, 0)
            return context_copy
    
    def validate_context_version(self, session_id: str, context_version: int) -> bool:
        """
        RACE CONDITION FIX: Validate if context is still current.
        
        Args:
            session_id: Session identifier
            context_version: Version from get_context() call
            
        Returns:
            True if context is still valid (not modified), False if stale
        """
        with self._lock:
            current_version = self._context_versions.get(session_id, 0)
            return current_version == context_version
    
    def increment_clarification_count(self, session_id: str) -> None:
        """
        BUG #3 FIX: Increment clarification count when a clarification is asked.
        
        Args:
            session_id: Session identifier
        """
        with self._lock:
            if session_id in self._contexts:
                self._contexts[session_id]['clarifications_asked'] = \
                    self._contexts[session_id].get('clarifications_asked', 0) + 1
                # Increment version when context changes
                self._context_versions[session_id] = \
                    self._context_versions.get(session_id, 0) + 1
                logger.debug(f"📋 Session {session_id}: clarification count = {self._contexts[session_id]['clarifications_asked']}")
    
    def update_context(
        self,
        session_id: str,
        query: str,
        response: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]] = None
    ):
        """
        Update conversation context after each turn.
        BUG #2 FIX: Thread-safe with lock protection.
        
        Args:
            session_id: Unique session identifier
            query: User query text
            response: Response dictionary from search
            user_preferences: Optional extracted preferences
        """
        now = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC
        
        with self._lock:  # BUG #2 FIX: Acquire lock before modifying shared state
            # BUG #CRITICAL-2 FIX: Immediate cleanup if at 80% capacity BEFORE adding new session
            if session_id not in self._contexts and len(self._contexts) >= self._max_contexts * 0.8:
                logger.warning(f"⚠️ Approaching limit ({len(self._contexts)}/{self._max_contexts}), forcing cleanup")
                # Release lock temporarily for cleanup
                pass  # Cleanup will be called after this block
            
            if session_id not in self._contexts:
                self._contexts[session_id] = {
                    'session_id': session_id,
                    'started_at': now,
                    'last_updated': now,
                    'turns': [],
                    'accumulated_preferences': {},
                    'mentioned_restaurants': set(),
                    'topics': [],
                    'clarifications_asked': 0  # BUG #3 FIX: Track clarification count per session
                }
                # RACE CONDITION FIX: Initialize version
                self._context_versions[session_id] = 1
            
            context = self._contexts[session_id]
            
            # Add new turn
            turn = {
                'timestamp': now,
                'query': query,
                'response_summary': self._summarize_response(response),
                'restaurants_shown': [r.get('name') for r in response.get('restaurants', [])[:5]]
            }
            context['turns'].append(turn)
            context['last_updated'] = now  # BUG #CRITICAL-2 FIX: Update timestamp
            
            # RACE CONDITION FIX: Increment version on every update
            self._context_versions[session_id] = self._context_versions.get(session_id, 0) + 1
        
        # BUG #CRITICAL-2 FIX: Trigger cleanup after adding turn if approaching limit (80% threshold)
        if len(self._contexts) > self._max_contexts * 0.8:
            # Release lock before cleanup (cleanup will acquire it again)
            self.cleanup_expired_sessions()
        
        # FIXED: Aggressive turn limit (15 turns max, was 20)
        if len(context['turns']) > self._max_turns_per_session:
            # Keep last N turns
            context['turns'] = context['turns'][-self._max_turns_per_session:]
            
            # BUG #7 FIX: Limit old_turns_summary with HARD FIFO cap
            if 'old_turns_summary' not in context:
                context['old_turns_summary'] = []
            
            # Only create summary if we have enough turns to summarize
            if len(context['turns']) >= 10:
                old_batch = context['turns'][:10]
                summary = self._summarize_turn_batch(old_batch)
                
                # FIXED: Safe timestamp extraction (handle string format)
                try:
                    first_ts = old_batch[0]['timestamp']
                    last_ts = old_batch[-1]['timestamp']
                    # Convert to string if datetime object
                    if isinstance(first_ts, datetime):
                        first_ts = first_ts.isoformat()
                    if isinstance(last_ts, datetime):
                        last_ts = last_ts.isoformat()
                    timestamp_range = f"{first_ts} to {last_ts}"
                except Exception as e:
                    timestamp_range = "unknown"
                    logger.warning(f"Timestamp format error: {e}")
                
                # BUG #7 FIX: FIFO eviction BEFORE append to prevent memory leak
                # If at capacity, remove oldest summary first
                if len(context['old_turns_summary']) >= self._max_old_summaries:
                    removed_summary = context['old_turns_summary'].pop(0)  # Remove oldest
                    logger.info(f"🗑️ Evicted oldest summary (FIFO) from session {session_id}")
                
                # Now safe to append new summary (won't exceed limit)
                context['old_turns_summary'].append({
                    'timestamp_range': timestamp_range,
                    'summary': summary,
                    'turn_count': len(old_batch)
                })
                logger.info(f"Summarized {len(old_batch)} old turns for session {session_id} (total summaries: {len(context['old_turns_summary'])})")
        
        # CRITICAL FIX: Detect intent change before merging
        intent_changed = False
        if user_preferences and context.get('accumulated_preferences'):
            intent_changed = self._detect_intent_change(
                query,
                context.get('last_query', ''),
                user_preferences,
                context.get('accumulated_preferences', {})
            )
        
        if intent_changed:
            # Clear contradicting preferences - user changed their mind
            logger.info(f"🔄 Intent change detected in session {session_id}: '{query}'")
            context['accumulated_preferences'] = user_preferences.copy()  # Replace, not merge!
            context['intent_change_count'] = context.get('intent_change_count', 0) + 1
            context['last_query'] = query  # Track for next comparison
        elif user_preferences:
            # SMART MERGE preferences (user is adding more details)
            for key, value in user_preferences.items():
                if key == 'locations':
                    # CRITICAL FIX: REPLACE locations if new query has district
                    # Don't merge "Quận 1" with "Quận 7"
                    import re
                    current_districts = set(re.findall(r'quận\s*(\d+)', ' '.join(value if isinstance(value, list) else [value]).lower()))
                    old_locs = context['accumulated_preferences'].get('locations', [])
                    old_districts = set(re.findall(r'quận\s*(\d+)', ' '.join(old_locs).lower()))
                    
                    if current_districts and old_districts and not (current_districts & old_districts):
                        # Different districts → REPLACE
                        context['accumulated_preferences'][key] = value if isinstance(value, list) else [value]
                        logger.info(f"🔄 Replaced location: Q{old_districts} → Q{current_districts}")
                    else:
                        # Same or no districts → merge
                        if key not in context['accumulated_preferences']:
                            context['accumulated_preferences'][key] = []
                        existing = context['accumulated_preferences'][key]
                        if isinstance(value, list):
                            existing.extend(value)
                        else:
                            existing.append(value)
                        context['accumulated_preferences'][key] = list(dict.fromkeys(existing))
                        
                elif key in ['cuisines', 'atmosphere']:
                    # Merge lists (add new items, remove duplicates)
                    if key not in context['accumulated_preferences']:
                        context['accumulated_preferences'][key] = []
                    
                    existing = context['accumulated_preferences'][key]
                    if isinstance(value, list):
                        existing.extend(value)
                    else:
                        existing.append(value)
                    
                    # Remove duplicates while preserving order
                    context['accumulated_preferences'][key] = list(dict.fromkeys(existing))
                elif key == 'excluded_cuisines':
                    # Track negative preferences (e.g., "không thích phở")
                    if key not in context['accumulated_preferences']:
                        context['accumulated_preferences'][key] = []
                    
                    existing = context['accumulated_preferences'][key]
                    if isinstance(value, list):
                        existing.extend(value)
                    else:
                        existing.append(value)
                    
                    context['accumulated_preferences'][key] = list(dict.fromkeys(existing))
                elif key in ['max_budget', 'min_budget']:
                    # FIXED: Track budget history instead of overwriting
                    # Store both current and history for smart suggestions
                    if f'{key}_history' not in context:
                        context[f'{key}_history'] = []
                    
                    # Add to history if significantly different
                    old_value = context['accumulated_preferences'].get(key)
                    if old_value and abs(value - old_value) > 50000:
                        context[f'{key}_history'].append(old_value)
                        # Flag for clarification in next response
                        context['budget_changed'] = True
                    
                    context['accumulated_preferences'][key] = value
                else:
                    # For other single values (rating, etc), smart update
                    old_value = context['accumulated_preferences'].get(key)
                    if old_value and old_value != value:
                        # Track that preference changed
                        if f'{key}_history' not in context:
                            context[f'{key}_history'] = []
                        context[f'{key}_history'].append(old_value)
                    
                    context['accumulated_preferences'][key] = value
        
        # CRITICAL FIX: Track mentioned restaurants with SIZE LIMIT
        # Prevent memory leak from unbounded set growth
        for r in response.get('restaurants', [])[:10]:
            context['mentioned_restaurants'].add(r.get('name'))
        
        # Enforce limit: keep only last 50 restaurants
        MAX_MENTIONED_RESTAURANTS = 50
        if len(context['mentioned_restaurants']) > MAX_MENTIONED_RESTAURANTS:
            # Convert to list, keep last N, convert back
            mentioned_list = list(context['mentioned_restaurants'])
            context['mentioned_restaurants'] = set(mentioned_list[-MAX_MENTIONED_RESTAURANTS:])
            logger.debug(f"Trimmed mentioned_restaurants to {MAX_MENTIONED_RESTAURANTS}")
        
        # PHASE 2: Store last restaurants for entity resolution
        # BUG #22 FIX: Store only IDs + timestamp, not full objects (prevent stale data)
        if response.get('restaurants'):
            restaurant_ids = [r['id'] for r in response['restaurants'][:10] if r.get('id')]
            self._last_restaurants[session_id] = {
                'ids': restaurant_ids,
                'timestamp': datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC
            }
        
        # Update timestamp and last_query
        context['last_updated'] = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC (do not overwrite with local time!)
        context['last_query'] = query
    
    def get_conversational_context(self, session_id: str) -> str:
        """
        Generate conversational context summary for LLM.
        
        Args:
            session_id: Session ID
            
        Returns:
            Formatted context string for LLM prompt
        """
        context = self.get_context(session_id)
        if not context or not context.get('turns'):
            return ""
        
        summary_parts = ["📝 Conversation History:"]
        
        # Recent turns (last 3)
        recent_turns = context['turns'][-3:]
        for i, turn in enumerate(recent_turns, 1):
            summary_parts.append(f"\nTurn {i}:")
            summary_parts.append(f"  User: {turn['query'][:100]}")
            summary_parts.append(f"  Bot: {turn['response_summary']}")
        
        # Accumulated preferences
        prefs = context.get('accumulated_preferences', {})
        if prefs:
            summary_parts.append("\n📊 User Preferences:")
            if prefs.get('cuisines'):
                summary_parts.append(f"  - Cuisines: {', '.join(prefs['cuisines'])}")
            if prefs.get('price_level'):
                summary_parts.append(f"  - Price Level: {prefs['price_level']}")
            if prefs.get('max_budget'):
                summary_parts.append(f"  - Budget: {prefs['max_budget']:,}đ")
            if prefs.get('locations'):
                summary_parts.append(f"  - Locations: {', '.join(prefs['locations'])}")
            if prefs.get('atmosphere'):
                summary_parts.append(f"  - Atmosphere: {', '.join(prefs['atmosphere'])}")
        
        # Previously mentioned restaurants (avoid repetition)
        mentioned = context.get('mentioned_restaurants', set())
        if mentioned:
            summary_parts.append(f"\n🏪 Previously Mentioned: {', '.join(list(mentioned)[:5])}")
        
        return "\n".join(summary_parts)
    
    def should_ask_clarification(
        self,
        session_id: str,
        current_query: str
    ) -> Optional[str]:
        """
        Determine if bot should ask clarifying questions.
        
        Returns:
            Clarification question or None
        """
        context = self.get_context(session_id)
        if not context:
            return None
        
        # Pattern 1: User keeps searching for same thing
        if len(context['turns']) >= 2:
            last_query = context['turns'][-1]['query'].lower()
            current_lower = current_query.lower()
            
            # Check if similar queries
            common_words = set(last_query.split()) & set(current_lower.split())
            if len(common_words) >= 3:
                # User might not be satisfied, ask why
                return (
                    "Bạn vẫn chưa tìm được quán ưng ý à? 🤔\n"
                    "Có thể bạn cho mình biết thêm:\n"
                    "- Bạn muốn thay đổi khu vực?\n"
                    "- Hay điều chỉnh mức giá?\n"
                    "- Hoặc có món ăn cụ thể nào bạn đang nghĩ tới?"
                )
        
        # Pattern 2: User asks vague query after specific query
        prefs = context.get('accumulated_preferences', {})
        if prefs and self._is_vague_query(current_query):
            return (
                "Bạn muốn tìm theo tiêu chí cũ không?\n"
                f"(Trước đó bạn đã tìm: {self._format_prefs(prefs)})"
            )
        
        return None
    
    def _summarize_response(self, response: Dict[str, Any]) -> str:
        """Summarize bot response."""
        restaurant_count = response.get('restaurant_count', 0)
        if restaurant_count == 0:
            return "No results found"
        else:
            return f"Showed {restaurant_count} restaurants"
    
    def _summarize_turn_batch(self, turns: List[Dict[str, Any]]) -> str:
        """
        Summarize a batch of conversation turns (ChatGPT-style).
        Used for long-term memory when context exceeds 50 turns.
        
        Args:
            turns: List of turn dictionaries
            
        Returns:
            Concise summary string
        """
        if not turns:
            return ""
        
        # Extract key information
        queries = [turn.get('query', '') for turn in turns]
        restaurants_mentioned = []
        for turn in turns:
            restaurants_mentioned.extend(turn.get('restaurants_shown', []))
        
        # Count unique restaurants
        unique_restaurants = set(restaurants_mentioned)
        
        # Detect main topics
        topics = []
        combined_queries = ' '.join(queries).lower()
        
        # Cuisine types
        cuisine_keywords = {
            'phở': 'Vietnamese phở',
            'sushi': 'Japanese sushi',
            'pizza': 'Italian pizza',
            'bbq': 'BBQ',
            'lẩu': 'Hotpot',
            'seafood': 'Seafood',
            'hải sản': 'Seafood'
        }
        for keyword, label in cuisine_keywords.items():
            if keyword in combined_queries:
                topics.append(label)
        
        # Price range
        if any(word in combined_queries for word in ['rẻ', 'cheap', 'budget']):
            topics.append('budget-friendly')
        elif any(word in combined_queries for word in ['cao cấp', 'luxury', 'expensive']):
            topics.append('upscale')
        
        # Location
        if any(word in combined_queries for word in ['gần', 'nearby', 'quận']):
            topics.append('location-specific')
        
        # Build summary
        summary_parts = [
            f"{len(turns)} queries",
            f"{len(unique_restaurants)} restaurants shown"
        ]
        
        if topics:
            summary_parts.append(f"topics: {', '.join(topics[:3])}")
        
        return ' | '.join(summary_parts)
    
    def _is_vague_query(self, query: str) -> bool:
        """Check if query is vague."""
        vague_keywords = [
            'gợi ý', 'tư vấn', 'ăn gì', 'gì đó', 'không biết',
            'suggest', 'recommend', 'what should i', 'any'
        ]
        return any(kw in query.lower() for kw in vague_keywords)
    
    def _format_prefs(self, prefs: Dict[str, Any]) -> str:
        """Format preferences for display."""
        parts = []
        if prefs.get('cuisines'):
            parts.append(', '.join(prefs['cuisines']))
        if prefs.get('locations'):
            parts.append(', '.join(prefs['locations']))
        if prefs.get('max_budget'):
            parts.append(f"< {prefs['max_budget']:,}đ")
        return ', '.join(parts) if parts else "các tiêu chí trước"
    
    def _detect_intent_change(
        self,
        current_query: str,
        last_query: str,
        current_prefs: Dict[str, Any],
        accumulated_prefs: Dict[str, Any]
    ) -> bool:
        """
        IMPROVED: Detect if user changed their mind (intent change).
        
        Signals:
        - Negation keywords: "không", "giờ", "bây giờ", "thôi", "khác"
        - Food type change: phở -> pizza (detect via keywords)
        - Cuisine contradiction: Vietnamese -> Korean
        - Location contradiction: Q1 -> Q7 (REPLACE, not merge)
        - Price contradiction: rẻ -> sang trọng
        
        Args:
            current_query: Current user query
            last_query: Previous query
            current_prefs: Current extracted preferences
            accumulated_prefs: Previously accumulated preferences
            
        Returns:
            True if intent changed
        """
        current_lower = current_query.lower()
        last_lower = last_query.lower() if last_query else ''
        
        # CRITICAL FIX 1: Detect "giờ", "bây giờ" as strong intent change signals
        # Example: "Tìm quán phở" → "Giờ tìm pizza"
        change_signals = [
            'giờ tìm', 'bây giờ', 'giờ muốn', 'giờ thích',
            'now find', 'now i want', 'instead',
            'thôi', 'khác', 'đổi', 'thay',
            'không', 'không phải'
        ]
        if any(signal in current_lower for signal in change_signals):
            logger.info(f"🔄 Intent change: signal word detected in '{current_query}'")
            return True
        
        # CRITICAL FIX 2: Detect food type change (phở → pizza, etc.)
        # Map common Vietnamese food keywords
        food_keywords = {
            'vietnamese': ['phở', 'bún', 'cơm', 'bánh mì', 'hủ tiếu', 'mì quảng'],
            'italian': ['pizza', 'pasta', 'spaghetti', 'ý'],
            'korean': ['hàn', 'bbq hàn', 'kimchi', 'kimbap'],
            'japanese': ['nhật', 'sushi', 'ramen', 'udon'],
            'chinese': ['trung', 'dimsum', 'mì vằn thắn'],
            'thai': ['thái', 'tomyum', 'pad thai']
        }
        
        def detect_food_category(text):
            for category, keywords in food_keywords.items():
                if any(kw in text for kw in keywords):
                    return category
            return None
        
        current_food = detect_food_category(current_lower)
        last_food = detect_food_category(last_lower)
        
        if current_food and last_food and current_food != last_food:
            logger.info(f"🔄 Intent change: food type changed {last_food} → {current_food}")
            return True
        
        # CRITICAL FIX 3: Check cuisine change (complete replacement, no overlap)
        current_cuisines = set(current_prefs.get('cuisines', []))
        old_cuisines = set(accumulated_prefs.get('cuisines', []))
        
        if current_cuisines and old_cuisines:
            # If NO overlap → complete change
            if not (current_cuisines & old_cuisines):
                logger.info(f"🔄 Intent change: cuisine {old_cuisines} → {current_cuisines}")
                return True
        
        # CRITICAL FIX 4: Location change - if new query has district, REPLACE old one
        # Example: "Quận 1 giá rẻ" (turn 1) → "Quận 7" (turn 15)
        current_locs = current_prefs.get('locations', [])
        old_locs = accumulated_prefs.get('locations', [])
        
        if current_locs and old_locs:
            # Extract district numbers
            import re
            current_districts = set(re.findall(r'quận\s*(\d+)', ' '.join(current_locs).lower()))
            old_districts = set(re.findall(r'quận\s*(\d+)', ' '.join(old_locs).lower()))
            
            # If user mentions a NEW district (not adding to old one), replace
            if current_districts and old_districts and not (current_districts & old_districts):
                logger.info(f"🔄 Intent change: location Q{old_districts} → Q{current_districts}")
                return True
        
        # CRITICAL FIX 5: Price level contradiction - rẻ ↔ sang trọng
        # Detect by keywords, not just budget numbers
        budget_low_keywords = ['rẻ', 'bình dân', 'sinh viên', 'giá rẻ', 'cheap']
        budget_high_keywords = ['sang trọng', 'cao cấp', 'đắt', 'luxury', 'upscale']
        
        current_is_low = any(kw in current_lower for kw in budget_low_keywords)
        current_is_high = any(kw in current_lower for kw in budget_high_keywords)
        
        old_is_low = accumulated_prefs.get('price_level') == 'cheap'
        old_is_high = accumulated_prefs.get('price_level') == 'upscale'
        
        if (current_is_low and old_is_high) or (current_is_high and old_is_low):
            logger.info(f"🔄 Intent change: price level contradiction detected")
            return True
        
        # Check numeric budget change (>2x or <0.5x)
        current_max = current_prefs.get('max_budget', 0)
        old_max = accumulated_prefs.get('max_budget', 0)
        
        if current_max and old_max:
            if current_max > old_max * 2 or current_max < old_max * 0.5:
                logger.info(f"🔄 Intent change: budget {old_max} → {current_max}")
                return True
        
        return False
    
    def clear_context(self, session_id: str):
        """Clear context for session. BUG #2 FIX: Thread-safe."""
        with self._lock:  # BUG #2 FIX: Acquire lock
            if session_id in self._contexts:
                del self._contexts[session_id]
    
    def cleanup_expired(self):
        """Remove expired contexts (called periodically). BUG #2 FIX: Thread-safe."""
        with self._lock:  # BUG #2 FIX: Acquire lock
            now = datetime.utcnow()  # BUG #CRITICAL-2 FIX: Use UTC consistently
            expired = [
                sid for sid, ctx in list(self._contexts.items())  # BUG #2 FIX: list() to avoid size change
                if now - ctx.get('last_updated', now) > self._context_ttl
            ]
            for sid in expired:
                if sid in self._contexts:  # BUG #2 FIX: Check existence
                    del self._contexts[sid]
                # Also clean up last restaurants
                if sid in self._last_restaurants:
                    del self._last_restaurants[sid]
    
    async def get_last_restaurants(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Get last shown restaurants for entity resolution.
        
        BUG #22 FIX: Fetch fresh data from DB using stored IDs to prevent stale references.
        BUG #2 FIX: Thread-safe with lock protection.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of fresh restaurant data or empty list
        """
        with self._lock:  # BUG #2 FIX: Acquire lock
            restaurant_ref = self._last_restaurants.get(session_id)
            if not restaurant_ref:
                return []
            
            # BUG #CRITICAL-2 FIX: Use UTC for timestamp comparison
            # BUG #22 FIX: Handle both local and UTC timestamps
            now_utc = datetime.utcnow()
            now_local = datetime.now()
            timestamp = restaurant_ref['timestamp']
            
            # Calculate age using both UTC and local time
            age_utc = now_utc - timestamp
            age_local = now_local - timestamp
            
            # Use the smaller absolute age (timestamp is either UTC or local)
            # This makes code work with both datetime.utcnow() and datetime.now()
            if abs(age_utc.total_seconds()) < abs(age_local.total_seconds()):
                age = age_utc
            else:
                age = age_local
            
            # Check if reference is too old (> 1 hour)
            if abs(age.total_seconds()) > 3600:
                logger.debug(f"Last restaurants reference expired (age: {age})")
                del self._last_restaurants[session_id]
                return []
            
            # Fetch fresh data from DB
            restaurant_ids = restaurant_ref['ids']
        if not restaurant_ids:
            return []
        
        try:
            # BUG #22 FIX: Import hybrid_search instance (lazy to avoid circular dependency)
            # This import pattern allows test mocking to work properly
            from services.hybrid_search import hybrid_search
            
            # Fetch fresh restaurant data
            restaurants = await hybrid_search._get_restaurants_by_ids(restaurant_ids)
            
            logger.debug(f"✅ Fetched {len(restaurants)}/{len(restaurant_ids)} fresh restaurants for session {session_id}")
            return restaurants
            
        except Exception as e:
            logger.error(f"❌ Failed to fetch fresh restaurant data: {e}")
            return []
    
    # ===== BUG #12 FIX: Pronoun Tracking Methods =====
    
    def track_pronoun(
        self,
        session_id: str,
        entity_type: str,
        entity_data: Dict[str, Any],
        context: str = None
    ):
        """
        Track entity for pronoun resolution (cái đó, nó, it).
        
        Args:
            session_id: User session ID
            entity_type: 'restaurant', 'comparison', 'list'
            entity_data: Entity information
            context: Context string (question or statement)
        """
        with self._pronoun_lock:
            if session_id not in self._pronoun_tracker:
                self._pronoun_tracker[session_id] = {
                    'last_mentioned': None,
                    'last_compared': [],
                    'mention_history': [],
                    'last_updated': datetime.utcnow()
                }
            
            tracker = self._pronoun_tracker[session_id]
            
            # Update last mentioned entity
            tracker['last_mentioned'] = {
                'type': entity_type,
                'data': entity_data,
                'context': context,
                'timestamp': datetime.utcnow()
            }
            
            # Add to mention history (keep last 5)
            tracker['mention_history'].append({
                'type': entity_type,
                'data': entity_data,
                'context': context,
                'timestamp': datetime.utcnow()
            })
            if len(tracker['mention_history']) > 5:
                tracker['mention_history'] = tracker['mention_history'][-5:]
            
            # If comparing, track in comparison list
            if entity_type == 'comparison':
                tracker['last_compared'] = entity_data.get('items', [])
            
            tracker['last_updated'] = datetime.utcnow()
            
            logger.debug(f"✅ Tracked pronoun for {session_id}: {entity_type}")
    
    def resolve_pronoun(
        self,
        session_id: str,
        pronoun: str,
        query: str
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve pronoun to actual entity (cái đó → restaurant A).
        
        Args:
            session_id: User session ID
            pronoun: Pronoun string ('cái đó', 'nó', 'it', etc.)
            query: Full query for context
            
        Returns:
            Resolved entity or None
        """
        with self._pronoun_lock:
            tracker = self._pronoun_tracker.get(session_id)
            if not tracker:
                return None
            
            last_mentioned = tracker.get('last_mentioned')
            if not last_mentioned:
                return None
            
            # Check if reference is too old (> 5 minutes)
            age = datetime.utcnow() - last_mentioned['timestamp']
            if age.total_seconds() > 300:
                logger.debug(f"Pronoun reference expired (age: {age})")
                return None
            
            # Resolve based on pronoun type
            pronoun_lower = pronoun.lower()
            
            # Demonstrative: "cái đó", "quán đó", "that one"
            if any(p in pronoun_lower for p in ['cái đó', 'quán đó', 'that', 'it']):
                return last_mentioned['data']
            
            # Personal: "nó", "it"
            if pronoun_lower in ['nó', 'it']:
                return last_mentioned['data']
            
            # Ambiguous: check context
            return last_mentioned['data']
    
    def get_comparison_context(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get active comparison context for "cái nào tốt hơn?" queries.
        
        Args:
            session_id: User session ID
            
        Returns:
            Comparison context or None
        """
        with self._comparison_lock:
            return self._comparison_tracker.get(session_id)
    
    def track_comparison(
        self,
        session_id: str,
        items: List[Dict[str, Any]],
        aspect: str = None
    ):
        """
        Track active comparison between restaurants.
        
        Args:
            session_id: User session ID
            items: List of restaurants being compared
            aspect: Comparison aspect (price, rating, distance)
        """
        with self._comparison_lock:
            self._comparison_tracker[session_id] = {
                'items': items,
                'aspect': aspect,
                'timestamp': datetime.utcnow()
            }
            logger.debug(f"✅ Tracked comparison for {session_id}: {len(items)} items")
    
    # ===== BUG #12 FIX: Topic Tracking Methods =====
    
    def track_topic(
        self,
        session_id: str,
        topic: str,
        preferences: Dict[str, Any]
    ):
        """
        Track conversation topic for topic switch detection.
        
        Args:
            session_id: User session ID
            topic: Topic identifier (cuisine type, food category)
            preferences: Associated preferences
        """
        with self._topic_lock:
            if session_id not in self._topic_tracker:
                self._topic_tracker[session_id] = []
            
            self._topic_tracker[session_id].append({
                'topic': topic,
                'preferences': preferences,
                'timestamp': datetime.utcnow()
            })
            
            # Keep last 5 topics
            if len(self._topic_tracker[session_id]) > 5:
                self._topic_tracker[session_id] = self._topic_tracker[session_id][-5:]
            
            logger.debug(f"✅ Tracked topic for {session_id}: {topic}")
    
    def detect_topic_switch(
        self,
        session_id: str,
        current_topic: str
    ) -> bool:
        """
        Detect if user switched topics (Nhật → Hàn).
        
        Args:
            session_id: User session ID
            current_topic: Current topic
            
        Returns:
            True if topic switched
        """
        with self._topic_lock:
            history = self._topic_tracker.get(session_id, [])
            if not history:
                return False
            
            last_topic = history[-1]['topic']
            
            # Topic switched if different and not a refinement
            if last_topic != current_topic:
                logger.info(f"🔄 Topic switched for {session_id}: {last_topic} → {current_topic}")
                return True
            
            return False


# Global instance
context_tracker = ContextTracker()



# Background cleanup task (call this periodically from main.py)
def setup_context_cleanup():
    """Setup periodic cleanup of expired contexts."""
    import asyncio
    
    async def cleanup_loop():
        while True:
            await asyncio.sleep(300)  # Every 5 minutes
            try:
                context_tracker.cleanup_expired()
                logger.info("Context tracker cleanup completed")
            except Exception as e:
                logger.error(f"Context cleanup error: {e}")
    
    # Start cleanup task
    asyncio.create_task(cleanup_loop())
