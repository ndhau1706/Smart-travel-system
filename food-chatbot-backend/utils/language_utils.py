"""
Language detection utility.
"""
import re
from typing import Literal


def detect_language(text: str) -> Literal["vi", "en"]:
    """
    Detect if text is Vietnamese or English.
    
    Args:
        text: Input text
        
    Returns:
        Language code: "vi" or "en"
    """
    if not text:
        return "vi"
    
    # Vietnamese specific characters
    vietnamese_chars = 'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ'
    vietnamese_chars += vietnamese_chars.upper()
    
    # Count Vietnamese characters
    vi_char_count = sum(1 for char in text if char in vietnamese_chars)
    
    # Vietnamese keywords
    vietnamese_keywords = [
        'món', 'quán', 'nhà hàng', 'ăn', 'uống', 'ngon', 'rẻ', 'đắt',
        'cơm', 'phở', 'bún', 'bánh', 'chè', 'cà phê', 'trà',
        'gần', 'xa', 'ở đâu', 'bao nhiêu', 'giá', 'tiền',
        'tìm', 'gợi ý', 'giới thiệu', 'muốn', 'thích', 'thèm'
    ]
    
    # English keywords
    english_keywords = [
        'restaurant', 'food', 'eat', 'drink', 'delicious', 'cheap', 'expensive',
        'where', 'how much', 'price', 'find', 'recommend', 'suggest', 'want', 'like',
        'near', 'close', 'far'
    ]
    
    text_lower = text.lower()
    
    # Count keyword matches
    vi_keyword_count = sum(1 for kw in vietnamese_keywords if kw in text_lower)
    en_keyword_count = sum(1 for kw in english_keywords if kw in text_lower)
    
    # Decision logic
    if vi_char_count > 0:
        return "vi"
    elif vi_keyword_count > en_keyword_count:
        return "vi"
    elif en_keyword_count > 0:
        return "en"
    else:
        # Default to Vietnamese
        return "vi"


def is_food_related(text: str, language: str = "vi") -> bool:
    """
    Check if text is related to food/restaurants.
    
    Args:
        text: Input text
        language: Language code
        
    Returns:
        True if text is food-related
    """
    text_lower = text.lower()
    
    # Food related keywords by language
    food_keywords = {
        "vi": [
            # Greetings are allowed
            'xin chào', 'hello', 'hi', 'chào',
            
            # Food related
            'món', 'ăn', 'uống', 'thức ăn', 'đồ ăn', 'món ăn',
            'quán', 'nhà hàng', 'restaurant', 'cafe', 'cà phê',
            'food', 'dish', 'meal', 'drink', 'beverage',
            
            # Specific foods (expanded with all food_tags from database)
            'cơm', 'phở', 'bún', 'bánh', 'mì', 'gỏi', 'lẩu',
            'nướng', 'hấp', 'xào', 'chiên', 'luộc', 'kho',
            'hải sản', 'thịt', 'gà', 'bò', 'heo', 'cá',
            'chè', 'trà', 'nước',
            # Food tags from database
            'buffet', 'café', 'ăn vặt', 'tráng miệng', 'đồ uống', 'đồ chay', 'bình dân',
            'hotpot', 'seafood', 'bbq', 'grilled', 'fried', 'dessert', 'snack',
            
            # Actions
            'gợi ý', 'giới thiệu', 'tìm', 'recommend', 'suggest',
            'muốn ăn', 'thèm', 'ngon', 'ngon miệng',
            'đặt bàn', 'booking', 'order',
            
            # Attributes
            'ngon', 'rẻ', 'đắt', 'giá', 'menu', 'thực đơn',
            'view', 'không gian', 'sang trọng', 'bình dân',
            'delicious', 'cheap', 'expensive', 'price'
        ],
        "en": [
            # Greetings
            'hello', 'hi', 'hey',
            
            # Food related
            'food', 'restaurant', 'cafe', 'eat', 'drink',
            'dish', 'meal', 'cuisine', 'dining',
            
            # Actions
            'recommend', 'suggest', 'find', 'looking for',
            'want to eat', 'hungry', 'craving',
            
            # Attributes
            'delicious', 'tasty', 'good', 'cheap', 'expensive',
            'price', 'menu', 'atmosphere', 'cozy', 'romantic'
        ]
    }
    
    keywords = food_keywords.get(language, food_keywords["vi"])
    
    # Check if any keyword is in text
    for keyword in keywords:
        if keyword in text_lower:
            return True
    
    return False
