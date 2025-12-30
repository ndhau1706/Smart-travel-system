"""
Restaurant data validator - BUG #21 FIX

Validates restaurant data from database to prevent:
- None/NULL values in critical fields
- Invalid data types
- Out-of-range values (rating=-1, etc.)
- XSS payloads in text fields
- Malformed JSON arrays
- Invalid coordinates
- Price level violations
"""
import re
import logging
from typing import Dict, Any, Optional, List
import html

logger = logging.getLogger(__name__)


class RestaurantValidator:
    """Validates and sanitizes restaurant data from database."""
    
    # Allowed rating range
    MIN_RATING = 0.0
    MAX_RATING = 5.0
    
    # Allowed rating count range
    MIN_RATING_COUNT = 0
    MAX_RATING_COUNT = 1_000_000
    
    # Allowed price levels
    VALID_PRICE_LEVELS = {'Rẻ', 'Trung bình', 'Cao', 'Sang trọng', None}
    
    # Allowed coordinate ranges (Vietnam bounds with buffer)
    MIN_LATITUDE = 8.0
    MAX_LATITUDE = 24.0
    MIN_LONGITUDE = 102.0
    MAX_LONGITUDE = 110.0
    
    # Max string lengths (prevent overflow)
    MAX_NAME_LENGTH = 500
    MAX_ADDRESS_LENGTH = 1000
    MAX_PHONE_LENGTH = 50
    MAX_WEBSITE_LENGTH = 500
    MAX_DESCRIPTION_LENGTH = 5000
    
    # XSS detection patterns
    XSS_PATTERNS = [
        r'<script[^>]*>',
        r'javascript:',
        r'onerror\s*=',
        r'onload\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<embed[^>]*>',
        r'<object[^>]*>',
    ]
    
    @classmethod
    def validate_restaurant(cls, restaurant: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Validate and sanitize restaurant data.
        
        Args:
            restaurant: Raw restaurant dict from database
            
        Returns:
            Validated and sanitized restaurant dict, or None if validation fails critically
        """
        try:
            validated = {}
            
            # CRITICAL: ID must exist and be valid
            if not restaurant.get('id'):
                logger.error(f"❌ Restaurant missing ID: {restaurant}")
                return None
            validated['id'] = restaurant['id']
            
            # CRITICAL: Name must exist and be non-empty
            name = restaurant.get('name')
            if not name or not isinstance(name, str) or not name.strip():
                logger.error(f"❌ Restaurant {validated['id']} has invalid name: {name}")
                return None
            
            # Sanitize name (remove XSS, truncate)
            validated['name'] = cls._sanitize_text(name, cls.MAX_NAME_LENGTH)
            
            # Rating validation
            rating = restaurant.get('rating')
            if rating is None:
                validated['rating'] = 0.0  # Default for new restaurants
            elif not isinstance(rating, (int, float)):
                logger.warning(f"⚠️  Restaurant {validated['id']} has non-numeric rating: {rating}")
                validated['rating'] = 0.0
            elif rating < cls.MIN_RATING or rating > cls.MAX_RATING:
                logger.warning(f"⚠️  Restaurant {validated['id']} has out-of-range rating: {rating}")
                validated['rating'] = max(cls.MIN_RATING, min(cls.MAX_RATING, float(rating)))
            else:
                validated['rating'] = float(rating)
            
            # Rating count validation
            rating_count = restaurant.get('rating_count', 0)
            if not isinstance(rating_count, int):
                try:
                    rating_count = int(rating_count)
                except (ValueError, TypeError):
                    logger.warning(f"⚠️  Restaurant {validated['id']} has invalid rating_count: {rating_count}")
                    rating_count = 0
            
            if rating_count < cls.MIN_RATING_COUNT or rating_count > cls.MAX_RATING_COUNT:
                logger.warning(f"⚠️  Restaurant {validated['id']} has out-of-range rating_count: {rating_count}")
                rating_count = max(cls.MIN_RATING_COUNT, min(cls.MAX_RATING_COUNT, rating_count))
            
            validated['rating_count'] = rating_count
            
            # Address validation
            address = restaurant.get('address')
            if address and isinstance(address, str):
                validated['address'] = cls._sanitize_text(address, cls.MAX_ADDRESS_LENGTH)
            else:
                validated['address'] = ''
                logger.warning(f"⚠️  Restaurant {validated['id']} has invalid address: {address}")
            
            # Phone validation
            phone = restaurant.get('phone')
            if phone and isinstance(phone, str):
                validated['phone'] = cls._sanitize_text(phone, cls.MAX_PHONE_LENGTH)
            else:
                validated['phone'] = ''
            
            # Website validation
            website = restaurant.get('website')
            if website and isinstance(website, str):
                # Additional check for javascript: protocol (XSS)
                if website.strip().lower().startswith('javascript:'):
                    logger.warning(f"⚠️  Restaurant {validated['id']} has javascript: in website")
                    validated['website'] = ''
                else:
                    validated['website'] = cls._sanitize_text(website, cls.MAX_WEBSITE_LENGTH)
            else:
                validated['website'] = ''
            
            # Coordinates validation
            coordinates_lat = restaurant.get('coordinates_lat')
            coordinates_lng = restaurant.get('coordinates_lng')
            
            validated['coordinates_lat'] = cls._validate_coordinate(
                coordinates_lat, cls.MIN_LATITUDE, cls.MAX_LATITUDE, validated['id'], 'latitude'
            )
            validated['coordinates_lng'] = cls._validate_coordinate(
                coordinates_lng, cls.MIN_LONGITUDE, cls.MAX_LONGITUDE, validated['id'], 'longitude'
            )
            
            # Price level validation
            price_level = restaurant.get('price_level')
            if price_level not in cls.VALID_PRICE_LEVELS:
                logger.warning(f"⚠️  Restaurant {validated['id']} has invalid price_level: {price_level}")
                validated['price_level'] = None
            else:
                validated['price_level'] = price_level
            
            # Food tags validation (array field)
            food_tags = restaurant.get('food_tags')
            validated['food_tags'] = cls._validate_array_field(food_tags, validated['id'], 'food_tags')
            
            # Comments validation (array field)
            comments = restaurant.get('comments')
            validated['comments'] = cls._validate_array_field(comments, validated['id'], 'comments')
            
            # Description validation
            description = restaurant.get('description')
            if description and isinstance(description, str):
                validated['description'] = cls._sanitize_text(description, cls.MAX_DESCRIPTION_LENGTH)
            else:
                validated['description'] = ''
            
            # Copy over other fields that don't need special validation
            for key in restaurant:
                if key not in validated:
                    validated[key] = restaurant[key]
            
            return validated
            
        except Exception as e:
            logger.error(f"❌ Failed to validate restaurant {restaurant.get('id', 'UNKNOWN')}: {type(e).__name__}: {e}")
            return None
    
    @classmethod
    def _sanitize_text(cls, text: str, max_length: int) -> str:
        """
        Sanitize text field: escape HTML, remove XSS patterns, truncate.
        
        Args:
            text: Input text
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text
        """
        if not text:
            return ''
        
        # Truncate to max length
        text = text[:max_length]
        
        # Check for XSS patterns
        for pattern in cls.XSS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                logger.warning(f"⚠️  XSS pattern detected in text: {pattern}")
                # Escape HTML entities
                text = html.escape(text)
                break
        
        return text.strip()
    
    @classmethod
    def _validate_coordinate(
        cls,
        value: Any,
        min_val: float,
        max_val: float,
        restaurant_id: Any,
        coord_type: str
    ) -> Optional[float]:
        """
        Validate coordinate value.
        
        Args:
            value: Coordinate value
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            restaurant_id: Restaurant ID for logging
            coord_type: Type of coordinate (latitude/longitude)
            
        Returns:
            Validated coordinate or None
        """
        if value is None:
            return None
        
        # Check type
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (ValueError, TypeError):
                logger.warning(f"⚠️  Restaurant {restaurant_id} has invalid {coord_type}: {value}")
                return None
        
        # Check range
        if value < min_val or value > max_val:
            logger.warning(f"⚠️  Restaurant {restaurant_id} has out-of-range {coord_type}: {value}")
            return None
        
        return float(value)
    
    @classmethod
    def _validate_array_field(cls, value: Any, restaurant_id: Any, field_name: str) -> List[Any]:
        """
        Validate array field (food_tags, comments).
        
        Args:
            value: Field value (could be list, string, or None)
            restaurant_id: Restaurant ID for logging
            field_name: Field name for logging
            
        Returns:
            Validated list (empty if invalid)
        """
        # Already a list
        if isinstance(value, list):
            # Sanitize each item in list
            sanitized = []
            for item in value:
                if isinstance(item, str):
                    sanitized_item = cls._sanitize_text(item, 500)  # 500 chars per tag/comment
                    if sanitized_item:
                        sanitized.append(sanitized_item)
                else:
                    sanitized.append(item)
            return sanitized
        
        # None or empty
        if not value:
            return []
        
        # String (should not happen if parsed correctly, but handle anyway)
        if isinstance(value, str):
            logger.warning(f"⚠️  Restaurant {restaurant_id} has string {field_name}: {value}")
            return []
        
        # Invalid type
        logger.warning(f"⚠️  Restaurant {restaurant_id} has invalid {field_name} type: {type(value)}")
        return []


# Global validator instance
restaurant_validator = RestaurantValidator()
