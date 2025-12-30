"""
Food Taxonomy and Semantic Understanding Engine.
Hierarchical food classification + semantic similarity.
"""
from typing import Dict, List, Set, Tuple, Optional
import json
from pathlib import Path


# Food Taxonomy - Based on REAL DATA from data.json (2057 restaurants in HCM)
# Food tags extracted: buffet, bình dân, cafe, cơm, hải sản, lẩu, món chiên, món kho, món nước, 
#                      món nướng, món xào, nướng, tráng miệng, ăn vặt, đồ chay, đồ uống
FOOD_TAXONOMY = {
    "Main_Dishes": {
        "Cơm": {
            "keywords": ["cơm", "rice", "cơm tấm", "cơm chiên", "cơm gà", "cơm bình dân"],
            "variations": ["cơm tấm", "cơm chiên", "cơm gà", "cơm sườn", "cơm bì", "cơm niêu", "cơm rang"],
            "description": "Rice-based dishes - most popular in Vietnam"
        },
        "Món Nước": {
            "keywords": ["món nước", "soup", "noodle soup", "phở", "bún", "mì", "hủ tiếu", "bánh canh"],
            "variations": ["phở bò", "phở gà", "bún bò", "bún riêu", "mì xào", "hủ tiếu nam vang", "bánh canh cua"],
            "description": "Soupy noodle dishes"
        },
        "Hải Sản": {
            "keywords": ["hải sản", "seafood", "tôm", "cua", "cá", "mực", "ốc", "nghêu", "sò"],
            "variations": ["hải sản nướng", "hải sản hấp", "lẩu hải sản", "hải sản chiên", "hải sản xào"],
            "description": "Seafood dishes"
        },
        "Lẩu": {
            "keywords": ["lẩu", "hotpot", "lẩu thái", "lẩu hải sản", "lẩu gà", "lẩu bò"],
            "variations": ["lẩu thái", "lẩu hải sản", "lẩu nấm", "lẩu cá", "lẩu bò", "lẩu gà"],
            "description": "Hotpot - popular group dining"
        },
        "Buffet": {
            "keywords": ["buffet", "tiệc", "ăn thoải mái", "all you can eat"],
            "variations": ["buffet hải sản", "buffet nướng", "buffet lẩu", "buffet thái"],
            "description": "Buffet style restaurants"
        },
    },
    "Cooking_Methods": {
        "Món Nướng": {
            "keywords": ["nướng", "grilled", "bbq", "nướng than", "nướng lụi", "nướng sa tế"],
            "variations": ["nướng than", "nướng sườn", "nướng hải sản", "nướng lụi", "nướng xiên"],
            "description": "Grilled dishes - very popular"
        },
        "Món Chiên": {
            "keywords": ["chiên", "fried", "rán", "giòn", "chiên xù", "chiên giòn"],
            "variations": ["chiên giòn", "chiên xù", "gà rán", "khoai chiên", "nem rán"],
            "description": "Fried dishes"
        },
        "Món Xào": {
            "keywords": ["xào", "stir-fry", "stir fried", "xào tỏi", "xào sa tế"],
            "variations": ["xào rau", "xào thịt", "xào hải sản", "xào lăn", "xào tỏi"],
            "description": "Stir-fried dishes"
        },
        "Món Kho": {
            "keywords": ["kho", "braised", "kho tộ", "kho quẹt", "kho tiêu"],
            "variations": ["kho tộ", "cá kho", "thịt kho", "kho quẹt"],
            "description": "Braised dishes in clay pot"
        },
    },
    "Snacks_Drinks": {
        "Ăn Vặt": {
            "keywords": ["ăn vặt", "snack", "vặt", "quẩy", "chè", "bánh tráng", "xôi"],
            "variations": ["bánh tráng trộn", "chè", "xôi", "quẩy", "nem chua rán"],
            "description": "Snacks and street food"
        },
        "Tráng Miệng": {
            "keywords": ["tráng miệng", "dessert", "ngọt", "chè", "kem", "bánh ngọt"],
            "variations": ["chè", "kem", "bánh ngọt", "yaourt", "flan"],
            "description": "Desserts"
        },
        "Đồ Uống": {
            "keywords": ["đồ uống", "drink", "nước", "nước ép", "sinh tố", "trà", "cà phê"],
            "variations": ["cà phê", "trà sữa", "nước ép", "sinh tố", "trà đá"],
            "description": "Beverages"
        },
        "Cafe": {
            "keywords": ["cafe", "coffee", "cà phê", "quán cafe", "coffee shop"],
            "variations": ["cà phê sữa", "cà phê đen", "cappuccino", "latte", "espresso"],
            "description": "Coffee shops and cafes"
        },
    },
    "Special_Types": {
        "Đồ Chay": {
            "keywords": ["chay", "vegetarian", "chay trường", "thuần chay", "vegan"],
            "variations": ["cơm chay", "phở chay", "bún chay", "lẩu chay"],
            "description": "Vegetarian/Vegan food"
        },
        "Bình Dân": {
            "keywords": ["bình dân", "rẻ", "giá rẻ", "sinh viên", "đại chúng"],
            "variations": ["quán bình dân", "cơm bình dân", "quán vỉa hè"],
            "description": "Affordable street food"
        },
    },
}

# Cooking Methods
COOKING_METHODS = {
    "nướng": ["grilled", "roasted", "BBQ"],
    "chiên": ["fried", "deep-fried"],
    "xào": ["stir-fried", "sautéed"],
    "luộc": ["boiled"],
    "nấu": ["cooked", "simmered"],
    "nướng lò": ["baked", "oven-roasted"],
    "hấp": ["steamed"],
    "nướng than": ["charcoal grilled"],
}

# Taste Profiles
TASTE_PROFILES = {
    "cay": "spicy",
    "mặn": "salty",
    "ngọt": "sweet",
    "chua": "sour",
    "đắng": "bitter",
    "ngon": "delicious",
    "béo": "creamy/rich",
    "nhạt": "bland",
}

# Ingredients
INGREDIENTS = {
    "Proteins": {
        "thịt": ["meat", "pork"],
        "bò": ["beef", "cow"],
        "gà": ["chicken", "poultry"],
        "heo": ["pork"],
        "tôm": ["shrimp", "prawn"],
        "cua": ["crab"],
        "cá": ["fish"],
        "mực": ["squid", "octopus"],
        "trứng": ["egg", "eggs"],
    },
    "Vegetables": {
        "rau": ["vegetable", "greens"],
        "xà lách": ["lettuce"],
        "cải": ["cabbage"],
        "cà chua": ["tomato"],
        "dưa": ["cucumber"],
        "ớt": ["chili", "pepper"],
    },
    "Carbs": {
        "gạo": ["rice"],
        "bánh": ["bread", "cake"],
        "noodle": ["noodles", "mì"],
        "bánh phở": ["rice noodles"],
    },
}

# Meal Types
MEAL_TYPES = {
    "sáng": "breakfast",
    "trưa": "lunch",
    "chiều": "afternoon",
    "tối": "dinner",
    "xế chiều": "snack",
}

# Atmosphere Keywords
ATMOSPHERE_TYPES = {
    "sang trọng": ["upscale", "elegant", "fancy"],
    "bình dân": ["casual", "simple", "humble"],
    "vui vẻ": ["fun", "lively", "vibrant"],
    "yên tĩnh": ["quiet", "peaceful", "calm"],
    "rộng rãi": ["spacious", "large"],
    "nhỏ gọn": ["cozy", "small", "intimate"],
    "thơm lành": ["fresh", "clean", "airy"],
    "sạch sẽ": ["clean", "hygienic"],
}


class SemanticUnderstandingEngine:
    """Semantic understanding and food taxonomy."""
    
    def __init__(self):
        self.taxonomy = FOOD_TAXONOMY
        self.cooking_methods = COOKING_METHODS
        self.taste_profiles = TASTE_PROFILES
        self.ingredients = INGREDIENTS
        self.meal_types = MEAL_TYPES
        self.atmosphere = ATMOSPHERE_TYPES
    
    def get_food_variants(self, dish: str) -> List[str]:
        """
        Get all variants of a dish.
        
        Example: "phở" → ["phở tái", "phở nạm", "phở bò", "phở gà", "phở chay"]
        """
        for cuisine_type, dishes in self.taxonomy.items():
            for category, food_items in dishes.items():
                if isinstance(food_items, dict):
                    for food_name, food_data in food_items.items():
                        if isinstance(food_data, dict) and dish.lower() in food_name.lower():
                            return food_data.get("variations", [])
        return []
    
    def get_similar_dishes(self, dish: str) -> List[str]:
        """
        Get semantically similar dishes.
        
        Example: "bánh mì" → ["bánh", "sandwich"]
        """
        similar = []
        
        # Find keywords
        for cuisine_type, dishes in self.taxonomy.items():
            for category, food_items in dishes.items():
                if isinstance(food_items, dict):
                    for food_name, food_data in food_items.items():
                        if isinstance(food_data, dict):
                            keywords = food_data.get("keywords", [])
                            # If original dish is in keywords, get the main food name
                            if any(dish.lower() in kw.lower() for kw in keywords):
                                similar.append(food_name)
        
        return similar
    
    def get_ingredients_for_dish(self, dish: str) -> List[str]:
        """
        Get ingredients commonly used in a dish.
        """
        for cuisine_type, dishes in self.taxonomy.items():
            for category, food_items in dishes.items():
                if isinstance(food_items, dict):
                    for food_name, food_data in food_items.items():
                        if isinstance(food_data, dict) and dish.lower() in food_name.lower():
                            return food_data.get("ingredients", [])
        return []
    
    def expand_food_query(self, dish: str) -> List[str]:
        """
        Expand a food query to include variants, similar dishes, and parent categories.
        
        Example: "phở" → ["phở", "phở tái", "phở nạm", "phở bò", "phở gà", "phở chay", "noodles"]
        """
        expanded = [dish]
        
        # Add variants
        variants = self.get_food_variants(dish)
        expanded.extend(variants)
        
        # Add similar dishes
        similar = self.get_similar_dishes(dish)
        expanded.extend(similar)
        
        # Add parent category (Vietnamese, Noodles, etc.)
        for cuisine_type, dishes in self.taxonomy.items():
            for category, food_items in dishes.items():
                if dish.lower() in str(food_items).lower():
                    # expanded.append(category.lower())
                    pass
        
        return list(set(expanded))  # Remove duplicates
    
    def is_vegetarian_query(self, query: str) -> bool:
        """Check if query is asking for vegetarian/vegan food."""
        return any(word in query.lower() for word in ["chay", "chay trường", "vegetarian", "vegan", "không thịt"])
    
    def extract_cooking_preference(self, query: str) -> Optional[str]:
        """Extract cooking method preference."""
        for method, translations in self.cooking_methods.items():
            if method in query.lower() or any(t in query.lower() for t in translations):
                return method
        return None
    
    def extract_taste_preference(self, query: str) -> List[str]:
        """Extract taste preferences."""
        preferences = []
        for taste, translation in self.taste_profiles.items():
            if taste in query.lower() or translation in query.lower():
                preferences.append(taste)
        return preferences
    
    def extract_atmosphere_preference(self, query: str) -> Optional[str]:
        """Extract atmosphere preference."""
        for atm, translations in self.atmosphere.items():
            if atm in query.lower() or any(t in query.lower() for t in translations):
                return atm
        return None
    
    def semantic_distance(self, query1: str, query2: str) -> float:
        """
        Calculate semantic distance between two queries.
        
        Returns:
            Score 0-1 (0 = identical, 1 = completely different)
        """
        if query1.lower() == query2.lower():
            return 0.0
        
        # Check if they're synonyms/variants
        expanded1 = set(self.expand_food_query(query1))
        expanded2 = set(self.expand_food_query(query2))
        
        if query2 in expanded1 or query1 in expanded2:
            return 0.1  # Very similar
        
        # Check if they share common ingredients
        ingredients1 = set(self.get_ingredients_for_dish(query1))
        ingredients2 = set(self.get_ingredients_for_dish(query2))
        
        if ingredients1 and ingredients2:
            overlap = len(ingredients1 & ingredients2) / max(len(ingredients1), len(ingredients2))
            if overlap > 0.3:
                return 0.3  # Similar
        
        return 1.0  # Different


# Global instance
semantic_engine = SemanticUnderstandingEngine()


# Export
__all__ = [
    'SemanticUnderstandingEngine',
    'semantic_engine',
    'FOOD_TAXONOMY',
    'COOKING_METHODS',
    'TASTE_PROFILES',
    'INGREDIENTS',
    'ATMOSPHERE_TYPES',
]
