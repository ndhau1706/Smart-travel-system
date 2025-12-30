"""
User Profile & Preference Learning
Learns user preferences over time and personalizes recommendations
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from collections import Counter


class UserProfileManager:
    """Manage user profiles and learn preferences."""
    
    def __init__(self):
        # In-memory storage (in production, use Redis or database)
        self.profiles = {}
        self.profile_ttl = timedelta(days=90)  # Keep profiles for 90 days
    
    def get_or_create_profile(self, user_id: str) -> Dict[str, Any]:
        """Get existing profile or create new one."""
        if user_id not in self.profiles:
            self.profiles[user_id] = self._create_default_profile(user_id)
        
        # Update last active
        self.profiles[user_id]['last_active'] = datetime.now().isoformat()
        
        return self.profiles[user_id]
    
    def _create_default_profile(self, user_id: str) -> Dict[str, Any]:
        """Create default profile structure."""
        return {
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_active': datetime.now().isoformat(),
            'preferences': {
                'favorite_cuisines': [],  # Most frequently searched
                'favorite_price_range': None,  # Most common price range
                'preferred_distance': None,  # Average max distance
                'preferred_rating': None,  # Minimum rating threshold
                'favorite_atmosphere': [],  # Preferred vibes
                'dietary_restrictions': [],  # Vegetarian, halal, etc.
            },
            'search_history': {
                'cuisine_counts': {},  # {cuisine: count}
                'price_range_counts': {},  # {range: count}
                'location_searches': [],  # Recent locations
                'atmosphere_counts': {},  # {atmosphere: count}
            },
            'interaction_history': {
                'total_searches': 0,
                'restaurants_viewed': [],  # Recent restaurant IDs
                'restaurants_clicked': [],  # Restaurant IDs user showed interest in
                'successful_searches': 0,  # Searches that resulted in clicks
            },
            'learned_patterns': {
                'typical_budget': None,  # Inferred from searches
                'time_preferences': {},  # When user typically searches
                'group_size_typical': None,  # Typical party size
            }
        }
    
    def update_from_search(
        self, 
        user_id: str,
        query: str,
        params: Dict[str, Any],
        restaurants_returned: List[Dict[str, Any]]
    ):
        """Update profile based on search behavior."""
        profile = self.get_or_create_profile(user_id)
        
        # Update search count
        profile['interaction_history']['total_searches'] += 1
        
        # Update cuisine preferences
        if params.get('cuisines'):
            for cuisine in params['cuisines']:
                cuisine_lower = cuisine.lower()
                profile['search_history']['cuisine_counts'][cuisine_lower] = \
                    profile['search_history']['cuisine_counts'].get(cuisine_lower, 0) + 1
        
        # Update price range preferences
        if params.get('max_budget'):
            budget = params['max_budget']
            range_key = self._get_price_range_key(budget)
            profile['search_history']['price_range_counts'][range_key] = \
                profile['search_history']['price_range_counts'].get(range_key, 0) + 1
        
        # Update distance preferences
        if params.get('max_distance'):
            distances = profile.get('_temp_distances', [])
            distances.append(params['max_distance'])
            profile['_temp_distances'] = distances[-20:]  # Keep last 20
        
        # Update atmosphere preferences
        if params.get('atmosphere'):
            for atmo in params['atmosphere']:
                profile['search_history']['atmosphere_counts'][atmo] = \
                    profile['search_history']['atmosphere_counts'].get(atmo, 0) + 1
        
        # Learn patterns
        self._update_learned_patterns(profile)
        
        self.profiles[user_id] = profile
    
    def update_from_interaction(
        self,
        user_id: str,
        restaurant_id: int,
        action: str  # 'view', 'click', 'book'
    ):
        """Update profile based on user interaction with restaurants."""
        profile = self.get_or_create_profile(user_id)
        
        if action == 'view':
            if restaurant_id not in profile['interaction_history']['restaurants_viewed']:
                profile['interaction_history']['restaurants_viewed'].append(restaurant_id)
                # Keep last 50
                profile['interaction_history']['restaurants_viewed'] = \
                    profile['interaction_history']['restaurants_viewed'][-50:]
        
        elif action == 'click':
            if restaurant_id not in profile['interaction_history']['restaurants_clicked']:
                profile['interaction_history']['restaurants_clicked'].append(restaurant_id)
                profile['interaction_history']['successful_searches'] += 1
                # Keep last 30
                profile['interaction_history']['restaurants_clicked'] = \
                    profile['interaction_history']['restaurants_clicked'][-30:]
        
        self.profiles[user_id] = profile
    
    def _update_learned_patterns(self, profile: Dict[str, Any]):
        """Update learned patterns from accumulated data."""
        # Learn favorite cuisines (top 3)
        cuisine_counts = profile['search_history']['cuisine_counts']
        if cuisine_counts:
            top_cuisines = sorted(
                cuisine_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:3]
            profile['preferences']['favorite_cuisines'] = [c[0] for c in top_cuisines]
        
        # Learn typical budget
        price_counts = profile['search_history']['price_range_counts']
        if price_counts:
            most_common_range = max(price_counts.items(), key=lambda x: x[1])[0]
            profile['preferences']['favorite_price_range'] = most_common_range
            profile['learned_patterns']['typical_budget'] = self._range_to_budget(most_common_range)
        
        # Learn preferred distance
        distances = profile.get('_temp_distances', [])
        if distances:
            avg_distance = sum(distances) / len(distances)
            profile['preferences']['preferred_distance'] = round(avg_distance, 1)
        
        # Learn favorite atmosphere
        atmo_counts = profile['search_history']['atmosphere_counts']
        if atmo_counts:
            top_atmos = sorted(
                atmo_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:2]
            profile['preferences']['favorite_atmosphere'] = [a[0] for a in top_atmos]
    
    def get_personalized_boost(
        self, 
        user_id: str,
        restaurant: Dict[str, Any]
    ) -> float:
        """
        Calculate personalization boost score for a restaurant.
        FIXED: Proper boost calculation with defaults.
        
        Args:
            user_id: User ID
            restaurant: Restaurant data
            
        Returns:
            Boost score (0.0 to 1.0)
        """
        if user_id not in self.profiles:
            return 0.0
        
        profile = self.profiles[user_id]
        
        # FIXED: Check if profile has enough data
        total_searches = profile['interaction_history'].get('total_searches', 0)
        if total_searches < 3:
            # Not enough data for personalization
            return 0.0
        
        boost = 0.0
        
        # Cuisine match (+0.3)
        favorite_cuisines = profile['preferences'].get('favorite_cuisines', [])
        if favorite_cuisines:
            # FIXED: Handle food_tags as string or list
            food_tags = restaurant.get('food_tags', [])
            if isinstance(food_tags, str):
                import json
                try:
                    food_tags = json.loads(food_tags)
                except:
                    food_tags = []
            restaurant_tags = [str(tag).lower() for tag in food_tags]
            if any(cuisine in restaurant_tags for cuisine in favorite_cuisines):
                boost += 0.3
        
        # Price match (+0.2)
        favorite_range = profile['preferences'].get('favorite_price_range')
        if favorite_range:
            restaurant_price = self._get_price_range_key(
                self._estimate_price(restaurant)
            )
            if restaurant_price == favorite_range:
                boost += 0.2
        
        # Previously clicked (+0.3)
        if restaurant.get('id') in profile['interaction_history']['restaurants_clicked']:
            boost += 0.3
        
        # Distance preference (+0.2)
        preferred_distance = profile['preferences']['preferred_distance']
        restaurant_distance = restaurant.get('distance')
        if preferred_distance and restaurant_distance:
            if restaurant_distance <= preferred_distance:
                boost += 0.2
        
        return min(boost, 1.0)  # Cap at 1.0
    
    def get_personalized_suggestions(
        self,
        user_id: str,
        language: str = 'vi'
    ) -> Optional[str]:
        """
        Generate personalized suggestions based on user history.
        
        Args:
            user_id: User ID
            language: Response language
            
        Returns:
            Suggestion message or None
        """
        if user_id not in self.profiles:
            return None
        
        profile = self.profiles[user_id]
        
        # Need at least 3 searches to personalize
        if profile['interaction_history']['total_searches'] < 3:
            return None
        
        favorite_cuisines = profile['preferences']['favorite_cuisines']
        favorite_range = profile['preferences']['favorite_price_range']
        
        if not favorite_cuisines:
            return None
        
        if language == 'vi':
            cuisines_str = ', '.join(favorite_cuisines[:2])
            msg = f"💡 **Gợi ý cá nhân hóa**: Dựa trên lịch sử tìm kiếm, bạn thường thích món **{cuisines_str}**"
            
            if favorite_range:
                range_text = {
                    'budget': 'giá rẻ',
                    'moderate': 'giá trung bình',
                    'upscale': 'cao cấp'
                }.get(favorite_range, '')
                msg += f" và **{range_text}**"
            
            msg += ". Tôi đã ưu tiên những quán phù hợp với sở thích này! 😊"
        else:
            cuisines_str = ', '.join(favorite_cuisines[:2])
            msg = f"💡 **Personalized**: Based on your history, you often prefer **{cuisines_str}**"
            
            if favorite_range:
                range_text = {
                    'budget': 'budget-friendly',
                    'moderate': 'moderate pricing',
                    'upscale': 'upscale'
                }.get(favorite_range, '')
                msg += f" and **{range_text}** options"
            
            msg += ". I've prioritized restaurants matching your taste! 😊"
        
        return msg
    
    def _get_price_range_key(self, budget: int) -> str:
        """Convert budget to range key."""
        if budget < 100000:
            return 'budget'
        elif budget < 300000:
            return 'moderate'
        else:
            return 'upscale'
    
    def _range_to_budget(self, range_key: str) -> int:
        """Convert range key to budget."""
        return {
            'budget': 75000,
            'moderate': 150000,
            'upscale': 400000
        }.get(range_key, 150000)
    
    def _estimate_price(self, restaurant: Dict[str, Any]) -> float:
        """FIXED: More accurate price estimation from price_level."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': 50000,      # 30-70k
            'PRICE_LEVEL_MODERATE': 120000,        # 80-160k
            'PRICE_LEVEL_EXPENSIVE': 250000,       # 180-320k
            'PRICE_LEVEL_VERY_EXPENSIVE': 500000   # 400k+
        }
        return price_map.get(restaurant.get('price_level', ''), 120000)


# Global instance
user_profile_manager = UserProfileManager()
