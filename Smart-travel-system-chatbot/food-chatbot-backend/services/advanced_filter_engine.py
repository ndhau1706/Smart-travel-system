"""
Advanced Filter Logic with Fuzzy Matching and Semantic Similarity
Fixes overly aggressive filtering while maintaining relevance.
"""
from typing import List, Dict, Any, Set, Optional
from thefuzz import fuzz, process
import re
from collections import Counter


class AdvancedFilterEngine:
    """
    Intelligent filtering with:
    - Fuzzy matching for typos and variations
    - Semantic similarity for cuisine matching
    - Soft filtering (scoring instead of hard cuts)
    - Context-aware filtering
    """
    
    def __init__(self):
        # Fuzzy matching threshold
        self.FUZZY_THRESHOLD = 70  # 70% similarity
        
        # Cuisine mapping for semantic matching
        self.CUISINE_ALIASES = {
            'phở': ['pho', 'phở bò', 'phở gà', 'vietnamese noodle'],
            'bún': ['bun', 'vermicelli', 'noodle'],
            'cơm': ['com', 'rice', 'cơm tấm', 'broken rice'],
            'bánh mì': ['banh mi', 'sandwich', 'bánh mỳ'],
            'sushi': ['japanese', 'nhật', 'nhật bản', 'sashimi'],
            'pizza': ['italian', 'ý', 'pasta'],
            'burger': ['hamburger', 'american', 'mỹ'],
            'bbq': ['nướng', 'grilled', 'barbecue'],
            'lẩu': ['lau', 'hotpot', 'hot pot'],
            'dimsum': ['dim sum', 'chinese', 'trung hoa', 'hoa'],
            'korean': ['hàn quốc', 'hàn', 'korea'],
            'thai': ['thái', 'thái lan', 'thailand'],
        }
        
        # Atmosphere/vibe mappings
        self.ATMOSPHERE_ALIASES = {
            'romantic': ['lãng mạn', 'date', 'hẹn hò', 'cozy', 'intimate'],
            'family': ['gia đình', 'family-friendly', 'kids'],
            'business': ['công sở', 'formal', 'professional'],
            'casual': ['bình dân', 'giản dị', 'informal'],
            'luxury': ['sang trọng', 'cao cấp', 'upscale', 'fine dining'],
            'view': ['view đẹp', 'scenic', 'rooftop', 'tầng cao'],
            'quiet': ['yên tĩnh', 'peaceful', 'calm'],
            'lively': ['sôi động', 'vibrant', 'busy', 'crowded'],
        }
        
        # Price level mappings
        self.PRICE_MAPPINGS = {
            'rẻ': '$',
            'giá rẻ': '$',
            'bình dân': '$',
            'cheap': '$',
            'budget': '$',
            'vừa phải': '$$',
            'trung bình': '$$',
            'moderate': '$$',
            'đắt': '$$$',
            'cao cấp': '$$$',
            'expensive': '$$$',
            'sang trọng': '$$$$',
            'very expensive': '$$$$',
            'luxury': '$$$$',
        }
    
    def apply_smart_filters(
        self,
        restaurants: List[Dict[str, Any]],
        filters: Dict[str, Any],
        use_soft_filtering: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Apply intelligent filters with fuzzy matching.
        
        Args:
            restaurants: List of restaurants
            filters: Filter criteria
            use_soft_filtering: If True, use scoring; if False, use hard filtering
            
        Returns:
            Filtered/scored restaurants
        """
        if not filters:
            return restaurants
        
        filtered = []
        
        for restaurant in restaurants:
            if use_soft_filtering:
                # Soft filtering: assign filter match score
                filter_score = self._calculate_filter_score(restaurant, filters)
                restaurant['filter_match_score'] = filter_score
                
                # Only exclude if score is too low (<0.2)
                if filter_score >= 0.2:
                    filtered.append(restaurant)
            else:
                # Hard filtering: strict matching
                if self._matches_filters(restaurant, filters):
                    restaurant['filter_match_score'] = 1.0
                    filtered.append(restaurant)
        
        return filtered
    
    def _calculate_filter_score(
        self,
        restaurant: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> float:
        """
        Calculate how well a restaurant matches filters (0.0 to 1.0).
        
        Uses fuzzy matching and semantic similarity.
        """
        scores = []
        weights = []
        
        # Cuisine filter
        if filters.get('cuisines'):
            cuisine_score = self._match_cuisines_fuzzy(
                restaurant,
                filters['cuisines']
            )
            scores.append(cuisine_score)
            weights.append(0.35)  # High weight
        
        # Price filter
        if filters.get('price_level') or filters.get('max_budget'):
            price_score = self._match_price_flexible(
                restaurant,
                filters.get('price_level'),
                filters.get('max_budget')
            )
            scores.append(price_score)
            weights.append(0.25)
        
        # Atmosphere filter
        if filters.get('atmosphere'):
            atmosphere_score = self._match_atmosphere_fuzzy(
                restaurant,
                filters['atmosphere']
            )
            scores.append(atmosphere_score)
            weights.append(0.20)
        
        # Rating filter
        if filters.get('min_rating'):
            rating_score = self._match_rating_soft(
                restaurant,
                filters['min_rating']
            )
            scores.append(rating_score)
            weights.append(0.10)
        
        # Distance filter
        if filters.get('max_distance'):
            distance_score = self._match_distance_soft(
                restaurant,
                filters['max_distance']
            )
            scores.append(distance_score)
            weights.append(0.10)
        
        # Calculate weighted average
        if not scores:
            return 1.0  # No filters applied
        
        total_weight = sum(weights)
        weighted_score = sum(s * w for s, w in zip(scores, weights)) / total_weight
        
        return weighted_score
    
    def _match_cuisines_fuzzy(
        self,
        restaurant: Dict[str, Any],
        target_cuisines: List[str]
    ) -> float:
        """
        Match cuisines with fuzzy matching and semantic similarity.
        
        Returns score 0.0-1.0 based on match quality.
        """
        # Extract restaurant cuisines
        restaurant_cuisines = []
        food_tags = restaurant.get('food_tags', [])
        
        if isinstance(food_tags, str):
            import json
            try:
                food_tags = json.loads(food_tags)
            except:
                food_tags = [food_tags] if food_tags else []
        
        if isinstance(food_tags, list):
            restaurant_cuisines = [c.lower().strip() for c in food_tags if c]
        
        # Add category
        if restaurant.get('category'):
            restaurant_cuisines.append(restaurant['category'].lower().strip())
        
        if not restaurant_cuisines:
            return 0.3  # Neutral score for missing data
        
        # Check each target cuisine
        match_scores = []
        
        for target_cuisine in target_cuisines:
            target_lower = target_cuisine.lower().strip()
            best_match_score = 0.0
            
            # 1. Check exact matches
            for rest_cuisine in restaurant_cuisines:
                if target_lower == rest_cuisine:
                    best_match_score = 1.0
                    break
                
                # 2. Check substring matches
                if target_lower in rest_cuisine or rest_cuisine in target_lower:
                    best_match_score = max(best_match_score, 0.9)
                
                # 3. Check fuzzy matches
                fuzzy_score = fuzz.ratio(target_lower, rest_cuisine) / 100.0
                if fuzzy_score >= self.FUZZY_THRESHOLD / 100.0:
                    best_match_score = max(best_match_score, fuzzy_score)
                
                # 4. Check semantic aliases
                alias_score = self._check_cuisine_aliases(target_lower, rest_cuisine)
                best_match_score = max(best_match_score, alias_score)
            
            match_scores.append(best_match_score)
        
        # Return average match score
        if match_scores:
            return sum(match_scores) / len(match_scores)
        
        return 0.3
    
    def _check_cuisine_aliases(self, target: str, restaurant_cuisine: str) -> float:
        """Check if cuisines are semantically similar using aliases."""
        for main_cuisine, aliases in self.CUISINE_ALIASES.items():
            target_matches = (target == main_cuisine or 
                            target in aliases or
                            any(alias in target for alias in aliases))
            
            rest_matches = (restaurant_cuisine == main_cuisine or
                          restaurant_cuisine in aliases or
                          any(alias in restaurant_cuisine for alias in aliases))
            
            if target_matches and rest_matches:
                return 0.85  # High score for semantic match
        
        return 0.0
    
    def _match_price_flexible(
        self,
        restaurant: Dict[str, Any],
        target_price_level: Optional[str],
        max_budget: Optional[int]
    ) -> float:
        """
        Match price with flexibility.
        
        Allows ±1 price level for partial match.
        """
        restaurant_price = restaurant.get('price_level', '')
        
        if not restaurant_price:
            return 0.5  # Neutral for missing data
        
        price_order = ['$', '$$', '$$$', '$$$$']
        
        # Check price level match
        if target_price_level:
            if restaurant_price == target_price_level:
                return 1.0
            
            try:
                target_idx = price_order.index(target_price_level)
                rest_idx = price_order.index(restaurant_price)
                
                diff = abs(target_idx - rest_idx)
                if diff == 0:
                    return 1.0
                elif diff == 1:
                    return 0.7  # Adjacent level
                elif diff == 2:
                    return 0.4
                else:
                    return 0.2
            except ValueError:
                pass
        
        # Check budget match (estimated prices)
        if max_budget:
            estimated_avg_price = self._estimate_restaurant_price(restaurant_price)
            
            if estimated_avg_price <= max_budget:
                return 1.0
            elif estimated_avg_price <= max_budget * 1.2:
                return 0.8  # Within 20%
            elif estimated_avg_price <= max_budget * 1.5:
                return 0.5  # Within 50%
            else:
                return 0.2  # Too expensive
        
        return 0.5
    
    def _estimate_restaurant_price(self, price_level: str) -> int:
        """Estimate average meal price from price level."""
        price_estimates = {
            '$': 70000,      # ~70k VND
            '$$': 150000,    # ~150k VND
            '$$$': 300000,   # ~300k VND
            '$$$$': 600000,  # ~600k VND
        }
        return price_estimates.get(price_level, 150000)
    
    def _match_atmosphere_fuzzy(
        self,
        restaurant: Dict[str, Any],
        target_atmospheres: List[str]
    ) -> float:
        """Match atmosphere with fuzzy matching."""
        # Extract restaurant atmosphere from comments/description
        restaurant_text = ' '.join([
            restaurant.get('comments', ''),
            restaurant.get('location_summary', ''),
            str(restaurant.get('atmosphere', []))
        ]).lower()
        
        match_scores = []
        
        for target_atmo in target_atmospheres:
            target_lower = target_atmo.lower().strip()
            
            # Check direct mention
            if target_lower in restaurant_text:
                match_scores.append(1.0)
                continue
            
            # Check aliases
            best_alias_score = 0.0
            for main_atmo, aliases in self.ATMOSPHERE_ALIASES.items():
                target_matches = target_lower == main_atmo or target_lower in aliases
                
                if target_matches:
                    # Check if any alias appears in restaurant text
                    for alias in [main_atmo] + aliases:
                        if alias in restaurant_text:
                            best_alias_score = 0.85
                            break
            
            match_scores.append(best_alias_score)
        
        return sum(match_scores) / len(match_scores) if match_scores else 0.5
    
    def _match_rating_soft(self, restaurant: Dict[str, Any], min_rating: float) -> float:
        """Soft rating match with tolerance. Bug 14 Fix: Handle missing ratings."""
        rating = restaurant.get('rating')
        
        # Bug 14 Fix: Handle missing/null ratings with neutral score
        if rating is None or rating == 0:
            return 0.5  # Neutral - don't exclude new restaurants
        
        if rating >= min_rating:
            return 1.0
        elif rating >= min_rating - 0.3:
            return 0.8  # Close match
        elif rating >= min_rating - 0.5:
            return 0.6  # Acceptable
        else:
            return 0.3  # Below threshold
    
    def _match_distance_soft(
        self,
        restaurant: Dict[str, Any],
        max_distance: float
    ) -> float:
        """Soft distance match with tolerance."""
        distance = restaurant.get('distance')
        
        if distance is None:
            return 0.5  # Unknown distance
        
        if distance <= max_distance:
            return 1.0
        elif distance <= max_distance * 1.2:
            return 0.8  # Within 20%
        elif distance <= max_distance * 1.5:
            return 0.5  # Within 50%
        else:
            return 0.2  # Too far
    
    def _matches_filters(
        self,
        restaurant: Dict[str, Any],
        filters: Dict[str, Any]
    ) -> bool:
        """Hard filtering: strict boolean match."""
        # Cuisine match
        if filters.get('cuisines'):
            if self._match_cuisines_fuzzy(restaurant, filters['cuisines']) < 0.7:
                return False
        
        # Price match
        if filters.get('max_budget'):
            price_level = restaurant.get('price_level')
            estimated_price = self._estimate_restaurant_price(price_level)
            if estimated_price > filters['max_budget']:
                return False
        
        # Rating match
        if filters.get('min_rating'):
            if restaurant.get('rating', 0) < filters['min_rating']:
                return False
        
        # Distance match
        if filters.get('max_distance'):
            distance = restaurant.get('distance')
            if distance and distance > filters['max_distance']:
                return False
        
        return True


# Global instance
advanced_filter_engine = AdvancedFilterEngine()
