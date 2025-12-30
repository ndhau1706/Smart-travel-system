"""
Improved Clarification Engine with NLU and Context Awareness
Smarter clarification questions based on intent confidence and entity completeness.
"""
from typing import Dict, List, Optional, Any, Tuple
import re
from collections import Counter


class ImprovedClarificationEngine:
    """
    ChatGPT-quality clarification with:
    - Intent confidence scoring
    - Entity completeness analysis
    - Conversational context awareness
    - Minimal interruption (only ask when truly ambiguous)
    """
    
    def __init__(self):
        # Confidence thresholds
        self.HIGH_CONFIDENCE_THRESHOLD = 0.8
        self.MEDIUM_CONFIDENCE_THRESHOLD = 0.5
        self.LOW_CONFIDENCE_THRESHOLD = 0.3
        
        # Essential entities for each intent
        self.ESSENTIAL_ENTITIES = {
            'find_restaurant': ['cuisine', 'location'],
            'compare_restaurants': ['entities_to_compare'],
            'get_recommendations': ['preferences'],
            'check_specific_restaurant': ['restaurant_name'],
            'filter_by_criteria': ['filter_criteria'],
            'general_question': [],  # No required entities
        }
        
        # Questions that don't need clarification
        self.CLEAR_INTENTS = {
            'greeting', 'farewell', 'thank_you', 'general_question'
        }
    
    def should_clarify(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any],
        intent_confidence: float,
        conversation_context: Optional[List[Dict]] = None
    ) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Determine if clarification is needed.
        
        Args:
            query: User query
            intent: Detected intent
            entities: Extracted entities
            intent_confidence: Confidence score (0-1)
            conversation_context: Previous conversation turns
            
        Returns:
            Tuple of (should_clarify: bool, clarification_message: str, suggestions: dict)
        """
        # 1. Clear intents don't need clarification
        if intent in self.CLEAR_INTENTS:
            return False, None, None
        
        # 2. High confidence + complete entities = no clarification
        if intent_confidence >= self.HIGH_CONFIDENCE_THRESHOLD:
            completeness = self._check_entity_completeness(intent, entities)
            if completeness >= 0.8:
                return False, None, None
        
        # 3. Use context to fill gaps
        if conversation_context:
            entities = self._fill_from_context(entities, conversation_context)
            completeness = self._check_entity_completeness(intent, entities)
            
            # Context helped complete the query
            if completeness >= 0.7 and intent_confidence >= 0.6:
                return False, None, None
        
        # 4. Very low confidence = need clarification
        if intent_confidence < self.LOW_CONFIDENCE_THRESHOLD:
            return self._generate_intent_clarification(query, intent, entities)
        
        # 5. Missing critical entities = need clarification
        completeness = self._check_entity_completeness(intent, entities)
        if completeness < 0.5:
            return self._generate_entity_clarification(query, intent, entities)
        
        # 6. Ambiguous query patterns
        if self._is_ambiguous(query, entities):
            return self._generate_ambiguity_clarification(query, intent, entities)
        
        # No clarification needed
        return False, None, None
    
    def _check_entity_completeness(
        self,
        intent: str,
        entities: Dict[str, Any]
    ) -> float:
        """
        Check how complete the extracted entities are.
        
        Returns completeness score 0.0-1.0.
        """
        required_entities = self.ESSENTIAL_ENTITIES.get(intent, [])
        
        if not required_entities:
            return 1.0  # No requirements
        
        # Count present entities
        present = 0
        for entity_type in required_entities:
            if entities.get(entity_type):
                # Check if entity has meaningful value
                value = entities[entity_type]
                if isinstance(value, str) and value.strip():
                    present += 1
                elif isinstance(value, (list, dict)) and value:
                    present += 1
        
        return present / len(required_entities)
    
    def _fill_from_context(
        self,
        entities: Dict[str, Any],
        context: List[Dict]
    ) -> Dict[str, Any]:
        """
        Fill missing entities from conversation context.
        
        Example: 
        User: "Tìm quán phở" (has cuisine)
        Bot: "Bạn muốn tìm ở đâu?"
        User: "Quận 1" (only has location)
        -> Fill cuisine from previous turn
        """
        filled_entities = entities.copy()
        
        # Look at last 3 turns
        for turn in context[-3:]:
            if turn.get('role') == 'user':
                prev_entities = turn.get('entities', {})
                
                # Fill missing entities from previous turns
                for key, value in prev_entities.items():
                    if not filled_entities.get(key) and value:
                        filled_entities[key] = value
        
        return filled_entities
    
    def _is_ambiguous(self, query: str, entities: Dict[str, Any]) -> bool:
        """
        Detect ambiguous queries that need clarification.
        
        Examples of ambiguity:
        - "quán ăn ngon" (too vague, what cuisine?)
        - "gần đây" (where is "here"?)
        - "giá rẻ" (how much exactly?)
        """
        query_lower = query.lower().strip()
        
        # Pattern 1: Too vague (generic terms without specifics)
        vague_patterns = [
            r'^(quán ăn|nhà hàng|chỗ ăn)(\s+(ngon|tốt|ok|ổn))?$',
            r'^(tìm|kiếm|gợi ý)(\s+(quán|nhà hàng|chỗ))?$',
            r'^(ăn gì|ăn|đi ăn)$',
        ]
        
        for pattern in vague_patterns:
            if re.match(pattern, query_lower):
                # Check if entities clarify the vagueness
                if not (entities.get('cuisine') or entities.get('food_type')):
                    return True
        
        # Pattern 2: Location ambiguity
        location_patterns = [
            r'(gần|near|nearby|quanh đây)',
            r'(ở đây|here)',
        ]
        
        for pattern in location_patterns:
            if re.search(pattern, query_lower):
                # Need user location
                if not entities.get('location') and not entities.get('user_location'):
                    return True
        
        # Pattern 3: Price ambiguity
        price_patterns = [
            r'(rẻ|giá rẻ|cheap)',
            r'(đắt|cao cấp|expensive)',
        ]
        
        for pattern in price_patterns:
            if re.search(pattern, query_lower):
                # Check if specific budget mentioned
                if not entities.get('max_budget') and not entities.get('price_level'):
                    return True
        
        return False
    
    def _generate_intent_clarification(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Tuple[bool, str, Dict]:
        """Generate clarification for unclear intent."""
        # Offer multiple interpretations
        message = "Xin lỗi, mình chưa hiểu rõ ý bạn. Bạn muốn:\n"
        
        suggestions = {
            'options': [
                {'label': '🔍 Tìm nhà hàng', 'value': 'find_restaurant'},
                {'label': '⭐ Gợi ý món ăn', 'value': 'get_recommendations'},
                {'label': '📍 Tìm quán gần đây', 'value': 'find_nearby'},
                {'label': '💰 Tìm quán theo giá', 'value': 'filter_by_price'},
            ]
        }
        
        return True, message, suggestions
    
    def _generate_entity_clarification(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Tuple[bool, str, Dict]:
        """Generate clarification for missing entities."""
        required = self.ESSENTIAL_ENTITIES.get(intent, [])
        missing = [e for e in required if not entities.get(e)]
        
        if not missing:
            return False, None, None
        
        # Focus on most important missing entity
        primary_missing = missing[0]
        
        if primary_missing == 'cuisine':
            message = "Bạn muốn tìm món gì? (VD: phở, sushi, pizza, lẩu...)"
            suggestions = {
                'type': 'cuisine',
                'quick_options': [
                    '🍜 Phở', '🍣 Sushi', '🍕 Pizza', 
                    '🍖 BBQ', '🍲 Lẩu', '🍱 Cơm'
                ]
            }
            return True, message, suggestions
        
        elif primary_missing == 'location':
            message = "Bạn muốn tìm ở khu vực nào? (VD: Quận 1, Quận 3, Bình Thạnh...)"
            suggestions = {
                'type': 'location',
                'quick_options': [
                    '📍 Quận 1', '📍 Quận 3', '📍 Bình Thạnh',
                    '📍 Phú Nhuận', '📍 Quận 10', '📍 Gần tôi'
                ]
            }
            return True, message, suggestions
        
        elif primary_missing == 'preferences':
            message = "Bạn thích món gì? Hoặc cho mình biết thêm về sở thích của bạn nhé!"
            suggestions = {
                'type': 'preferences',
                'quick_options': [
                    '🌶️ Cay', '🥗 Lành mạnh', '🍖 Thịt nướng',
                    '🐟 Hải sản', '🥬 Chay', '🍰 Tráng miệng'
                ]
            }
            return True, message, suggestions
        
        elif primary_missing == 'restaurant_name':
            message = "Bạn muốn hỏi về quán nào? Cho mình biết tên quán nhé!"
            return True, message, {'type': 'restaurant_name'}
        
        # Generic missing entity
        message = f"Bạn có thể cho mình biết thêm về {primary_missing}?"
        return True, message, {'type': primary_missing}
    
    def _generate_ambiguity_clarification(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> Tuple[bool, str, Dict]:
        """Generate clarification for ambiguous queries."""
        query_lower = query.lower()
        
        # Handle vague queries
        if re.search(r'(quán ăn|nhà hàng)\s+(ngon|tốt)', query_lower):
            message = "Bạn muốn tìm món gì? (phở, sushi, pizza, lẩu...)"
            suggestions = {
                'type': 'cuisine',
                'quick_options': ['Phở', 'Sushi', 'Pizza', 'Lẩu', 'BBQ', 'Cơm']
            }
            return True, message, suggestions
        
        # Handle location ambiguity
        if re.search(r'(gần|nearby)', query_lower):
            message = "Bạn cần chia sẻ vị trí để mình tìm quán gần bạn nhé! 📍"
            suggestions = {
                'type': 'location',
                'action': 'request_location'
            }
            return True, message, suggestions
        
        # Handle price ambiguity
        if re.search(r'(rẻ|giá rẻ)', query_lower):
            message = "Ngân sách của bạn khoảng bao nhiêu/người?"
            suggestions = {
                'type': 'budget',
                'quick_options': [
                    '💵 < 50k', '💵 50-100k', '💵 100-200k', 
                    '💵 200-500k', '💵 > 500k'
                ]
            }
            return True, message, suggestions
        
        return False, None, None
    
    def calculate_intent_confidence(
        self,
        query: str,
        intent: str,
        entities: Dict[str, Any]
    ) -> float:
        """
        Calculate intent confidence score.
        
        Based on:
        - Query length and specificity
        - Entity presence
        - Keyword matching
        
        Returns confidence 0.0-1.0
        """
        confidence = 0.5  # Base confidence
        
        # Factor 1: Query length (longer = more specific = higher confidence)
        word_count = len(query.split())
        if word_count >= 5:
            confidence += 0.2
        elif word_count >= 3:
            confidence += 0.1
        
        # Factor 2: Entity richness
        entity_count = len([v for v in entities.values() if v])
        if entity_count >= 3:
            confidence += 0.2
        elif entity_count >= 2:
            confidence += 0.1
        elif entity_count >= 1:
            confidence += 0.05
        
        # Factor 3: Intent-specific keywords
        intent_keywords = {
            'find_restaurant': ['tìm', 'kiếm', 'find', 'search', 'quán', 'nhà hàng'],
            'get_recommendations': ['gợi ý', 'recommend', 'suggest', 'nên ăn', 'nên chọn'],
            'compare_restaurants': ['so sánh', 'compare', 'khác gì', 'hơn'],
            'check_specific_restaurant': ['quán', 'restaurant', 'địa chỉ', 'giờ mở cửa'],
        }
        
        keywords = intent_keywords.get(intent, [])
        query_lower = query.lower()
        keyword_matches = sum(1 for kw in keywords if kw in query_lower)
        
        if keyword_matches >= 2:
            confidence += 0.1
        elif keyword_matches >= 1:
            confidence += 0.05
        
        # Cap at 1.0
        return min(1.0, confidence)


# Global instance
improved_clarification_engine = ImprovedClarificationEngine()
