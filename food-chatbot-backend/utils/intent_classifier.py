"""
Intent Classification and Multi-Intent Detection.
Determines user intent from query with confidence scoring.
"""
from typing import Dict, List, Tuple, Optional
from enum import Enum
import re


class IntentType(str, Enum):
    """Main intent categories."""
    SEARCH = "search"
    QUESTION = "question"
    FEEDBACK = "feedback"
    GREETING = "greeting"
    OFF_TOPIC = "off_topic"
    CLARIFICATION = "clarification"


class SubIntent(str, Enum):
    """Sub-intent categories for SEARCH."""
    BY_CUISINE = "by_cuisine"
    BY_LOCATION = "by_location"
    BY_BUDGET = "by_budget"
    BY_QUALITY = "by_quality"
    BY_ATMOSPHERE = "by_atmosphere"
    BY_SPECIAL = "by_special"
    BY_TIME = "by_time"
    BY_GROUP = "by_group"
    BY_POPULARITY = "by_popularity"
    BY_RATING = "by_rating"


# Intent Keywords
INTENT_KEYWORDS = {
    IntentType.GREETING: {
        "vi": ["xin chào", "chào", "hello", "hi", "chào bạn", "chào anh", "chào em", "yo"],
        "score": 1.0,
    },
    IntentType.SEARCH: {
        "vi": ["tìm", "gợi ý", "giới thiệu", "muốn", "thích", "thèm", "cần", "tìm kiếm", "lên kế hoạch", "recommend", "suggest"],
        "score": 1.0,
    },
    IntentType.FEEDBACK: {
        "vi": ["tuyệt vời", "không tốt", "tốt", "xấu", "yêu thích", "ghét", "cảm ơn", "không thích", "sao lại"],
        "score": 0.9,
    },
    IntentType.OFF_TOPIC: {
        "vi": [
            # Medical/Health
            "bệnh viện", "bệnh", "khám bệnh", "doctor", "hospital", "phòng khám", "thuốc", "y tế",
            # Travel/Tourism
            "du lịch", "khu du lịch", "tour", "điểm du lịch", "danh lam", "thắng cảnh", "resort", "khách sạn",
            # Shopping/Services
            "mua sắm", "trung tâm thương mại", "mall", "shopping", "siêu thị", "cửa hàng quần áo",
            # Entertainment
            "rạp phim", "cinema", "xem phim", "phim", "nhạc", "concert", "trò chơi", "game", "karaoke",
            # Transportation
            "xe buýt", "bus", "tàu hỏa", "train", "máy bay", "flight", "sân bay", "airport",
            # Education
            "trường học", "school", "university", "đại học", "trường", "học",
            # Finance/Banking
            "ngân hàng", "bank", "atm", "rút tiền", "chuyển khoản",
            # Others
            "thời tiết", "weather", "tin tức", "news", "thể thao", "sport", "mấy giờ", "ngày mấy",
            "bưu điện", "post office", "công viên", "park", "bảo tàng", "museum"
        ],
        "score": 0.95,
    },
    IntentType.CLARIFICATION: {
        "vi": ["sao", "sao lại", "tại sao", "cái nào", "cái gì", "hình như", "hay", "gì", "à", "nhưng"],
        "score": 0.7,
    },
}

# Sub-intent Keywords (for SEARCH)
SUBINTENT_KEYWORDS = {
    SubIntent.BY_CUISINE: {
        "keywords": ["phở", "bánh mì", "bún", "cơm", "mì", "hải sản", "nướng", "lẩu", "gỏi", "thái", "nhật"],
        "patterns": [r"(?:quán|nhà hàng)\s+(\w+)", r"(?:ăn|uống)\s+(\w+)"],
    },
    SubIntent.BY_LOCATION: {
        "keywords": ["quận", "bến", "phường", "thành phố", "huyện", "gần", "xa", "ở"],
        "patterns": [r"(?:ở|quanh|gần)\s+(\w+)", r"(?:quận|q)\s*(\d+)"],
    },
    SubIntent.BY_BUDGET: {
        "keywords": ["rẻ", "đắt", "giá", "bao nhiêu", "ngân sách", "tiền", "k", "30k", "50k"],
        "patterns": [r"(\d+)\s*k", r"dưới\s*(\d+)", r"trên\s*(\d+)"],
    },
    SubIntent.BY_QUALITY: {
        "keywords": ["ngon", "ngon nhất", "xịn", "chất", "tuyệt vời", "ngon miệng", "tươi tốt"],
        "patterns": [r"(?:tìm|gợi ý)\s+(?:quán|cái)\s+(\w+)"],
    },
    SubIntent.BY_ATMOSPHERE: {
        "keywords": ["sang trọng", "bình dân", "vui vẻ", "yên tĩnh", "rộng", "nhỏ", "thơm", "sạch"],
        "patterns": [],
    },
    SubIntent.BY_SPECIAL: {
        "keywords": ["bàn riêng", "riêng tư", "view", "khoảng cách", "bàn lớn", "family"],
        "patterns": [],
    },
    SubIntent.BY_TIME: {
        "keywords": ["mở cửa", "đang mở", "giờ nào", "bây giờ", "hôm nay", "tối nay", "trưa nay"],
        "patterns": [r"(?:mở cửa)\s+(?:lúc|từ|đến)\s*(\d{1,2}):?(\d{2})?"],
    },
    SubIntent.BY_GROUP: {
        "keywords": ["người", "nhóm", "gia đình", "bạn", "đôi", "trio", "4 người", "10 người"],
        "patterns": [r"(\d+)\s*(?:người|cái|chiếc)", r"(?:2|ba|4|5|6|7|8|9|10)\s+(?:người|bạn)"],
    },
    SubIntent.BY_POPULARITY: {
        "keywords": ["nổi tiếng", "khét", "nhan nhản", "đông", "sao"],
        "patterns": [],
    },
    SubIntent.BY_RATING: {
        "keywords": ["ngon nhất", "xếp hạng", "rating", "đánh giá", "tốt nhất", "top"],
        "patterns": [],
    },
}

# Contradiction Keywords
CONTRADICTION_KEYWORDS = {
    "cheap_expensive": (["rẻ", "cheap", "hạt dẻ"], ["đắt", "expensive", "chát", "cháy túi"]),
    "quality_price": (["xịn", "ngon", "chất", "cao cấp"], ["rẻ", "cheap", "mềm"]),
    "space": (["rộng", "spacious"], ["nhỏ", "cozy", "intimate", "nhỏ gọn"]),
    "noise": (["yên tĩnh", "quiet"], ["vui vẻ", "lively", "sôi động", "tấp nập"]),
}

# Ambiguity Keywords
AMBIGUITY_KEYWORDS = {
    "vague_cuisine": ["cái gì", "gì", "không biết", "gợi ý", "tùy"],
    "vague_location": ["bất kỳ", "đâu cũng được", "gần gần", "khoảng"],
    "vague_price": ["tùy", "bất kỳ", "không biết", "khoảng"],
}


class IntentClassifier:
    """Classify user intents with confidence scoring."""
    
    def classify(self, query: str) -> Dict:
        """
        Classify query into intents.
        
        Returns:
            {
                "main_intent": IntentType,
                "confidence": float,
                "sub_intents": [{"intent": SubIntent, "confidence": float}],
                "has_contradiction": bool,
                "contradiction_types": List[str],
                "is_ambiguous": bool,
                "ambiguity_types": List[str],
                "explanation": str,
            }
        """
        query_lower = query.lower()
        
        # Step 1: Detect main intent
        main_intent, confidence = self._detect_main_intent(query_lower)
        
        # Step 2: Detect sub-intents (for SEARCH)
        sub_intents = []
        if main_intent == IntentType.SEARCH:
            sub_intents = self._detect_sub_intents(query_lower)
        
        # Step 3: Detect contradictions
        contradictions = self._detect_contradictions(query_lower)
        
        # Step 4: Detect ambiguity
        ambiguities = self._detect_ambiguities(query_lower)
        
        # Step 5: Generate explanation
        explanation = self._generate_explanation(
            main_intent, sub_intents, contradictions, ambiguities
        )
        
        return {
            "main_intent": main_intent.value,
            "confidence": confidence,
            "sub_intents": [
                {"intent": si["intent"].value, "confidence": si["confidence"]}
                for si in sub_intents
            ],
            "has_contradiction": len(contradictions) > 0,
            "contradiction_types": contradictions,
            "is_ambiguous": len(ambiguities) > 0,
            "ambiguity_types": ambiguities,
            "explanation": explanation,
        }
    
    def _detect_main_intent(self, query: str) -> Tuple[IntentType, float]:
        """Detect primary intent with boosted confidence."""
        scores = {}
        
        for intent_type, intent_data in INTENT_KEYWORDS.items():
            keywords = intent_data.get("vi", [])
            base_score = intent_data.get("score", 1.0)
            
            # Count keyword matches
            matches = sum(1 for kw in keywords if kw in query)
            
            if matches > 0:
                # Boost confidence: even 1 match gives high confidence
                # Formula: min(matches * 0.3, 1.0) ensures 3+ matches = 90%+ confidence
                match_confidence = min(matches * 0.3, 1.0)
                scores[intent_type] = match_confidence * base_score
        
        # Default to SEARCH if food-related, OFF_TOPIC otherwise
        if not scores:
            # Check if food-related (expanded list with all food_tags from database)
            food_keywords = [
                "phở", "bánh", "bún", "cơm", "mì", "quán", "nhà hàng", "ăn", "uống", 
                "món", "thức ăn", "food", "restaurant",
                # Food tags from database
                "buffet", "lẩu", "hải sản", "nướng", "chiên", "xào", "kho", 
                "cafe", "ăn vặt", "tráng miệng", "đồ uống", "đồ chay", "bình dân",
                "hotpot", "seafood", "bbq", "grill", "fried", "stir fry", "dessert"
            ]
            if any(kw in query for kw in food_keywords):
                # Higher confidence for exact food keyword matches
                # This allows single word queries like "buffet" to work
                return IntentType.SEARCH, 0.85
            else:
                return IntentType.OFF_TOPIC, 0.8
        
        # Return best match
        best_intent = max(scores, key=scores.get)
        confidence = scores[best_intent]
        
        # Boost confidence for OFF_TOPIC (to ensure it gets priority)
        if best_intent == IntentType.OFF_TOPIC and confidence < 0.9:
            confidence = min(confidence * 1.5, 0.95)  # Boost but cap at 95%
        
        return best_intent, confidence
    
    def _detect_sub_intents(self, query: str) -> List[Dict]:
        """Detect sub-intents for SEARCH queries."""
        sub_intents = []
        
        for subintent_type, subintent_data in SUBINTENT_KEYWORDS.items():
            keywords = subintent_data.get("keywords", [])
            patterns = subintent_data.get("patterns", [])
            
            # Check keyword matches
            keyword_matches = sum(1 for kw in keywords if kw in query)
            
            # Check pattern matches
            pattern_matches = sum(1 for pattern in patterns if re.search(pattern, query))
            
            if keyword_matches > 0 or pattern_matches > 0:
                confidence = min((keyword_matches + pattern_matches * 0.5) / 3, 1.0)
                sub_intents.append({
                    "intent": subintent_type,
                    "confidence": confidence
                })
        
        # Sort by confidence
        sub_intents.sort(key=lambda x: x["confidence"], reverse=True)
        return sub_intents
    
    def _detect_contradictions(self, query: str) -> List[str]:
        """Detect contradictory requests."""
        contradictions = []
        
        for contra_type, (group1, group2) in CONTRADICTION_KEYWORDS.items():
            has_group1 = any(kw in query for kw in group1)
            has_group2 = any(kw in query for kw in group2)
            
            if has_group1 and has_group2:
                contradictions.append(contra_type)
        
        return contradictions
    
    def _detect_ambiguities(self, query: str) -> List[str]:
        """Detect ambiguous or vague requests."""
        ambiguities = []
        
        for ambig_type, keywords in AMBIGUITY_KEYWORDS.items():
            if any(kw in query for kw in keywords):
                ambiguities.append(ambig_type)
        
        return ambiguities
    
    def _generate_explanation(
        self, 
        main_intent: IntentType,
        sub_intents: List[Dict],
        contradictions: List[str],
        ambiguities: List[str]
    ) -> str:
        """Generate explanation of intent classification."""
        parts = []
        
        # Main intent
        parts.append(f"Bạn muốn {self._intent_to_vietnamese(main_intent)}")
        
        # Sub-intents
        if sub_intents:
            sub_intent_names = [self._subintent_to_vietnamese(si["intent"]) for si in sub_intents[:2]]
            parts.append(f"Yêu cầu: {', '.join(sub_intent_names)}")
        
        # Contradictions
        if contradictions:
            parts.append(f"⚠️ Có yêu cầu mâu thuẫn: {', '.join(contradictions)}")
        
        # Ambiguities
        if ambiguities:
            parts.append(f"❓ Yêu cầu chưa rõ: {', '.join(ambiguities)}")
        
        return " | ".join(parts)
    
    @staticmethod
    def _intent_to_vietnamese(intent: IntentType) -> str:
        """Convert intent to Vietnamese description."""
        mapping = {
            IntentType.SEARCH: "tìm quán ăn",
            IntentType.QUESTION: "hỏi về thông tin",
            IntentType.FEEDBACK: "phản hồi",
            IntentType.GREETING: "chào hỏi",
            IntentType.OFF_TOPIC: "hỏi về chủ đề khác",
            IntentType.CLARIFICATION: "yêu cầu làm rõ",
        }
        return mapping.get(intent, "không biết")
    
    @staticmethod
    def _subintent_to_vietnamese(subintent: SubIntent) -> str:
        """Convert sub-intent to Vietnamese description."""
        mapping = {
            SubIntent.BY_CUISINE: "theo loại món ăn",
            SubIntent.BY_LOCATION: "theo địa điểm",
            SubIntent.BY_BUDGET: "theo giá",
            SubIntent.BY_QUALITY: "theo chất lượng",
            SubIntent.BY_ATMOSPHERE: "theo không khí",
            SubIntent.BY_SPECIAL: "theo yêu cầu đặc biệt",
            SubIntent.BY_TIME: "theo giờ mở cửa",
            SubIntent.BY_GROUP: "theo số người",
            SubIntent.BY_POPULARITY: "theo mức độ nổi tiếng",
            SubIntent.BY_RATING: "theo đánh giá",
        }
        return mapping.get(subintent, "không biết")


# Global instance
intent_classifier = IntentClassifier()


# Export
__all__ = [
    'IntentClassifier',
    'IntentType',
    'SubIntent',
    'intent_classifier',
]
