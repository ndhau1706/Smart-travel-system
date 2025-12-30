"""
Hybrid search combining FAISS semantic search and BM25 keyword search.
"""
from typing import List, Dict, Any, Tuple, Optional
import aiosqlite
import json
import logging
import math
import copy
from config import settings
from database import db_manager
from services.vector_store import vector_store
from services.bm25_search import bm25_search
from utils import extract_price_range, extract_location, normalize_text, restaurant_validator
# BUG #10 FIX: Import semantic validator to prevent hallucination
from utils.semantic_validator import semantic_validator

logger = logging.getLogger(__name__)

# Import learned ranker (lazy to avoid circular import)
_learned_ranker = None

def get_learned_ranker():
    global _learned_ranker
    if _learned_ranker is None:
        from services.learned_ranker import learned_ranker
        _learned_ranker = learned_ranker
    return _learned_ranker


class HybridSearch:
    """Combines semantic and keyword search with ranking - OPTIMIZED with caching."""
    
    def __init__(self):
        # BUG #20 FIX: Store references to search components for testing
        self.vector_store = vector_store
        self.bm25_search = bm25_search
        
        # Dynamic weights (adjusted per query)
        self.default_semantic_weight = settings.SEMANTIC_WEIGHT
        self.default_bm25_weight = settings.BM25_WEIGHT
        self._search_cache = {}  # In-memory cache for search results
        self._cache_ttl = 300  # 5 minutes TTL (default)
        # Cache statistics
        self._cache_hits = 0
        self._cache_misses = 0
        # BUG #16 FIX: Data version tracking for cache invalidation
        self._data_version = 0  # Auto-synced with DB
        self._last_version_check = 0
        # BUG #2 FIX: Very short TTL for dynamic data (price, rating, opening hours)
        self._dynamic_data_ttl = 15  # 15 seconds for price/rating/opening hours (was 60s)
        self._static_data_ttl = 60  # 60 seconds for static data (name, address)
        # FIXED: Add lock for thread-safe cache access
        import asyncio
        self._cache_lock = asyncio.Lock()
        # BUG #16 FIX: Flag to track if version sync is running
        self._version_sync_task = None
        # BUG #4 FIX: Track last DB version check timestamp for staleness detection
        self._last_db_check_time = 0
        # BUG #4 FIX: Event for immediate invalidation (webhook-style)
        self._invalidation_event = asyncio.Event()
        logger.info("✅ HybridSearch initialized with cache invalidation support")
    
    def _generate_cache_key(
        self,
        query: str,
        top_k: int,
        filters: Dict[str, Any] = None
    ) -> str:
        """
        Generate cache key for a search query.
        
        This is exposed for testing purposes to allow tests to properly
        inject cache entries with the correct key format.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Optional filters
            
        Returns:
            MD5 hash of cache key components
        """
        import hashlib
        import json
        
        cache_key_components = {
            'query': query,
            'top_k': top_k,
            'version': self._data_version
        }
        
        if filters:
            if 'user_location' in filters and filters['user_location']:
                from utils.location_utils import parse_location
                parsed = parse_location(filters['user_location'])
                
                if parsed is not None:
                    lat, lon = parsed
                    cache_key_components['location'] = f"{lat:.2f},{lon:.2f}"
            
            for key in ['max_budget', 'min_budget', 'locations', 'cuisines', 'min_rating']:
                if key in filters and filters[key]:
                    cache_key_components[key] = filters[key]
        
        cache_key_str = json.dumps(cache_key_components, sort_keys=True, default=str)
        return hashlib.md5(cache_key_str.encode()).hexdigest()
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search - OPTIMIZED with caching & parallel execution.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Additional filters (price, location, etc.)
            
        Returns:
            List of ranked restaurants
        """
        if top_k is None:
            top_k = settings.MAX_RESULTS
        
        # CRITICAL FIX: Generate stable cache key
        import time
        cache_key = self._generate_cache_key(query, top_k, filters)
        
        logger.debug(f"Cache key: {cache_key[:12]}... for query='{query[:30]}...'")
        
        # CRITICAL FIX: Check cache with version validation and dynamic TTL
        async with self._cache_lock:
            if cache_key in self._search_cache:
                cached_data = self._search_cache[cache_key]
                cached_results, created_time, last_accessed_time, cache_version, is_dynamic = cached_data
                
                # BUG #2 FIX: Determine TTL based on data type
                # Dynamic queries (price/rating/hours) get 15s TTL, static get 60s
                ttl = self._dynamic_data_ttl if is_dynamic else self._static_data_ttl
                
                # BUG #4 FIX: Multi-layer staleness validation
                current_time = time.time()
                cache_age = current_time - created_time
                is_expired = cache_age > ttl
                is_stale = cache_version != self._data_version
                
                # BUG #4 FIX: Additional timestamp-based staleness check
                # If DB was checked recently and cache is older, it's potentially stale
                time_since_db_check = current_time - self._last_db_check_time
                is_potentially_stale = (
                    self._last_db_check_time > created_time and
                    time_since_db_check < 2.0  # Within 2s of DB check
                )
                
                # BUG #2 FIX: Multi-tier cache freshness strategy with DYNAMIC TTL
                # For DYNAMIC data (price/rating/hours):
                # - Cache < 10s: Very fresh, safe to use
                # - Cache 10-15s: Moderately fresh, prefer fresh search
                # - Cache > 15s: Too stale
                # For STATIC data (name/address):
                # - Cache < 30s: Very fresh
                # - Cache 30-60s: Moderately fresh
                # - Cache > 60s: Too stale
                if is_dynamic:
                    cache_very_fresh = cache_age <= 10
                    cache_moderately_fresh = 10 < cache_age <= 15
                    cache_too_old = cache_age > 15
                else:
                    cache_very_fresh = cache_age <= 30
                    cache_moderately_fresh = 30 < cache_age <= 60
                    cache_too_old = cache_age > 60
                
                if not is_expired and not is_stale and not is_potentially_stale and cache_very_fresh:
                    # Very fresh cache (< 30s) - safe to use immediately
                    # Update last access time for LRU
                    self._search_cache[cache_key] = (cached_results, created_time, time.time(), cache_version, is_dynamic)
                    self._cache_hits += 1
                    hit_rate = self._cache_hits / (self._cache_hits + self._cache_misses) * 100
                    logger.info(f"✅ Cache HIT! Rate: {hit_rate:.1f}% ({self._cache_hits}/{self._cache_hits + self._cache_misses})")
                    # Apply filters to cached results
                    if filters:
                        return self._apply_filters(cached_results, filters)
                    return cached_results[:top_k]
                else:
                    # BUG #CRITICAL-4 FIX: Don't delete moderately fresh cache (30-60s)
                    # Keep it as potential fallback, but attempt fresh search first
                    # CRITICAL: Moderately fresh cache (30-60s) should ALWAYS be kept as fallback,
                    # even if potentially_stale. Only delete if expired, version mismatch, or too old.
                    if cache_moderately_fresh:
                        # Keep moderately fresh cache (30-60s) for potential timeout fallback
                        # Even if potentially_stale, this cache is still valuable as fallback
                        logger.info(f"⚠️  Cache age {cache_age:.1f}s (30-60s), attempting fresh search but keeping as fallback")
                    elif is_expired or is_stale or is_potentially_stale or cache_too_old:
                        # Cache invalid or too old - remove it
                        del self._search_cache[cache_key]
                        if is_expired:
                            reason = 'expired'
                        elif is_stale:
                            reason = 'version_stale'
                        elif cache_too_old:
                            reason = 'too_old_for_fallback'
                        else:
                            reason = 'timestamp_stale'
                        logger.info(f"🗑️ Cache {reason}: {cache_key[:12]}...")
        
        # Cache miss - perform search
        async with self._cache_lock:
            self._cache_misses += 1
        logger.info(f"Cache MISS. Total queries: {self._cache_hits + self._cache_misses}")
        
        # CRITICAL FIX: Calculate dynamic weights based on query type
        semantic_weight, bm25_weight = self._calculate_dynamic_weights(query)
        # FIXED: Log weights with cache key for reproducibility
        logger.info(f"[WEIGHTS] cache_key={cache_key[:8]}... query='{query[:30]}...' semantic={semantic_weight:.3f} bm25={bm25_weight:.3f}")
        
        # Run semantic and BM25 searches IN PARALLEL for speed boost
        import asyncio
        
        async def run_semantic():
            if semantic_weight > 0:
                return await asyncio.to_thread(vector_store.search, query, top_k * 3)
            return []
        
        async def run_bm25():
            if bm25_weight > 0:
                return await asyncio.to_thread(bm25_search.search, query, top_k * 3)
            return []
        
        # FIXED BUG #18: Execute both in parallel with timeout + GRACEFUL FALLBACK
        # FIXED BUG #20: Comprehensive async exception handling
        
        # Track tasks for proper cleanup
        search_task = None
        # BUG #CRITICAL-4 FIX: Track if fallback was used for tagging
        semantic_fallback_used = False
        bm25_fallback_used = False
        
        try:
            # BUG #CRITICAL-4 FIX: asyncio.gather() returns a Future, not a coroutine
            # Cannot wrap it in create_task(). Use gather() directly.
            search_task = asyncio.gather(run_semantic(), run_bm25())
            
            semantic_results, bm25_results = await asyncio.wait_for(
                search_task,
                timeout=5.0  # 5 second timeout for search operations
            )
            
        except asyncio.TimeoutError:
            # BUG #20 FIX: Cancel the task to prevent resource leaks
            if search_task and not search_task.done():
                search_task.cancel()
                try:
                    await search_task  # Wait for cancellation to complete
                except asyncio.CancelledError:
                    pass  # Expected when cancelling
            
            logger.error(f"❌ Hybrid search timeout for query: {query[:50]}...")
            
            # BUG #CRITICAL-4 FIX: Check cache before attempting fallback
            # Prevent returning stale/partial data on timeout
            cache_fallback_used = False
            async with self._cache_lock:
                if cache_key in self._search_cache:
                    cached_data = self._search_cache[cache_key]
                    cached_results, created_time, _, cache_version, is_dynamic = cached_data
                    
                    current_time = time.time()
                    cache_age = current_time - created_time
                    
                    # BUG #2 FIX: Strict staleness checks for DYNAMIC data
                    # Only use cache if: 1) within TTL, 2) version matches
                    max_fallback_age = 15 if is_dynamic else 60
                    if cache_age <= max_fallback_age and cache_version == self._data_version:
                        logger.warning(f"🔄 Using cached results (age: {cache_age:.1f}s) as timeout fallback")
                        
                        # BUG #CRITICAL-4 FIX: Deep copy to avoid modifying cached data
                        fallback_results = copy.deepcopy(cached_results)
                        
                        # Tag results with fallback warning
                        for r in fallback_results:
                            r['_fallback_used'] = True
                            r['_cache_age'] = cache_age
                            r['_warning'] = 'partial_data_timeout_fallback'
                        
                        cache_fallback_used = True
                        
                        # Apply filters to cached results
                        if filters:
                            return self._apply_filters(fallback_results[:top_k], filters)
                        return fallback_results[:top_k]
                        return cached_results[:top_k]
                    else:
                        # BUG #2 FIX: Cache too stale - delete it
                        del self._search_cache[cache_key]
                        if cache_age > max_fallback_age:
                            data_type = 'dynamic' if is_dynamic else 'static'
                            logger.warning(f"⚠️  Cache too stale for {data_type} data ({cache_age:.1f}s > {max_fallback_age}s), not using as fallback")
                        elif cache_version != self._data_version:
                            logger.warning(f"⚠️  Cache version mismatch (v{cache_version} != v{self._data_version}), not using as fallback")
            
            if not cache_fallback_used:
                logger.warning(f"🔄 Attempting live fallback: Try each search separately with shorter timeout")
            
            # CRITICAL FIX: Graceful fallback instead of crashing
            semantic_results = []
            bm25_results = []
            
            # Try semantic only (faster, usually)
            try:
                if semantic_weight > 0:
                    # BUG #CRITICAL-4 FIX: Properly await to_thread call
                    semantic_task = asyncio.to_thread(vector_store.search, query, top_k)
                    raw_results = await asyncio.wait_for(
                        semantic_task,
                        timeout=2.0  # Shorter timeout for fallback
                    )
                    # BUG #CRITICAL-4 FIX: vector_store.search returns tuples, need to convert to dicts for tagging
                    # But we need to keep tuple format for _normalize_scores downstream
                    # So we'll set a flag and handle separately
                    semantic_results = raw_results  # Keep as tuples for now
                    semantic_fallback_used = True
                    logger.info(f"✅ Semantic fallback succeeded: {len(semantic_results)} results (BM25 missing)")
            except asyncio.TimeoutError:
                logger.warning(f"⚠️  Semantic fallback timeout")
                semantic_results = []
                semantic_fallback_used = False
            except asyncio.CancelledError:
                logger.warning(f"⚠️  Semantic fallback cancelled")
                raise  # Re-raise CancelledError for proper propagation
            except Exception as e:
                logger.warning(f"⚠️  Semantic fallback failed: {type(e).__name__}: {e}")
                semantic_results = []
                semantic_fallback_used = False
            
            # Try BM25 only if semantic failed
            if not semantic_results:
                try:
                    if bm25_weight > 0:
                        # BUG #CRITICAL-4 FIX: Properly await to_thread call
                        bm25_task = asyncio.to_thread(bm25_search.search, query, top_k)
                        raw_results = await asyncio.wait_for(
                            bm25_task,
                            timeout=2.0  # Shorter timeout for fallback
                        )
                        # BM25 also returns tuples
                        bm25_results = raw_results
                        bm25_fallback_used = True
                        logger.info(f"✅ BM25 fallback succeeded: {len(bm25_results)} results (semantic missing)")
                except asyncio.TimeoutError:
                    logger.warning(f"⚠️  BM25 fallback timeout")
                    bm25_results = []
                except asyncio.CancelledError:
                    logger.warning(f"⚠️  BM25 fallback cancelled")
                    raise  # Re-raise CancelledError for proper propagation
                except Exception as e:
                    logger.warning(f"⚠️  BM25 fallback failed: {type(e).__name__}: {e}")
                    bm25_results = []
        
        except asyncio.CancelledError:
            # BUG #20 FIX: Handle task cancellation (connection closed, shutdown, etc.)
            logger.warning(f"⚠️  Hybrid search cancelled for query: {query[:50]}...")
            
            # Cancel ongoing task if exists
            if search_task and not search_task.done():
                search_task.cancel()
                try:
                    await search_task
                except asyncio.CancelledError:
                    pass
            
            # Re-raise to propagate cancellation up the chain
            raise
        
        except (KeyboardInterrupt, SystemExit):
            # BUG #20 FIX: Handle graceful shutdown
            logger.error(f"🛑 Shutdown signal received during search")
            
            # Cancel ongoing task
            if search_task and not search_task.done():
                search_task.cancel()
                try:
                    await search_task
                except asyncio.CancelledError:
                    pass
            
            # Re-raise to allow graceful shutdown
            raise
        
        except Exception as e:
            # BUG #20 FIX: Catch all other unexpected exceptions
            logger.error(f"💥 Unexpected error in hybrid search: {type(e).__name__}: {e}")
            logger.exception("Full traceback:")
            
            # Cancel ongoing task
            if search_task and not search_task.done():
                search_task.cancel()
                try:
                    await search_task
                except asyncio.CancelledError:
                    pass
            
            # Return empty results instead of crashing
            semantic_results = []
            bm25_results = []
            
            # If BOTH failed, return popular restaurants as last resort
            if not semantic_results and not bm25_results:
                logger.error(f"🚨 ALL fallbacks failed for query: {query[:50]}...")
                logger.info(f"🔄 Returning popular restaurants as last resort")
                
                try:
                    # Get top popular restaurants from DB (no search, just ORDER BY rating/count)
                    popular = await self._get_popular_restaurants(top_k)
                    
                    # Tag as fallback
                    for r in popular:
                        r['_search_timeout'] = True
                        r['_fallback_popular'] = True
                        r['relevance_score'] = 0.0
                    
                    # Cache with short TTL (30s) since it's fallback data
                    async with self._cache_lock:
                        self._search_cache[cache_key] = (
                            popular,
                            time.time(),
                            30,  # Short TTL for fallback
                            self._data_version,
                            {'timeout_fallback': True}
                        )
                    
                    logger.warning(f"⚠️  Returned {len(popular)} popular restaurants as timeout fallback")
                    return popular
                
                except Exception as e:
                    logger.critical(f"💥 CRITICAL: Even popular fallback failed: {e}")
                    # Absolute last resort: return empty with error flag
                    return [{
                        '_search_timeout': True,
                        '_critical_error': True,
                        '_error_message': 'Search service temporarily unavailable. Please try again.',
                        'id': -1,
                        'name': 'Error',
                        'relevance_score': 0.0
                    }]
        
        # Normalize scores
        semantic_scores = self._normalize_scores(semantic_results, reverse=True) if semantic_results else {}
        bm25_scores = self._normalize_scores(bm25_results, reverse=False) if bm25_results else {}
        
        # Combine scores with DYNAMIC weights
        combined_scores = {}
        
        for restaurant_id, score in semantic_scores.items():
            combined_scores[restaurant_id] = score * semantic_weight
        
        for restaurant_id, score in bm25_scores.items():
            if restaurant_id in combined_scores:
                combined_scores[restaurant_id] += score * bm25_weight
            else:
                combined_scores[restaurant_id] = score * bm25_weight
        
        # Sort by combined score
        sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
        
        # Get restaurant details
        restaurants = await self._get_restaurant_details(sorted_ids[:top_k * 2])
        
        # BUG #10 FIX: Validate semantic search results to prevent hallucination
        # This prevents returning antonyms, negated terms, and semantically opposite results
        if semantic_weight > 0 and restaurants:  # Only if semantic search was used
            restaurants, validation_stats = semantic_validator.filter_results(
                query=query,
                restaurants=restaurants,
                confidence_threshold=0.5
            )
            
            if validation_stats['rejected'] > 0:
                logger.warning(
                    f"🚨 BUG #10 FIX: Hallucination prevention filtered {validation_stats['rejected']} "
                    f"results for query '{query[:50]}'. "
                    f"Reasons: {validation_stats['rejection_reasons']}"
                )
        
        # Apply filters
        if filters:
            restaurants = self._apply_filters(restaurants, filters)
        
        # Add scores and rank
        for restaurant in restaurants:
            restaurant['relevance_score'] = combined_scores.get(restaurant['id'], 0.0)
        
        # ENABLED: Use learned ranker for adaptive ranking
        # Falls back to rule-based ranking if learned ranker unavailable
        try:
            ranker = get_learned_ranker()
            query_context = {
                'user_location': filters.get('user_location') if filters else None,
                'max_budget': filters.get('max_budget') if filters else None,
                'query': query
            }
            ranked_restaurants = ranker.rank_restaurants(restaurants, query_context)
        except Exception as e:
            logger.warning(f"Learned ranker failed, using rule-based: {e}")
            # Fallback to rule-based ranking
            ranked_restaurants = self._rank_results(restaurants, filters)
        
        # BUG #CRITICAL-4 FIX: Tag fallback results with warnings
        # Check if we used semantic-only or BM25-only fallback
        if semantic_fallback_used and not bm25_results:
            # Semantic-only fallback was used
            for restaurant in ranked_restaurants:
                restaurant['_fallback_used'] = True
                restaurant['_fallback_type'] = 'semantic_only'
                restaurant['_warning'] = 'partial_data_no_bm25'
        elif bm25_fallback_used and not semantic_results:
            # BM25-only fallback was used
            for restaurant in ranked_restaurants:
                restaurant['_fallback_used'] = True
                restaurant['_fallback_type'] = 'bm25_only'
                restaurant['_warning'] = 'partial_data_no_semantic'
        
        # BUG #2 FIX: Detect if query involves dynamic data (price, rating, opening hours)
        query_lower = query.lower()
        has_price_query = any(kw in query_lower for kw in ['giá', 'rẻ', 'đắt', 'buffet', 'budget', 'tiền', 'dưới', 'trên', 'tầm', 'k', 'nghìn', 'triệu'])
        has_rating_query = any(kw in query_lower for kw in ['rating', 'đánh giá', 'review', 'ngon', 'sao', 'star', 'tốt', 'chất lượng'])
        has_opening_hours_query = any(kw in query_lower for kw in ['mở cửa', 'đóng cửa', 'giờ', 'bây giờ', 'lúc này', 'hiện tại', 'đang mở', 'open', 'close'])
        is_dynamic_query = has_price_query or has_rating_query or has_opening_hours_query
        
        # Cache results with version tracking
        # FIXED BUG #20: Use lock for thread-safe cache write with LRU eviction
        async with self._cache_lock:
            # Update with last access time for LRU + version + dynamic flag
            current_time = time.time()
            self._search_cache[cache_key] = (
                ranked_restaurants,
                current_time,  # created_time
                current_time,  # last_accessed_time
                self._data_version,  # cache_version
                is_dynamic_query  # is_dynamic (for TTL)
            )
            
            # FIXED BUG #20: Limit cache size with LRU eviction
            if len(self._search_cache) > 1000:
                # Remove oldest 20% by LAST ACCESS time (not creation time)
                sorted_cache = sorted(self._search_cache.items(), key=lambda x: x[1][2])  # Sort by last_accessed
                for old_key, _ in sorted_cache[:200]:
                    del self._search_cache[old_key]
                logger.info(f"🧹 Evicted 200 least recently used cache entries")
        
        return ranked_restaurants[:top_k]
    
    def _calculate_dynamic_weights(self, query: str) -> Tuple[float, float]:
        """
        IMPROVED: Calculate semantic and BM25 weights with consistent logic.
        
        Priority Order:
        1. Exact match detection (e.g., "Phở Lệ", "Pizza 4Ps") → 95% BM25
        2. Named entity with context (e.g., "Phở Hòa quận 1") → 80% BM25
        3. Generic single word (e.g., "buffet", "sushi") → 50/50 balance
        4. Descriptive queries → 60% semantic
        5. Food + location queries → 55% BM25
        
        Args:
            query: User search query
            
        Returns:
            Tuple of (semantic_weight, bm25_weight)
        """
        query_lower = query.lower().strip()
        words = query.split()
        word_count = len(words)
        
        # CRITICAL FIX 1: Detect EXACT MATCH queries (proper names)
        # Examples: "Phở Lệ", "Pizza 4Ps", "Cơm Tấm Sài Gòn"
        # Signal: Multiple words with MOST words capitalized AND not generic food queries
        if word_count >= 2:
            # Filter out common lowercase keywords
            common_keywords = {'quận', 'district', 'gần', 'tìm', 'quán', 'nhà', 'hàng', 'q', 'ở', 'tại'}
            meaningful_words = [w for w in words if w.lower() not in common_keywords]
            
            if meaningful_words:
                capitalized_words = sum(1 for w in meaningful_words if w and w[0].isupper())
                has_number = any(char.isdigit() for char in query)
                
                # CRITICAL: Check for number first (highest priority)
                # "Pizza 4Ps" → exact match even with 1 meaningful word
                if has_number and capitalized_words >= 1:
                    logger.debug(f"🎯 EXACT MATCH mode (has number): '{query}' → 95% BM25")
                    return self._normalize_hybrid_weights(0.05, 0.95)
                
                # For multi-word queries
                if len(meaningful_words) >= 2:
                    # Check if contains ONLY generic food terms (no proper nouns)
                    generic_food_terms = {'phở', 'bún', 'cơm', 'sushi', 'pizza', 'buffet', 'bbq', 
                                         'pasta', 'burger', 'steak', 'cafe', 'bar', 'nướng', 'lẩu'}
                    
                    # Find proper nouns (capitalized non-food words)
                    proper_nouns = [w for w in meaningful_words 
                                   if w and w[0].isupper() and w.lower() not in generic_food_terms]
                    
                    # CRITICAL: At least 2 words capitalized AND has proper noun
                    # Examples: 
                    #   "Phở Lệ" (has "Lệ" proper noun → exact)
                    #   "Cơm Tấm Sài Gòn" (has proper nouns → exact)
                    #   "Sushi Quận 1" (no proper noun, "Quận" is keyword → NOT exact)
                    if capitalized_words >= 2 and proper_nouns:
                        # Has proper noun → exact match
                        logger.debug(f"🎯 EXACT MATCH mode (proper noun '{proper_nouns[0]}'): '{query}' → 95% BM25")
                        return self._normalize_hybrid_weights(0.05, 0.95)
        
        # CRITICAL FIX 2: Named entity with CONTEXT (e.g., "Phở Hòa quận 1")
        # Has proper noun + location/filter keywords
        if word_count >= 2:
            has_capital = any(w and w[0].isupper() for w in words)
            location_keywords = ['quận', 'district', 'q', 'gần', 'đường', 'khu']
            has_location = any(kw in query_lower for kw in location_keywords)
            
            if has_capital and has_location:
                logger.debug(f"📍 Named entity + location: '{query}' → 80% BM25")
                return self._normalize_hybrid_weights(0.2, 0.8)  # 80% BM25 for name + location
        
        # CRITICAL FIX 3: Single word queries - distinguish generic vs specific
        if word_count == 1:
            # Generic food terms → BALANCE (semantic helps with variations)
            generic_terms = [
                'buffet', 'bbq', 'grill', 'nướng', 'lẩu', 'hotpot',
                'quán', 'restaurant', 'nhà hàng', 'cafe', 'bar'
            ]
            if any(term in query_lower for term in generic_terms):
                logger.debug(f"🍽️ Generic term: '{query}' → 50/50 balance")
                return self._normalize_hybrid_weights(0.5, 0.5)  # Balanced for generic terms
            
            # Specific food names → Prefer BM25 but keep some semantic
            specific_foods = [
                'phở', 'bún', 'cơm', 'bánh', 'mì', 'pizza', 'sushi',
                'pasta', 'burger', 'steak', 'dimsum'
            ]
            if any(food in query_lower for food in specific_foods):
                logger.debug(f"🍜 Specific food: '{query}' → 55% BM25")
                return self._normalize_hybrid_weights(0.45, 0.55)  # Slight BM25 preference
            
            # Other single words (rare) → balanced
            return self._normalize_hybrid_weights(0.5, 0.5)
        
        # CRITICAL FIX 4: Descriptive queries with adjectives
        # Must check BEFORE length-based rules
        descriptive_keywords = [
            'romantic', 'cozy', 'yên tĩnh', 'sang trọng', 'view đẹp',
            'không gian', 'atmosphere', 'vibe', 'mood', 'chill',
            'ấm cúng', 'thoáng mát', 'rộng rãi'
        ]
        has_descriptive = any(kw in query_lower for kw in descriptive_keywords)
        
        if has_descriptive:
            # Check if also has specific food/location
            has_specific = any(kw in query_lower for kw in ['phở', 'bún', 'sushi', 'pizza', 'quận', 'gần'])
            if has_specific:
                # "sushi romantic" → balance both
                logger.debug(f"🌟 Descriptive + specific: '{query}' → 60/40 semantic/BM25")
                return self._normalize_hybrid_weights(0.6, 0.4)
            else:
                # Pure descriptive → prefer semantic
                logger.debug(f"💭 Pure descriptive: '{query}' → 70% semantic")
                return self._normalize_hybrid_weights(0.7, 0.3)
        
        # CRITICAL FIX 5: Food + Location queries (most common)
        # Example: "phở quận 1", "sushi nhật bản", "cơm tấm gần đây"
        if word_count <= 5:
            food_keywords = [
                'phở', 'bún', 'cơm', 'bánh', 'mì', 'lẩu', 'nướng',
                'sushi', 'pizza', 'burger', 'steak', 'pasta', 'dimsum'
            ]
            location_keywords = ['quận', 'district', 'gần', 'đường', 'q']
            
            has_food = any(food in query_lower for food in food_keywords)
            has_location = any(loc in query_lower for loc in location_keywords)
            
            if has_food and has_location:
                # Food + location → prefer BM25 for precision
                logger.debug(f"🗺️ Food + location: '{query}' → 55% BM25")
                return self._normalize_hybrid_weights(0.45, 0.55)
            elif has_food:
                # Food only → balance
                logger.debug(f"🍴 Food only: '{query}' → 50/50")
                return self._normalize_hybrid_weights(0.5, 0.5)
        
        # CRITICAL FIX 6: Long queries - DON'T over-rely on semantic
        # Example: "tìm quán ăn ngon view đẹp romantic không quá đắt"
        if word_count > 10:
            # Still need BM25 for keyword matching
            logger.debug(f"📝 Long query: '{query}' → 65% semantic (not 75%)")
            return self._normalize_hybrid_weights(0.65, 0.35)  # Reduced from 0.75 to 0.65
        
        # Medium queries (6-10 words) → Balanced
        if word_count <= 10:
            logger.debug(f"⚖️ Medium query: '{query}' → 60/40 semantic/BM25")
            return self._normalize_hybrid_weights(0.6, 0.4)
        
        # Default: Use configured weights
        logger.debug(f"⚙️ Default weights for: '{query}'")
        return self._normalize_hybrid_weights(self.default_semantic_weight, self.default_bm25_weight)
    
    def _normalize_hybrid_weights(self, semantic_weight: float, bm25_weight: float) -> Tuple[float, float]:
        """
        BUG #5 FIX: Normalize semantic and BM25 weights to ensure they sum to exactly 1.0.
        
        This prevents:
        - Weight sum > 1.0 (over-scoring)
        - Weight sum < 1.0 (under-scoring)
        - Inconsistent search results
        
        Args:
            semantic_weight: Raw semantic weight
            bm25_weight: Raw BM25 weight
            
        Returns:
            Tuple of (normalized_semantic_weight, normalized_bm25_weight)
        """
        from decimal import Decimal, ROUND_HALF_UP
        
        # Convert to Decimal for precise arithmetic
        sem_dec = Decimal(str(semantic_weight))
        bm25_dec = Decimal(str(bm25_weight))
        weight_sum = sem_dec + bm25_dec
        
        EPSILON = Decimal('1e-9')
        
        # Check if already normalized
        if abs(weight_sum - Decimal('1.0')) < EPSILON:
            return (semantic_weight, bm25_weight)
        
        # Normalize proportionally
        if weight_sum > 0:
            normalization_factor = Decimal('1.0') / weight_sum
            normalized_semantic = float(sem_dec * normalization_factor)
            normalized_bm25 = float(bm25_dec * normalization_factor)
            
            logger.warning(
                f"⚠️  BUG #5 FIX: Hybrid weights normalized from "
                f"sum={float(weight_sum):.6f} to 1.0 "
                f"(semantic: {semantic_weight:.3f} → {normalized_semantic:.3f}, "
                f"bm25: {bm25_weight:.3f} → {normalized_bm25:.3f})"
            )
            
            return (normalized_semantic, normalized_bm25)
        else:
            # Both weights zero - use 50/50 default
            logger.error(
                "❌ BUG #5 FIX: Both weights were zero, using 50/50 default"
            )
            return (0.5, 0.5)
    
    async def start_version_sync(self):
        """BUG #16 FIX: Start background task to sync data version from DB."""
        import asyncio
        
        if self._version_sync_task is None or self._version_sync_task.done():
            self._version_sync_task = asyncio.create_task(self._sync_data_version_loop())
            logger.info("🔄 Started data version sync task")
    
    async def _sync_data_version_loop(self):
        """
        BUG #4 FIX: Background loop to sync data version with aggressive staleness detection.
        
        Improvements:
        - Reduced interval: 5s → 1s (80% faster detection)
        - Event-driven invalidation for immediate updates
        - Timestamp-based staleness check
        - Graceful degradation on errors
        """
        import asyncio
        import time
        
        logger.info("🔄 Started aggressive version sync loop (1s interval)")
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while True:
            try:
                # BUG #4 FIX: Wait 1 second OR until invalidation event
                # This allows immediate updates via webhook while still having periodic checks
                try:
                    await asyncio.wait_for(
                        self._invalidation_event.wait(),
                        timeout=1.0  # BUG #4 FIX: Reduced from 5s to 1s (80% faster)
                    )
                    # Event triggered - immediate invalidation requested
                    logger.info("⚡ Immediate invalidation event triggered!")
                    self._invalidation_event.clear()
                except asyncio.TimeoutError:
                    # Normal 1s periodic check
                    pass
                except asyncio.CancelledError:
                    # BUG #20 FIX: Task cancelled (shutdown)
                    logger.info("🛑 Version sync task cancelled (graceful shutdown)")
                    break  # Exit loop gracefully
                
                # Get current DB version
                db_version = await db_manager.get_data_version()
                current_time = time.time()
                self._last_db_check_time = current_time
                
                # Check if version changed
                if db_version != self._data_version:
                    old_version = self._data_version
                    self._data_version = db_version
                    
                    # BUG #4 FIX: Immediate cache invalidation on version change
                    async with self._cache_lock:
                        stale_count = 0
                        keys_to_remove = []
                        for key, (_, _, _, cache_version, _) in list(self._search_cache.items()):
                            if cache_version != db_version:
                                keys_to_remove.append(key)
                                stale_count += 1
                        
                        for key in keys_to_remove:
                            del self._search_cache[key]
                        
                        logger.warning(f"🔄 Data version changed: {old_version} → {db_version}")
                        if stale_count > 0:
                            logger.warning(f"🗑️ IMMEDIATELY invalidated {stale_count} stale cache entries")
                        else:
                            logger.info("✅ No stale cache entries (cache was already clean)")
                
                # Reset error counter on success
                consecutive_errors = 0
            
            except asyncio.CancelledError:
                # BUG #20 FIX: Handle task cancellation gracefully
                logger.info("🛑 Version sync loop cancelled (graceful shutdown)")
                break  # Exit loop gracefully
            
            except (KeyboardInterrupt, SystemExit):
                # BUG #20 FIX: Handle graceful shutdown signals
                logger.error("🛑 Shutdown signal received in version sync loop")
                break  # Exit loop gracefully
            
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"❌ Error in version sync loop ({consecutive_errors}/{max_consecutive_errors}): {type(e).__name__}: {e}")
                
                # BUG #4 FIX: Graceful degradation - if too many errors, invalidate cache as safety measure
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"🚨 Version sync failing repeatedly! Invalidating cache as safety measure.")
                    try:
                        async with self._cache_lock:
                            cache_size = len(self._search_cache)
                            self._search_cache.clear()
                            logger.warning(f"⚠️ Safety invalidation: cleared {cache_size} entries")
                    except Exception as clear_error:
                        logger.error(f"💥 Failed to clear cache: {clear_error}")
                    consecutive_errors = 0  # Reset
                
                # Exponential backoff on errors (but max 10s)
                error_sleep = min(10, 2 ** consecutive_errors)
                try:
                    await asyncio.sleep(error_sleep)
                except asyncio.CancelledError:
                    logger.info("🛑 Sleep interrupted by cancellation")
                    break  # Exit if cancelled during sleep
    
    async def invalidate_cache_on_data_change(self, reason: str = "data_change"):
        """
        BUG #4 FIX: IMMEDIATE cache invalidation when data changes (webhook-style).
        
        This provides event-driven invalidation instead of waiting for periodic sync.
        Called by db_manager hooks when:
        - Restaurant added/updated/deleted
        - Index rebuilt
        - Admin data changes
        
        This eliminates the 1-5s staleness window!
        """
        async with self._cache_lock:
            old_size = len(self._search_cache)
            self._search_cache.clear()
            logger.warning(f"⚡ IMMEDIATE Cache INVALIDATION! Reason: {reason}. Cleared {old_size} entries")
            
            # Reset stats
            self._cache_hits = 0
            self._cache_misses = 0
        
        # BUG #4 FIX: Trigger immediate version sync (don't wait for next 1s interval)
        self._invalidation_event.set()
        logger.info("⚡ Invalidation event triggered for immediate version sync")
    
    async def invalidate_cache(self, reason: str = "manual"):
        """
        CRITICAL: Invalidate all cache when data changes.
        
        Call this when:
        - Admin adds/updates/deletes restaurant
        - Price changes
        - Rating changes
        - Index rebuilt
        
        Args:
            reason: Reason for invalidation (for logging)
        """
        async with self._cache_lock:
            cache_size = len(self._search_cache)
            self._search_cache.clear()
            self._data_version += 1
            logger.warning(f"⚠️ Cache INVALIDATED (reason: {reason}): cleared {cache_size} entries, version → {self._data_version}")
    
    async def invalidate_cache_for_restaurant(self, restaurant_id: int):
        """
        OPTIMIZED: Partial invalidation for single restaurant change.
        
        More efficient than full invalidation.
        
        Args:
            restaurant_id: ID of changed restaurant
        """
        async with self._cache_lock:
            # Remove cache entries that might contain this restaurant
            # This is approximate - we increment version to be safe
            self._data_version += 1
            logger.info(f"🔄 Partial cache invalidation for restaurant {restaurant_id}, version → {self._data_version}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring.
        
        BUG #4 FIX: This method should NOT be async because it's called from
        sync contexts. We use a try-lock pattern to safely read cache size.
        """
        total_queries = self._cache_hits + self._cache_misses
        hit_rate = (self._cache_hits / total_queries * 100) if total_queries > 0 else 0
        
        # BUG #4 FIX: Safe cache size reading without blocking
        # If lock is held (e.g., during invalidation), return last known size
        try:
            # Try non-blocking lock acquisition for stats
            import threading
            cache_size = len(self._search_cache)  # Read is atomic in Python GIL
        except:
            cache_size = -1  # Unknown if error occurs
        
        return {
            'cache_size': cache_size,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'hit_rate': round(hit_rate, 2),
            'data_version': self._data_version
        }
    
    def _normalize_scores(
        self,
        results: List[Tuple[int, float]],
        reverse: bool = False
    ) -> Dict[int, float]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            results: List of (id, score) tuples
            reverse: If True, lower scores are better (for distance)
            
        Returns:
            Dictionary of normalized scores
        """
        if not results:
            return {}
        
        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return {id: 1.0 for id, _ in results}
        
        normalized = {}
        for id, score in results:
            norm_score = (score - min_score) / (max_score - min_score)
            if reverse:
                norm_score = 1.0 - norm_score
            normalized[id] = norm_score
        
        return normalized
    
    async def _get_restaurant_details(self, restaurant_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get full restaurant details from database with RETRY mechanism.
        
        FIXED: Added exponential backoff retry for DB failures.
        
        Args:
            restaurant_ids: List of restaurant IDs
            
        Returns:
            List of restaurant dictionaries
        """
        if not restaurant_ids:
            return []
        
        placeholders = ','.join('?' * len(restaurant_ids))
        query = f"SELECT * FROM restaurants WHERE id IN ({placeholders})"
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with db_manager.get_connection() as db:
                    db.row_factory = aiosqlite.Row
                    async with db.execute(query, restaurant_ids) as cursor:
                        rows = await cursor.fetchall()
                        restaurants = []
                        
                        for row in rows:
                            restaurant = dict(row)
                            # Parse JSON fields
                            if restaurant.get('food_tags'):
                                try:
                                    restaurant['food_tags'] = json.loads(restaurant['food_tags'])
                                except:
                                    restaurant['food_tags'] = []
                            if restaurant.get('comments'):
                                try:
                                    restaurant['comments'] = json.loads(restaurant['comments'])
                                except:
                                    restaurant['comments'] = []
                            
                            # BUG #21 FIX: Validate restaurant data before returning
                            validated = restaurant_validator.validate_restaurant(restaurant)
                            if validated:
                                restaurants.append(validated)
                            else:
                                logger.warning(f"⚠️  Skipped invalid restaurant: {restaurant.get('id', 'UNKNOWN')}")
                        
                        return restaurants
                        
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 0.1 * (2 ** attempt)  # Exponential backoff: 0.1s, 0.2s, 0.4s
                    logger.warning(f"⚠️ DB error attempt {attempt + 1}/{max_retries}, retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"❌ DB failed after {max_retries} attempts: {e}")
                    raise
        
        return []  # Fallback
    
    async def _get_popular_restaurants(self, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Get popular restaurants as fallback when search fails.
        
        BUG #18 FIX: Fallback strategy when hybrid search times out.
        Returns high-rated, popular restaurants (no search, just DB query).
        
        Args:
            top_k: Number of restaurants to return
            
        Returns:
            List of popular restaurants
        """
        try:
            # Simple query: ORDER BY rating DESC, review_count DESC
            query = """
                SELECT * FROM restaurants 
                WHERE rating >= 4.0 
                ORDER BY rating DESC, id ASC 
                LIMIT ?
            """
            
            async with db_manager.get_connection() as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(query, (top_k,)) as cursor:
                    rows = await cursor.fetchall()
                    restaurants = []
                    
                    for row in rows:
                        restaurant = dict(row)
                        # Parse JSON fields
                        if restaurant.get('food_tags'):
                            try:
                                restaurant['food_tags'] = json.loads(restaurant['food_tags'])
                            except:
                                restaurant['food_tags'] = []
                        if restaurant.get('comments'):
                            try:
                                restaurant['comments'] = json.loads(restaurant['comments'])
                            except:
                                restaurant['comments'] = []
                        
                        # BUG #21 FIX: Validate restaurant data before returning
                        validated = restaurant_validator.validate_restaurant(restaurant)
                        if validated:
                            # Tag as popular fallback
                            validated['relevance_score'] = 0.0
                            validated['_popular_fallback'] = True
                            restaurants.append(validated)
                        else:
                            logger.warning(f"⚠️  Skipped invalid popular restaurant: {restaurant.get('id', 'UNKNOWN')}")
                    
                    logger.info(f"✅ Retrieved {len(restaurants)} popular restaurants as fallback")
                    return restaurants
        
        except Exception as e:
            logger.error(f"❌ Failed to get popular restaurants: {e}")
            return []
    
    def _apply_filters(
        self,
        restaurants: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply SOFT filters with scoring (ChatGPT-style).
        Instead of hard filtering (removing non-matches), we score each restaurant.
        
        Args:
            restaurants: List of restaurants
            filters: Filter criteria
            
        Returns:
            Filtered restaurant list with filter scores
        """
        # CHATGPT-STYLE SOFT FILTERING
        # Score each restaurant based on filter matches
        # Perfect match = 1.0, Partial match = 0.5-0.8, No match = 0.3
        
        for restaurant in restaurants:
            filter_score = 1.0
            filter_matches = []
            filter_misses = []
            
            # Price level filter (weight: 0.8 if specified)
            if filters.get('price_level'):
                price_level = filters['price_level']
                restaurant_price = restaurant.get('price_level')
                if restaurant_price == price_level:
                    filter_matches.append('price_exact')
                else:
                    # Check if close (within 1 level)
                    price_order = ['PRICE_LEVEL_INEXPENSIVE', 'PRICE_LEVEL_MODERATE', 
                                   'PRICE_LEVEL_EXPENSIVE', 'PRICE_LEVEL_VERY_EXPENSIVE']
                    try:
                        user_idx = price_order.index(price_level)
                        rest_idx = price_order.index(restaurant_price) if restaurant_price in price_order else -1
                        if rest_idx >= 0 and abs(user_idx - rest_idx) == 1:
                            filter_score *= 0.7  # Close match
                            filter_matches.append('price_close')
                        else:
                            filter_score *= 0.4  # Different price range
                            filter_misses.append('price')
                    except:
                        filter_score *= 0.5
            else:
                filter_matches.append('price_na')
            
            # Cuisine/Food type filter (weight: 0.9 if specified)
            if filters.get('cuisine_types'):
                cuisine_types = filters['cuisine_types']
                restaurant_tags = restaurant.get('food_tags', [])
                if isinstance(restaurant_tags, str):
                    import json
                    try:
                        restaurant_tags = json.loads(restaurant_tags)
                    except:
                        restaurant_tags = []
                
                # Check for matches
                tag_match_found = False
                for cuisine in cuisine_types:
                    cuisine_lower = str(cuisine).lower()
                    for tag in restaurant_tags:
                        tag_lower = str(tag).lower()
                        if cuisine_lower in tag_lower or tag_lower in cuisine_lower:
                            tag_match_found = True
                            break
                    if tag_match_found:
                        break
                
                if tag_match_found:
                    filter_matches.append('cuisine_match')
                else:
                    filter_score *= 0.5  # Penalty for no cuisine match
                    filter_misses.append('cuisine')
            else:
                filter_matches.append('cuisine_na')
            
            # Rating filter (weight: 0.7 if specified)
            if filters.get('min_rating'):
                min_rating = filters['min_rating']
                restaurant_rating = restaurant.get('rating', 0)
                if restaurant_rating >= min_rating:
                    filter_matches.append('rating_match')
                elif restaurant_rating >= min_rating - 0.5:
                    filter_score *= 0.8  # Close rating
                    filter_matches.append('rating_close')
                else:
                    filter_score *= 0.4  # Low rating
                    filter_misses.append('rating')
            else:
                filter_matches.append('rating_na')
            
            # Location filter (weight: 0.85 if specified)
            if filters.get('locations'):
                requested_locations = filters['locations']
                from utils.text_processing import normalize_text
                
                address = restaurant.get('address', '')
                location_summary = restaurant.get('location_summary', '')
                name = restaurant.get('name', '')
                combined_text = f"{name} {address} {location_summary}".lower()
                
                location_match = False
                for loc in requested_locations:
                    loc_normalized = normalize_text(loc, remove_accents=True).lower()
                    combined_normalized = normalize_text(combined_text, remove_accents=True)
                    if loc_normalized in combined_normalized:
                        location_match = True
                        break
                
                if location_match:
                    filter_matches.append('location_match')
                else:
                    filter_score *= 0.6  # Penalty for wrong location
                    filter_misses.append('location')
            else:
                filter_matches.append('location_na')
            
            # Store soft filter score (0.3 minimum for any restaurant)
            restaurant['_soft_filter_score'] = max(0.3, filter_score)
            restaurant['_filter_matches'] = filter_matches
            restaurant['_filter_misses'] = filter_misses
        
        # BUG #7 FIX: Calculate distances BEFORE sorting (moved from legacy code below)
        if filters.get('user_location'):
            # BUG #12 FIX: Safe location parsing
            from utils.location_utils import parse_location
            parsed = parse_location(filters['user_location'])
            
            if parsed is None:
                logger.warning(f"⚠️ Invalid user location format: {filters['user_location']}")
                # Set all distances to None
                for restaurant in restaurants:
                    restaurant['distance'] = None
            else:
                user_lat, user_lon = parsed
            
                # Validate user location first
                if not self._validate_coordinates(user_lat, user_lon):
                    logger.warning(f"⚠️ Invalid user location: lat={user_lat}, lon={user_lon}")
                    # Set all distances to None
                    for restaurant in restaurants:
                        restaurant['distance'] = None
                else:
                    # Calculate distances for valid user location
                    for restaurant in restaurants:
                        rest_lat = restaurant.get('coordinates_lat')
                        rest_lon = restaurant.get('coordinates_lon')
                        
                        # Validate restaurant coordinates
                        if rest_lat is None or rest_lon is None:
                            restaurant['distance'] = None
                            continue
                        
                        if not self._validate_coordinates(rest_lat, rest_lon):
                            logger.debug(f"Invalid coordinates for {restaurant.get('name')}: lat={rest_lat}, lon={rest_lon}")
                            restaurant['distance'] = None
                            continue
                        
                        try:
                            distance = self._calculate_distance(
                                user_lat, user_lon,
                                rest_lat, rest_lon
                            )
                            restaurant['distance'] = distance
                        except (TypeError, ValueError, OverflowError, ZeroDivisionError) as e:
                            logger.warning(f"Distance calculation error for {restaurant.get('name')}: {e}")
                            restaurant['distance'] = None
        
        # Sort by soft filter score (higher = better match)
        restaurants.sort(key=lambda x: x.get('_soft_filter_score', 0.3), reverse=True)
        
        # Return all restaurants with scores (no hard removal)
        logger.info(f"Soft filtering completed: {len(restaurants)} restaurants scored")
        return restaurants
        
        # Budget filter (Google Maps $ price level system) - LEGACY CODE BELOW, KEPT FOR REFERENCE
        if filters.get('max_budget'):
            max_budget = filters['max_budget']
            # Map price levels to approximate per-person costs (Google Maps style)
            # $ (INEXPENSIVE) = under 100k per person
            # $$ (MODERATE) = 100-300k per person
            # $$$ (EXPENSIVE) = 300-500k per person
            # $$$$ (VERY_EXPENSIVE) = over 500k per person
            
            # SMART BUDGET FILTERING with fallback
            # Mark budget fit: strict, loose, over
            price_map = {
                'PRICE_LEVEL_INEXPENSIVE': 75000,
                'PRICE_LEVEL_MODERATE': 150000,
                'PRICE_LEVEL_EXPENSIVE': 350000,
                'PRICE_LEVEL_VERY_EXPENSIVE': 600000
            }
            
            strict_match = []
            loose_match = []  # Within 30% tolerance
            
            for r in filtered:
                est_price = price_map.get(r.get('price_level', ''), 150000)
                if est_price <= max_budget:
                    r['_budget_fit'] = 'strict'
                    strict_match.append(r)
                elif est_price <= max_budget * 1.3:  # 30% tolerance
                    r['_budget_fit'] = 'loose'
                    loose_match.append(r)
                else:
                    r['_budget_fit'] = 'over'
            
            # Strategy: Use strict if available, else use loose
            if len(strict_match) >= 3:
                # Enough strict matches, use only those
                filtered = strict_match
                filters['_budget_strategy'] = 'strict'
            elif len(strict_match) > 0:
                # Some strict matches, prioritize them but include loose
                filtered = strict_match + loose_match[:5]
                filters['_budget_strategy'] = 'mixed'
            else:
                # No strict matches, use loose (with warning)
                filtered = loose_match
                filters['_budget_strategy'] = 'relaxed'
                filters['_budget_warning'] = True
        
        # Rating filter
        if filters.get('min_rating'):
            min_rating = filters['min_rating']
            filtered = [r for r in filtered if r.get('rating', 0) >= min_rating]
        
        # Location filter by district/area name
        if filters.get('locations'):
            requested_locations = filters['locations']
            # Normalize for matching
            from utils.text_processing import normalize_text
            
            location_filtered = []
            for restaurant in filtered:
                address = restaurant.get('address', '')
                location_summary = restaurant.get('location_summary', '')
                name = restaurant.get('name', '')
                
                # Combine all text for matching
                combined_text = f"{name} {address} {location_summary}".lower()
                
                # Check if any requested location is in the combined text
                match_found = False
                for loc in requested_locations:
                    loc_normalized = normalize_text(loc, remove_accents=True).lower()
                    combined_normalized = normalize_text(combined_text, remove_accents=True)
                    
                    if loc_normalized in combined_normalized:
                        match_found = True
                        restaurant['_location_match_score'] = 1.0  # Mark as exact match
                        break
                
                if match_found:
                    location_filtered.append(restaurant)
            
            # Apply filter if we have at least 5 results (more lenient threshold)
            min_results = max(5, int(len(filtered) * 0.2))  # 20% threshold instead of 40%
            if len(location_filtered) >= min_results:
                filtered = location_filtered
                # Sort by location match (exact matches first) then by original score
                filtered.sort(key=lambda x: x.get('_location_match_score', 0), reverse=True)
        
        # Location filter (if user location provided)
        if filters.get('user_location'):
            # BUG #12 FIX: Safe location parsing
            from utils.location_utils import parse_location
            parsed = parse_location(filters['user_location'])
            
            if parsed is None:
                logger.warning(f"⚠️ Invalid user location format: {filters['user_location']}")
                # Skip distance calculation for all restaurants
                for restaurant in filtered:
                    restaurant['distance'] = None
                return filtered
            
            user_lat, user_lon = parsed
            
            # BUG #7 FIX: Validate user location first
            if not self._validate_coordinates(user_lat, user_lon):
                logger.warning(f"⚠️ Invalid user location: lat={user_lat}, lon={user_lon}")
                # Skip distance calculation for all restaurants
                for restaurant in filtered:
                    restaurant['distance'] = None
                return filtered
            
            # DEBUG: Log that we're in distance calculation block
            logger.debug(f"📍 Calculating distances for {len(filtered)} restaurants")
            
            for restaurant in filtered:
                rest_lat = restaurant.get('coordinates_lat')
                rest_lon = restaurant.get('coordinates_lon')
                
                # BUG #7 FIX: Comprehensive validation
                # Check 1: Not None
                if rest_lat is None or rest_lon is None:
                    restaurant['distance'] = None
                    continue
                
                # Check 2: Validate restaurant coordinates
                if not self._validate_coordinates(rest_lat, rest_lon):
                    logger.debug(f"Invalid coordinates for {restaurant.get('name')}: lat={rest_lat}, lon={rest_lon}")
                    restaurant['distance'] = None
                    continue
                
                try:
                    distance = self._calculate_distance(
                        user_lat, user_lon,
                        rest_lat, rest_lon
                    )
                    restaurant['distance'] = distance
                except (TypeError, ValueError, OverflowError, ZeroDivisionError) as e:
                    # Handle any remaining edge cases
                    logger.warning(f"Distance calculation error for {restaurant.get('name')}: {e}")
                    restaurant['distance'] = None
        
        return filtered
    
    def _validate_coordinates(self, lat: any, lon: any) -> bool:
        """
        BUG #7 FIX: Comprehensive coordinate validation.
        
        Checks for:
        - None values
        - Type errors (string, list, dict, etc.)
        - NaN values
        - Infinity values
        - Out-of-range values (lat: -90 to 90, lon: -180 to 180)
        - Gulf of Guinea bug (0, 0)
        
        Args:
            lat: Latitude value
            lon: Longitude value
            
        Returns:
            True if valid, False otherwise
        """
        import math
        
        # Check 1: None values
        if lat is None or lon is None:
            return False
        
        # Check 2: Type validation (must be numeric)
        try:
            lat = float(lat)
            lon = float(lon)
        except (TypeError, ValueError):
            # String, list, dict, or other non-numeric types
            return False
        
        # Check 3: NaN detection
        if math.isnan(lat) or math.isnan(lon):
            return False
        
        # Check 4: Infinity detection
        if math.isinf(lat) or math.isinf(lon):
            return False
        
        # Check 5: Valid range
        # Latitude: -90 to 90
        # Longitude: -180 to 180
        if not (-90 <= lat <= 90):
            return False
        
        if not (-180 <= lon <= 180):
            return False
        
        # Check 6: Gulf of Guinea bug (0, 0)
        # Many invalid/missing coordinates default to (0, 0)
        # This is in the Atlantic Ocean, unlikely to be valid for Vietnam restaurants
        if lat == 0 and lon == 0:
            return False
        
        return True
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates (Haversine formula).
        
        ASSUMES: Coordinates are already validated by _validate_coordinates()
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        import math
        
        # Haversine formula
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)
    
    def _rank_results(
        self,
        restaurants: List[Dict[str, Any]],
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Final ranking based on multiple factors.
        UNIFIED WEIGHTS with learned_ranker for consistency.
        
        Args:
            restaurants: List of restaurants with relevance scores
            filters: User preferences
            
        Returns:
            Ranked restaurant list
        """
        if not restaurants:
            return []
        
        # Calculate ranking score with UNIFIED WEIGHTS
        for restaurant in restaurants:
            score = 0.0
            
            # Base relevance (40%)
            score += restaurant.get('relevance_score', 0) * 0.4
            
            # Rating (25%) - UNIFIED with learned_ranker
            rating = restaurant.get('rating', 0)
            if rating:
                score += (rating / 5.0) * 0.25
            
            # Popularity (rating count) (15%)
            rating_count = restaurant.get('rating_count', 0)
            if rating_count:
                # Normalize rating count (log scale)
                import math
                popularity_score = min(1.0, math.log10(rating_count + 1) / 4)
                score += popularity_score * 0.15
            
            # Distance (15%) - if available
            if restaurant.get('distance') is not None:
                distance = restaurant['distance']
                # Closer is better, normalize to max 10km
                distance_score = max(0, 1.0 - (distance / 10.0))
                score += distance_score * 0.15
            else:
                # If no distance, give neutral score
                score += 0.075
            
            # Price match (5%) - ADDED for consistency with learned_ranker
            if filters and filters.get('max_budget'):
                max_budget = filters['max_budget']
                est_price = self._estimate_price(restaurant)
                if est_price <= max_budget:
                    score += 0.05
                elif est_price <= max_budget * 1.2:
                    score += 0.025
            else:
                score += 0.025
            
            restaurant['ranking_score'] = score
        
        # Sort by ranking score
        ranked = sorted(restaurants, key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked
    
    def _estimate_price(self, restaurant: Dict[str, Any]) -> float:
        """Estimate average price per person from price_level."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': 75000,
            'PRICE_LEVEL_MODERATE': 150000,
            'PRICE_LEVEL_EXPENSIVE': 350000,
            'PRICE_LEVEL_VERY_EXPENSIVE': 600000
        }
        return price_map.get(restaurant.get('price_level', ''), 150000)
    
    async def _get_restaurants_by_ids(self, restaurant_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Fetch fresh restaurant data from database by IDs.
        
        BUG #22 FIX: Prevents dangling references by fetching current data.
        
        Args:
            restaurant_ids: List of restaurant IDs
            
        Returns:
            List of restaurant dictionaries with fresh data
        """
        if not restaurant_ids:
            return []
        
        try:
            async with aiosqlite.connect(settings.DB_PATH) as db:
                db.row_factory = aiosqlite.Row
                
                # Build query with placeholders
                placeholders = ','.join('?' * len(restaurant_ids))
                query = f"""
                    SELECT id, name, rating, editorial_summary, price_level, 
                           types, formatted_address, lat, lng, rating_count,
                           google_maps_url, opening_hours, website, phone_number
                    FROM restaurants
                    WHERE id IN ({placeholders})
                """
                
                cursor = await db.execute(query, restaurant_ids)
                rows = await cursor.fetchall()
                
                restaurants = []
                for row in rows:
                    restaurant = dict(row)
                    
                    # Parse JSON fields
                    if restaurant.get('types'):
                        restaurant['types'] = json.loads(restaurant['types'])
                    if restaurant.get('opening_hours'):
                        restaurant['opening_hours'] = json.loads(restaurant['opening_hours'])
                    
                    restaurants.append(restaurant)
                
                logger.debug(f"Fetched {len(restaurants)}/{len(restaurant_ids)} restaurants from DB")
                return restaurants
                
        except Exception as e:
            logger.error(f"Error fetching restaurants by IDs: {e}")
            return []


# Global instance
hybrid_search = HybridSearch()
