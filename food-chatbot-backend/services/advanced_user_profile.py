"""
Advanced User Profile Manager with ML-based Personalization
Learns user preferences through implicit and explicit signals.
"""
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import numpy as np
from sklearn.preprocessing import MinMaxScaler
from database.postgres_manager import postgres_manager
from database.redis_manager import redis_manager
import asyncio


class AdvancedUserProfileManager:
    """
    Enhanced user profile manager with:
    - Long-term memory (PostgreSQL)
    - Implicit signal learning (clicks, time spent, scroll depth)
    - Collaborative filtering
    - Preference evolution tracking
    - Smart cold start handling
    """
    
    def __init__(self):
        self.scaler = MinMaxScaler()
        
        # Weight configurations for different signals
        self.SIGNAL_WEIGHTS = {
            'explicit_like': 1.0,
            'click': 0.7,
            'view': 0.3,
            'time_spent_long': 0.6,  # >30 seconds
            'time_spent_medium': 0.4,  # 10-30 seconds
            'time_spent_short': 0.1,  # <10 seconds
            'search_repeat': 0.5,
            'scroll_depth_high': 0.4,  # >70%
            'scroll_depth_medium': 0.2,  # 30-70%
        }
        
        # Cold start thresholds
        self.COLD_START_SEARCHES = 3
        self.WARM_START_SEARCHES = 10
        self.HOT_START_SEARCHES = 30
    
    # ==================== Profile Management ====================
    
    async def get_or_create_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile with caching."""
        # Try cache first
        cached = await redis_manager.get_user_profile_cache(user_id)
        if cached:
            return cached
        
        # Get from database
        profile = await postgres_manager.get_user_profile(user_id)
        
        if not profile:
            # Create new profile
            profile = await postgres_manager.create_or_update_profile(user_id)
        
        # Cache for fast access
        await redis_manager.set_user_profile_cache(user_id, profile)
        
        return profile
    
    async def update_profile_activity(self, user_id: str, search_success: bool = False):
        """Update user activity counters."""
        await postgres_manager.update_user_activity(user_id, search_success)
        
        # Invalidate cache
        await redis_manager.invalidate_user_profile_cache(user_id)
    
    # ==================== Implicit Signal Learning ====================
    
    async def record_restaurant_interaction(
        self,
        user_id: str,
        restaurant_id: int,
        interaction_type: str,  # 'click', 'view', 'like', 'dislike'
        context: Optional[Dict] = None
    ):
        """Record user interaction with restaurant."""
        # Save to PostgreSQL
        await postgres_manager.save_interaction(
            user_id, restaurant_id, interaction_type, context
        )
        
        # Update real-time preferences
        await self._update_realtime_preferences(
            user_id, restaurant_id, interaction_type, context
        )
    
    async def _update_realtime_preferences(
        self,
        user_id: str,
        restaurant_id: int,
        interaction_type: str,
        context: Optional[Dict]
    ):
        """Update user preferences based on interaction."""
        if not context:
            return
        
        # Extract restaurant features from context
        cuisine = context.get('cuisine')
        price_range = context.get('price_range')
        atmosphere = context.get('atmosphere', [])
        
        # Get current preferences
        prefs = await postgres_manager.get_preferences(user_id)
        if not prefs:
            prefs = {
                'favorite_cuisines': [],
                'cuisine_weights': {},
                'favorite_atmospheres': []
            }
        
        # Update cuisine preferences with weighted signal
        signal_weight = self.SIGNAL_WEIGHTS.get(interaction_type, 0.5)
        
        if cuisine:
            cuisine_weights = prefs.get('cuisine_weights', {})
            if isinstance(cuisine_weights, str):
                import json
                cuisine_weights = json.loads(cuisine_weights)
            
            current_weight = cuisine_weights.get(cuisine, 0.0)
            cuisine_weights[cuisine] = current_weight + signal_weight
            
            # Update favorite cuisines list
            favorite_cuisines = prefs.get('favorite_cuisines', [])
            if cuisine not in favorite_cuisines:
                favorite_cuisines.append(cuisine)
            
            await postgres_manager.update_preferences(
                user_id,
                favorite_cuisines=favorite_cuisines,
                cuisine_weights=cuisine_weights
            )
        
        # Update atmosphere preferences
        if atmosphere:
            favorite_atmospheres = prefs.get('favorite_atmospheres', [])
            for atmo in atmosphere:
                if atmo not in favorite_atmospheres:
                    favorite_atmospheres.append(atmo)
            
            await postgres_manager.update_preferences(
                user_id,
                favorite_atmospheres=favorite_atmospheres
            )
        
        # Invalidate cache
        await redis_manager.invalidate_user_profile_cache(user_id)
    
    async def record_search(
        self,
        user_id: str,
        session_id: str,
        query: str,
        intent: Optional[str],
        params: Dict[str, Any],
        results_count: int,
        time_spent: Optional[int] = None,
        clicked_restaurants: Optional[List[int]] = None
    ):
        """Record a search event."""
        was_successful = bool(clicked_restaurants and len(clicked_restaurants) > 0)
        
        await postgres_manager.save_search(
            user_id=user_id,
            session_id=session_id,
            query=query,
            intent=intent,
            cuisines=params.get('cuisines'),
            price_range=params.get('price_range'),
            max_budget=params.get('max_budget'),
            max_distance=params.get('max_distance'),
            atmosphere=params.get('atmosphere'),
            user_location=params.get('user_location'),
            results_count=results_count,
            clicked_restaurants=clicked_restaurants,
            time_spent=time_spent,
            was_successful=was_successful
        )
        
        # Update activity counter
        await self.update_profile_activity(user_id, was_successful)
    
    # ==================== Personalized Boost Calculation ====================
    
    async def get_personalized_boost(
        self,
        user_id: str,
        restaurant: Dict[str, Any]
    ) -> float:
        """
        Calculate personalized boost score for a restaurant.
        
        Returns a score between 0.0 and 1.0 that boosts ranking.
        Handles cold start, warm start, and hot start scenarios.
        """
        profile = await self.get_or_create_profile(user_id)
        total_searches = profile.get('total_searches', 0)
        
        # Cold start: No personalization
        if total_searches < self.COLD_START_SEARCHES:
            return 0.0
        
        # Get preferences
        prefs = await postgres_manager.get_preferences(user_id)
        if not prefs:
            return 0.0
        
        boost_score = 0.0
        boost_factors = []
        
        # 1. Cuisine matching (40% weight)
        cuisine_boost = await self._calculate_cuisine_boost(
            restaurant, prefs, total_searches
        )
        boost_factors.append(('cuisine', cuisine_boost, 0.40))
        
        # 2. Previous interactions (30% weight)
        interaction_boost = await self._calculate_interaction_boost(
            user_id, restaurant.get('id')
        )
        boost_factors.append(('interaction', interaction_boost, 0.30))
        
        # 3. Price preference (15% weight)
        price_boost = self._calculate_price_boost(restaurant, prefs)
        boost_factors.append(('price', price_boost, 0.15))
        
        # 4. Atmosphere matching (10% weight)
        atmosphere_boost = self._calculate_atmosphere_boost(restaurant, prefs)
        boost_factors.append(('atmosphere', atmosphere_boost, 0.10))
        
        # 5. Distance preference (5% weight)
        distance_boost = self._calculate_distance_boost(restaurant, prefs)
        boost_factors.append(('distance', distance_boost, 0.05))
        
        # Calculate weighted sum
        for factor_name, score, weight in boost_factors:
            boost_score += score * weight
        
        # Apply confidence scaling based on data amount
        confidence = self._calculate_confidence(total_searches)
        boost_score *= confidence
        
        return min(1.0, max(0.0, boost_score))
    
    async def _calculate_cuisine_boost(
        self,
        restaurant: Dict[str, Any],
        prefs: Dict[str, Any],
        total_searches: int
    ) -> float:
        """Calculate boost based on cuisine preferences."""
        # Parse restaurant cuisines
        restaurant_cuisines = []
        food_tags = restaurant.get('food_tags', '')
        
        if isinstance(food_tags, str):
            restaurant_cuisines = [c.strip().lower() for c in food_tags.split(',') if c.strip()]
        elif isinstance(food_tags, list):
            restaurant_cuisines = [c.lower() for c in food_tags]
        
        if not restaurant_cuisines:
            return 0.0
        
        # Get user's cuisine weights
        cuisine_weights = prefs.get('cuisine_weights', {})
        if isinstance(cuisine_weights, str):
            import json
            cuisine_weights = json.loads(cuisine_weights)
        
        if not cuisine_weights:
            return 0.0
        
        # Normalize weights
        max_weight = max(cuisine_weights.values()) if cuisine_weights else 1.0
        
        # Calculate match score
        match_scores = []
        for cuisine in restaurant_cuisines:
            if cuisine in cuisine_weights:
                normalized_weight = cuisine_weights[cuisine] / max_weight
                match_scores.append(normalized_weight)
        
        if not match_scores:
            return 0.0
        
        # Return average match score
        return sum(match_scores) / len(match_scores)
    
    async def _calculate_interaction_boost(
        self,
        user_id: str,
        restaurant_id: Optional[int]
    ) -> float:
        """Calculate boost based on previous interactions."""
        if not restaurant_id:
            return 0.0
        
        # Get recent interactions (last 180 days)
        interactions = await postgres_manager.get_user_interactions(user_id, days=180)
        
        # Find interactions with this restaurant
        restaurant_interactions = [
            i for i in interactions if i['restaurant_id'] == restaurant_id
        ]
        
        if not restaurant_interactions:
            return 0.0
        
        # Calculate weighted score based on interaction types
        total_score = 0.0
        for interaction in restaurant_interactions:
            interaction_type = interaction['interaction_type']
            weight = self.SIGNAL_WEIGHTS.get(interaction_type, 0.5)
            
            # Time decay: older interactions matter less
            age_days = (datetime.now() - interaction['created_at']).days
            decay = np.exp(-age_days / 90)  # 90-day half-life
            
            total_score += weight * decay
        
        # Normalize to 0-1 range (cap at score of 5)
        return min(1.0, total_score / 5.0)
    
    def _calculate_price_boost(
        self,
        restaurant: Dict[str, Any],
        prefs: Dict[str, Any]
    ) -> float:
        """Calculate boost based on price preference."""
        preferred_range = prefs.get('preferred_price_range')
        if not preferred_range:
            return 0.5  # Neutral
        
        restaurant_range = restaurant.get('price_level', '')
        
        # Exact match
        if restaurant_range == preferred_range:
            return 1.0
        
        # Adjacent ranges get partial credit
        price_order = ['$', '$$', '$$$', '$$$$']
        try:
            pref_idx = price_order.index(preferred_range)
            rest_idx = price_order.index(restaurant_range)
            distance = abs(pref_idx - rest_idx)
            
            if distance == 1:
                return 0.7
            elif distance == 2:
                return 0.4
            else:
                return 0.2
        except ValueError:
            return 0.5
    
    def _calculate_atmosphere_boost(
        self,
        restaurant: Dict[str, Any],
        prefs: Dict[str, Any]
    ) -> float:
        """Calculate boost based on atmosphere preferences."""
        favorite_atmospheres = prefs.get('favorite_atmospheres', [])
        if not favorite_atmospheres:
            return 0.5  # Neutral
        
        # Extract restaurant atmospheres from comments/metadata
        restaurant_atmospheres = restaurant.get('atmosphere', [])
        if isinstance(restaurant_atmospheres, str):
            restaurant_atmospheres = [a.strip() for a in restaurant_atmospheres.split(',')]
        
        if not restaurant_atmospheres:
            return 0.5
        
        # Calculate overlap
        matches = len(set(favorite_atmospheres) & set(restaurant_atmospheres))
        if matches > 0:
            return min(1.0, matches / len(favorite_atmospheres))
        
        return 0.3
    
    def _calculate_distance_boost(
        self,
        restaurant: Dict[str, Any],
        prefs: Dict[str, Any]
    ) -> float:
        """Calculate boost based on distance preference."""
        max_typical_distance = prefs.get('max_typical_distance')
        if not max_typical_distance:
            return 0.5  # Neutral
        
        restaurant_distance = restaurant.get('distance')
        if not restaurant_distance:
            return 0.5
        
        # Closer than typical = good
        if restaurant_distance <= max_typical_distance:
            return 1.0
        
        # Further but not too far = OK
        if restaurant_distance <= max_typical_distance * 1.5:
            return 0.7
        
        # Too far = penalty
        return 0.3
    
    def _calculate_confidence(self, total_searches: int) -> float:
        """
        Calculate confidence multiplier based on amount of data.
        
        Cold start (0-3): 0.0 confidence
        Warm start (3-10): 0.3-0.7 confidence
        Hot start (10-30): 0.7-1.0 confidence
        Mature (30+): 1.0 confidence
        """
        if total_searches < self.COLD_START_SEARCHES:
            return 0.0
        elif total_searches < self.WARM_START_SEARCHES:
            # Linear interpolation from 0.3 to 0.7
            progress = (total_searches - self.COLD_START_SEARCHES) / \
                      (self.WARM_START_SEARCHES - self.COLD_START_SEARCHES)
            return 0.3 + progress * 0.4
        elif total_searches < self.HOT_START_SEARCHES:
            # Linear interpolation from 0.7 to 1.0
            progress = (total_searches - self.WARM_START_SEARCHES) / \
                      (self.HOT_START_SEARCHES - self.WARM_START_SEARCHES)
            return 0.7 + progress * 0.3
        else:
            return 1.0
    
    # ==================== Collaborative Filtering ====================
    
    async def get_similar_users(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[str]:
        """Find users with similar preferences (for collaborative filtering)."""
        # Get user's favorite restaurants
        user_favorites = await postgres_manager.get_user_favorite_restaurants(
            user_id, limit=20
        )
        
        if not user_favorites:
            return []
        
        # This is a simplified version
        # In production, use cosine similarity or matrix factorization
        similar_users = []
        
        # TODO: Implement proper collaborative filtering
        # For now, return empty list
        
        return similar_users
    
    # ==================== Analytics & Insights ====================
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get comprehensive user insights."""
        stats = await postgres_manager.get_user_stats(user_id)
        prefs = await postgres_manager.get_preferences(user_id)
        profile = await self.get_or_create_profile(user_id)
        
        # Calculate user stage
        total_searches = profile.get('total_searches', 0)
        if total_searches < self.COLD_START_SEARCHES:
            stage = 'cold_start'
        elif total_searches < self.WARM_START_SEARCHES:
            stage = 'warm_start'
        elif total_searches < self.HOT_START_SEARCHES:
            stage = 'hot_start'
        else:
            stage = 'mature'
        
        return {
            'user_stage': stage,
            'confidence': self._calculate_confidence(total_searches),
            'statistics': stats,
            'preferences': prefs,
            'personalization_strength': 'high' if total_searches >= 30 else 
                                       'medium' if total_searches >= 10 else 
                                       'low' if total_searches >= 3 else 'none'
        }
    
    async def learn_from_feedback(
        self,
        user_id: str,
        restaurant_id: int,
        feedback_type: str,  # 'like', 'dislike', 'report'
        reason: Optional[str] = None
    ):
        """Learn from explicit user feedback."""
        # Record interaction with strong signal
        weight_map = {
            'like': 'explicit_like',
            'dislike': 'dislike',
            'report': 'dislike'
        }
        
        interaction_type = weight_map.get(feedback_type, feedback_type)
        
        await self.record_restaurant_interaction(
            user_id,
            restaurant_id,
            interaction_type,
            context={'reason': reason} if reason else None
        )


# Global instance
advanced_profile_manager = AdvancedUserProfileManager()
