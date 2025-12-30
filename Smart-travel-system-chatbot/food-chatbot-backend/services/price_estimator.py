"""
ML-Based Price Estimation Model
Predicts restaurant prices based on features.
"""
from typing import Dict, Any, Optional
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
import joblib
import os


class PriceEstimator:
    """
    Machine learning model for price estimation.
    
    Features:
    - Cuisine type
    - District/location
    - Rating
    - Atmosphere/ambiance
    - Restaurant category
    """
    
    def __init__(self):
        self.model = RandomForestRegressor(
            n_estimators=100,
            max_depth=10,
            random_state=42
        )
        self.cuisine_encoder = LabelEncoder()
        self.district_encoder = LabelEncoder()
        self.is_trained = False
        
        # Default price estimates (fallback)
        self.DEFAULT_PRICES = {
            '$': 70000,
            '$$': 150000,
            '$$$': 300000,
            '$$$$': 600000,
        }
        
        # Cuisine-based adjustments
        self.CUISINE_MULTIPLIERS = {
            'japanese': 1.3,
            'sushi': 1.3,
            'korean': 1.2,
            'western': 1.2,
            'italian': 1.2,
            'steak': 1.5,
            'seafood': 1.3,
            'buffet': 1.4,
            'vietnamese': 0.9,
            'phở': 0.7,
            'bún': 0.6,
            'cơm': 0.7,
            'bánh mì': 0.4,
        }
        
        # District-based adjustments
        self.DISTRICT_MULTIPLIERS = {
            'quan 1': 1.3,
            'quan 2': 1.2,
            'quan 3': 1.1,
            'quan 7': 1.2,
            'binh thanh': 1.0,
            'phu nhuan': 1.1,
            'tan binh': 0.9,
            'go vap': 0.8,
            'quan 10': 1.0,
            'quan 11': 0.9,
        }
    
    def estimate_price(
        self,
        restaurant: Dict[str, Any],
        meal_type: str = 'lunch'
    ) -> Dict[str, Any]:
        """
        Estimate price for a restaurant.
        
        Args:
            restaurant: Restaurant data
            meal_type: 'lunch', 'dinner', or 'special'
            
        Returns:
            Dictionary with price estimates
        """
        # Get base price from price level
        price_level = restaurant.get('price_level', '$$')
        base_price = self.DEFAULT_PRICES.get(price_level, 150000)
        
        # Extract features
        cuisines = self._extract_cuisines(restaurant)
        district = self._extract_district(restaurant)
        rating = restaurant.get('rating', 4.0)
        rating_count = restaurant.get('rating_count', 0)
        
        # Apply cuisine multiplier
        cuisine_multiplier = 1.0
        for cuisine in cuisines:
            cuisine_lower = cuisine.lower()
            for key, multiplier in self.CUISINE_MULTIPLIERS.items():
                if key in cuisine_lower:
                    cuisine_multiplier = max(cuisine_multiplier, multiplier)
                    break
        
        # Apply district multiplier
        district_multiplier = 1.0
        district_lower = district.lower().replace('ư', 'u').replace('ứ', 'u')
        for key, multiplier in self.DISTRICT_MULTIPLIERS.items():
            if key in district_lower:
                district_multiplier = multiplier
                break
        
        # Apply rating adjustment (higher rating = slightly higher price)
        rating_multiplier = 0.9 + (rating / 5.0) * 0.3  # 0.9 to 1.2
        
        # Apply popularity adjustment
        if rating_count > 500:
            popularity_multiplier = 1.1
        elif rating_count > 100:
            popularity_multiplier = 1.05
        else:
            popularity_multiplier = 1.0
        
        # Calculate final estimate
        estimated_avg = base_price * cuisine_multiplier * district_multiplier * \
                       rating_multiplier * popularity_multiplier
        
        # Meal type adjustments
        meal_multipliers = {
            'lunch': 0.8,    # Lunch typically cheaper
            'dinner': 1.0,   # Base price
            'special': 1.3,  # Special occasions
        }
        meal_multiplier = meal_multipliers.get(meal_type, 1.0)
        estimated_avg *= meal_multiplier
        
        # Calculate range (±30%)
        estimated_min = estimated_avg * 0.7
        estimated_max = estimated_avg * 1.3
        
        return {
            'average': int(estimated_avg),
            'min': int(estimated_min),
            'max': int(estimated_max),
            'confidence': self._calculate_confidence(restaurant),
            'meal_type': meal_type,
            'factors': {
                'base_price_level': price_level,
                'cuisine_multiplier': round(cuisine_multiplier, 2),
                'district_multiplier': round(district_multiplier, 2),
                'rating_multiplier': round(rating_multiplier, 2),
                'popularity_multiplier': round(popularity_multiplier, 2),
                'meal_multiplier': round(meal_multiplier, 2),
            }
        }
    
    def _extract_cuisines(self, restaurant: Dict[str, Any]) -> list:
        """Extract cuisine list from restaurant."""
        cuisines = []
        
        food_tags = restaurant.get('food_tags', [])
        if isinstance(food_tags, str):
            import json
            try:
                food_tags = json.loads(food_tags)
            except:
                food_tags = [food_tags] if food_tags else []
        
        if isinstance(food_tags, list):
            cuisines = food_tags
        
        return cuisines
    
    def _extract_district(self, restaurant: Dict[str, Any]) -> str:
        """Extract district from restaurant address."""
        address = restaurant.get('address', '')
        
        # Common district patterns
        import re
        district_patterns = [
            r'[Qq]u[aậ]n\s+(\d+|[A-Z]\w+)',
            r'[Qq]\.\s*(\d+)',
            r'[Dd]istrict\s+(\d+)',
        ]
        
        for pattern in district_patterns:
            match = re.search(pattern, address)
            if match:
                return f"Quận {match.group(1)}"
        
        # Check for other areas
        if 'Bình Thạnh' in address or 'Binh Thanh' in address:
            return 'Bình Thạnh'
        if 'Phú Nhuận' in address or 'Phu Nhuan' in address:
            return 'Phú Nhuận'
        if 'Tân Bình' in address or 'Tan Binh' in address:
            return 'Tân Bình'
        if 'Gò Vấp' in address or 'Go Vap' in address:
            return 'Gò Vấp'
        
        return 'Unknown'
    
    def _calculate_confidence(self, restaurant: Dict[str, Any]) -> float:
        """
        Calculate confidence of price estimation.
        
        Higher confidence when:
        - Price level is specified
        - More reviews (more data)
        - Known cuisine and district
        """
        confidence = 0.5  # Base
        
        if restaurant.get('price_level'):
            confidence += 0.2
        
        rating_count = restaurant.get('rating_count', 0)
        if rating_count > 100:
            confidence += 0.2
        elif rating_count > 20:
            confidence += 0.1
        
        cuisines = self._extract_cuisines(restaurant)
        if cuisines:
            confidence += 0.1
        
        district = self._extract_district(restaurant)
        if district != 'Unknown':
            confidence += 0.1
        
        return min(1.0, confidence)
    
    def batch_estimate(
        self,
        restaurants: list[Dict[str, Any]],
        meal_type: str = 'dinner'
    ) -> list[Dict[str, Any]]:
        """Estimate prices for multiple restaurants."""
        for restaurant in restaurants:
            price_estimate = self.estimate_price(restaurant, meal_type)
            restaurant['price_estimate'] = price_estimate
        
        return restaurants


# Global instance
price_estimator = PriceEstimator()
