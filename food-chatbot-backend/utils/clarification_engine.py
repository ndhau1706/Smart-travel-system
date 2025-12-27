"""
Clarification Engine - Smart follow-up questions when query is ambiguous
Handles vague queries like "quán rẻ", "gần đây", "ngon" without specific parameters
"""
from typing import Dict, List, Optional, Any
import re
import logging

logger = logging.getLogger(__name__)


class ClarificationEngine:
    """Detect ambiguous queries and generate clarifying questions."""
    
    def __init__(self):
        # FIXED BUG #3: Remove random behavior - purely deterministic now
        self.clarification_threshold = 2  # Need 2+ ambiguities to ask
        # REMOVED: self.ask_probability - no more random behavior!
        
        # BUG #3 FIX: Implicit intent patterns to infer user needs
        self.implicit_intents = {
            'budget': {
                'cheap': ['sinh viên', 'bình dân', 'rẻ', 'tiết kiệm', 'vừa túi tiền', 'student', 'budget'],
                'expensive': ['cao cấp', 'sang trọng', 'luxury', 'upscale', 'đắt', 'fine dining', 'fancy', 'high-end']
            },
            'atmosphere': {
                'romantic': ['hẹn hò', 'date', 'lãng mạn', 'romantic', 'couple'],
                'family': ['gia đình', 'family', 'trẻ em', 'kids', 'children'],
                'business': ['công việc', 'business', 'họp', 'meeting', 'formal']
            }
        }
        
        # Ambiguity detection patterns
        self.ambiguous_patterns = {
            'price_vague': {
                'keywords': ['rẻ', 'cheap', 'giá tốt', 'bình dân', 'phải chăng', 'vừa túi tiền', 'hợp túi'],
                'question_vi': "💰 Bạn muốn chi khoảng bao nhiêu cho một người?\n   • Dưới 50k (cực rẻ)\n   • 50-100k (bình dân)\n   • 100-200k (trung bình)\n   • 200-500k (cao cấp)\n   • Trên 500k (sang trọng)",
                'question_en': "💰 What's your budget per person?\n   • Under 50k (very cheap)\n   • 50-100k (budget-friendly)\n   • 100-200k (moderate)\n   • 200-500k (upscale)\n   • Over 500k (luxury)",
                'priority': 1
            },
            'distance_vague': {
                'keywords': ['gần', 'gần đây', 'nearby', 'near me', 'lân cận', 'xung quanh', 'kế bên'],
                'question_vi': "📍 Bạn muốn tìm trong bán kính bao xa?\n   • Dưới 1km (đi bộ được)\n   • 1-3km (xe máy 5-10 phút)\n   • 3-5km (di chuyển dễ)\n   • 5-10km (chấp nhận được)\n   • Không quan trọng khoảng cách",
                'question_en': "📍 How far are you willing to go?\n   • Under 1km (walking distance)\n   • 1-3km (5-10 min by motorbike)\n   • 3-5km (easy to reach)\n   • 5-10km (acceptable)\n   • Distance doesn't matter",
                'priority': 2
            },
            'quality_vague': {
                'keywords': ['ngon', 'chất lượng', 'tốt', 'quality', 'good', 'delicious', 'đã', 'ok'],
                'question_vi': "⭐ Bạn ưu tiên tiêu chí nào về chất lượng?\n   • Rating cao (4.5+ sao)\n   • Nhiều review (đông khách)\n   • Nổi tiếng/trending (đang hot)\n   • Cân bằng cả 3",
                'question_en': "⭐ What quality criteria matter most?\n   • High rating (4.5+ stars)\n   • Many reviews (popular)\n   • Trending/famous\n   • Balance of all",
                'priority': 3
            },
            'cuisine_vague': {
                'keywords': ['ăn gì', 'món gì', 'gì ngon', 'what to eat', 'food', 'cái gì'],
                'question_vi': "🍜 Bạn muốn ăn món gì?\n   • Việt Nam (phở, bún, cơm)\n   • Châu Á (Nhật, Hàn, Thái, Trung)\n   • Âu Mỹ (Ý, Pháp, Mỹ)\n   • Hải sản / BBQ / Lẩu\n   • Gợi ý cho tôi",
                'question_en': "🍜 What cuisine do you prefer?\n   • Vietnamese (pho, bun, rice)\n   • Asian (Japanese, Korean, Thai, Chinese)\n   • Western (Italian, French, American)\n   • Seafood / BBQ / Hotpot\n   • Surprise me",
                'priority': 1
            },
            'atmosphere_vague': {
                'keywords': ['view đẹp', 'không gian', 'atmosphere', 'vibe', 'chill', 'yên tĩnh', 'thoải mái'],
                'question_vi': "🎭 Bạn muốn không gian như thế nào?\n   • Lãng mạn (hẹn hò, view đẹp)\n   • Sôi động (đông vui, nhiều người)\n   • Yên tĩnh (riêng tư, nhẹ nhàng)\n   • Sang trọng (cao cấp, lịch sự)\n   • Thoải mái (đơn giản, bình dân)",
                'question_en': "🎭 What atmosphere do you prefer?\n   • Romantic (date-friendly, nice view)\n   • Lively (busy, energetic)\n   • Quiet (private, peaceful)\n   • Upscale (elegant, formal)\n   • Casual (simple, laid-back)",
                'priority': 4
            },
            'time_vague': {
                'keywords': ['bây giờ', 'hiện tại', 'lúc này', 'now', 'đang mở', 'mở cửa'],
                'question_vi': "🕐 Bạn muốn đi ăn khi nào?\n   • Ngay bây giờ (đang mở cửa)\n   • Trong 1-2 giờ tới\n   • Tối nay\n   • Cuối tuần này\n   • Chưa chắc (xem trước)",
                'question_en': "🕐 When are you planning to go?\n   • Right now (currently open)\n   • In 1-2 hours\n   • Tonight\n   • This weekend\n   • Just browsing",
                'priority': 5
            }
        }
    
    def detect_implicit_intent(self, query: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        BUG #3 FIX: Detect implicit intents from query phrases.
        Infers budget, atmosphere, etc. from contextual phrases like "sinh viên", "cao cấp".
        
        Args:
            query: User query
            params: Current extracted parameters
            
        Returns:
            Updated parameters with implicit intents
        """
        query_lower = query.lower()
        implicit_params = params.copy()
        
        # Detect implicit budget
        for budget_level, keywords in self.implicit_intents['budget'].items():
            if any(keyword in query_lower for keyword in keywords):
                if budget_level == 'cheap':
                    # Sinh viên / bình dân → under 100k
                    if 'max_budget' not in implicit_params or implicit_params.get('max_budget', 999999) > 100000:
                        implicit_params['max_budget'] = 100000
                        logger.debug(f"🎯 Implicit budget detected: cheap (max 100k) from '{query}'")
                elif budget_level == 'expensive':
                    # Cao cấp / sang trọng → over 200k
                    if 'min_budget' not in implicit_params or implicit_params.get('min_budget', 0) < 200000:
                        implicit_params['min_budget'] = 200000
                        logger.debug(f"🎯 Implicit budget detected: expensive (min 200k) from '{query}'")
                break
        
        # Detect implicit atmosphere
        for atmosphere_type, keywords in self.implicit_intents['atmosphere'].items():
            if any(keyword in query_lower for keyword in keywords):
                if 'atmosphere' not in implicit_params:
                    implicit_params['atmosphere'] = []
                if atmosphere_type not in implicit_params['atmosphere']:
                    implicit_params['atmosphere'].append(atmosphere_type)
                    logger.debug(f"🎯 Implicit atmosphere detected: {atmosphere_type} from '{query}'")
        
        return implicit_params
    
    def detect_ambiguity(self, query: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if query is ambiguous and needs clarification.
        
        Args:
            query: User query
            params: Extracted parameters
            
        Returns:
            Clarification object if needed, None otherwise
        """
        query_lower = query.lower()
        ambiguities_found = []
        
        # Check each ambiguity type
        for ambiguity_type, config in self.ambiguous_patterns.items():
            # Skip if parameter already specified
            if self._has_parameter(ambiguity_type, params):
                continue
            
            # Check if query contains vague keywords
            if any(keyword in query_lower for keyword in config['keywords']):
                ambiguities_found.append({
                    'type': ambiguity_type,
                    'priority': config['priority'],
                    'question_vi': config['question_vi'],
                    'question_en': config['question_en']
                })
        
        if not ambiguities_found:
            return None
        
        # Sort by priority (lower number = higher priority)
        ambiguities_found.sort(key=lambda x: x['priority'])
        
        # Return highest priority ambiguity
        return ambiguities_found[0]
    

    
    def _has_parameter(self, ambiguity_type: str, params: Dict[str, Any]) -> bool:
        """Check if parameter is already specified or can be inferred."""
        param_map = {
            'price_vague': ['min_budget', 'max_budget', 'price_range', 'price_level'],
            'distance_vague': ['max_distance', 'location', 'locations'],
            'quality_vague': ['min_rating', 'min_reviews'],
            'cuisine_vague': ['cuisines', 'cuisine'],
            'atmosphere_vague': ['atmosphere'],
            'time_vague': ['filter_open_now']
        }
        
        required_params = param_map.get(ambiguity_type, [])
        return any(params.get(param) for param in required_params)
    
    def should_ask_clarification(
        self, 
        query: str, 
        params: Dict[str, Any],
        previous_clarifications: int = 0,
        context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Determine if we should ask for clarification (ChatGPT-style: only when TRULY needed).
        
        PHILOSOPHY: Work with what we have. Only ask when absolutely necessary.
        - If user gives cuisine + location → search immediately
        - If user gives "rẻ" → apply default price range, don't ask
        - If user gives "gần" → apply default 3km, don't ask
        - Only ask if query is EXTREMELY vague like "quán ăn" with no context
        
        Args:
            query: User query
            params: Extracted parameters
            previous_clarifications: Number of clarifications already asked in conversation
            context: Optional conversation context from previous turns
            
        Returns:
            True if clarification needed
        """
        # CHATGPT STRATEGY: Only ask clarification when TRULY ambiguous
        # Don't ask too many clarifications in one conversation (max 1 per session)
        if previous_clarifications >= 1:
            return False
        
        # BUG #3 FIX: Merge context from previous turns to avoid re-asking
        if context and context.get('accumulated_preferences'):
            accumulated_prefs = context['accumulated_preferences']
            # Add context info to params if not already present
            if 'locations' not in params or not params['locations']:
                params['locations'] = accumulated_prefs.get('locations', [])
            if 'cuisines' not in params or not params['cuisines']:
                params['cuisines'] = accumulated_prefs.get('cuisines', [])
            if 'max_budget' not in params and 'max_budget' in accumulated_prefs:
                params['max_budget'] = accumulated_prefs['max_budget']
            if 'min_budget' not in params and 'min_budget' in accumulated_prefs:
                params['min_budget'] = accumulated_prefs['min_budget']
        
        # BUG #3 FIX: Detect and apply implicit intents BEFORE checking if clarification needed
        enriched_params = self.detect_implicit_intent(query, params)
        
        # BUG #20 FIX: Only count EXPLICIT parameters, not implicit ones
        # "quán rẻ" infers budget implicitly but still vague → should ask
        # We need explicit params from original query, not inferred
        
        # Check if params were EXPLICITLY provided (not inferred)
        has_explicit_cuisine = len(params.get('cuisines', [])) >= 1  # Original params, not enriched
        has_explicit_location = len(params.get('locations', [])) >= 1
        has_explicit_budget = params.get('max_budget') is not None or params.get('min_budget') is not None
        has_explicit_rating = params.get('min_rating') is not None
        has_explicit_distance = params.get('max_distance') is not None
        
        # Calculate quality score with EXPLICIT params only
        context_score = sum([
            2 if has_explicit_cuisine else 0,
            2 if has_explicit_location else 0,
            1 if has_explicit_budget else 0,
            1 if has_explicit_rating else 0,
            1 if has_explicit_distance else 0
        ])
        
        # BUG #20 FIX: Require 2+ SPECIFIC parameters for sufficient context
        # Test 3 requirement: "1 parameter alone should NOT be enough (need 2+)"
        # Example: "phở" (cuisine only) → ASK for location ✓
        # Example: "phở quận 1" (cuisine + location) → DON'T ask ✓
        # Example: "rẻ" (budget descriptor only) → ASK for cuisine/location ✓
        if context_score >= 4:  # Need 2+ specific params: cuisine=2 + location=2
            return False
        
        # Count EXPLICIT parameters (quality over quantity)
        explicit_param_count = sum([
            has_explicit_cuisine,
            has_explicit_location,
            has_explicit_budget,
            has_explicit_rating,
            has_explicit_distance
        ])
        
        # BUG #20 FIX: Need 2+ explicit params - single param not enough
        # "phở" alone (cuisine=1) → ASK ✓
        # "phở Quận 1" (cuisine + location = 2) → DON'T ask ✓
        if explicit_param_count >= 2:
            return False
        
        # FIXED BUG #20: Detect generic/vague queries more aggressively
        words = query.split()
        query_lower = query.lower()
        
        # Single-word queries are TOO vague (need clarification)
        if len(words) == 1:
            # Exception: If it's a specific restaurant name, don't ask
            # But food types like "buffet", "phở", "sushi" → ASK
            vague_single_words = [
                'buffet', 'phở', 'bún', 'cơm', 'bánh', 'chả', 'gà', 'bò', 'heo',
                'sushi', 'ramen', 'pizza', 'pasta', 'steak',
                'quán', 'nhà hàng', 'restaurant', 'food', 'ăn', 'eat',
                'ngon', 'rẻ', 'gần', 'xa', 'đắt', 'cheap', 'expensive',
                'nướng', 'chiên', 'luộc', 'xào', 'hấp'
            ]
            if any(word in query_lower for word in vague_single_words):
                return True  # Single vague word → ASK
        
        # 1-2 word queries with ONLY generic words
        if len(words) <= 2 and explicit_param_count == 0:
            generic_only_words = ['quán', 'nhà', 'hàng', 'restaurant', 'food', 'ăn', 'eat', 'món', 'gợi', 'ý', 'gì', 'đâu', 'nào', 'where', 'what']
            if all(word.lower() in generic_only_words for word in words):
                return True
        
        # Vague descriptors without specifics
        vague_descriptors = ['rẻ', 'đắt', 'ngon', 'tốt', 'gần', 'xa', 'cheap', 'good', 'near', 'far']
        if len(words) <= 2 and any(desc in query_lower for desc in vague_descriptors):
            if explicit_param_count < 2:  # Need at least 2 specific params
                return True  # "quán rẻ" or "gần đây" → ASK
        
        # If we reach here, query has enough information
        return False
    
    def generate_clarification_message(
        self, 
        query: str, 
        params: Dict[str, Any],
        language: str = 'vi'
    ) -> Optional[str]:
        """
        Generate clarification question message.
        
        Args:
            query: User query
            params: Extracted parameters
            language: Language for response
            
        Returns:
            Clarification message or None
        """
        ambiguity = self.detect_ambiguity(query, params)
        if not ambiguity:
            return None
        
        question_key = f'question_{language}'
        question = ambiguity.get(question_key, ambiguity['question_vi'])
        
        # Build friendly message
        if language == 'vi':
            intro = "🤔 Để tìm quán phù hợp nhất, cho tôi biết thêm nhé:\n\n"
        else:
            intro = "🤔 To find the best match, please tell me:\n\n"
        
        return intro + question
    
    def parse_clarification_response(self, response: str, clarification_type: str) -> Dict[str, Any]:
        """
        Parse user's response to clarification question.
        
        Args:
            response: User's response
            clarification_type: Type of clarification asked
            
        Returns:
            Extracted parameters from response
        """
        response_lower = response.lower()
        params = {}
        
        if clarification_type == 'price_vague':
            if any(word in response_lower for word in ['dưới 50', 'under 50', 'cực rẻ', 'very cheap']):
                params['max_budget'] = 50000
            elif any(word in response_lower for word in ['50-100', '50k-100k', 'bình dân', 'budget']):
                params['min_budget'] = 50000
                params['max_budget'] = 100000
            elif any(word in response_lower for word in ['100-200', 'trung bình', 'moderate']):
                params['min_budget'] = 100000
                params['max_budget'] = 200000
            elif any(word in response_lower for word in ['200-500', 'cao cấp', 'upscale']):
                params['min_budget'] = 200000
                params['max_budget'] = 500000
            elif any(word in response_lower for word in ['trên 500', 'over 500', 'sang trọng', 'luxury']):
                params['min_budget'] = 500000
        
        elif clarification_type == 'distance_vague':
            if any(word in response_lower for word in ['dưới 1', 'under 1', 'đi bộ', 'walking']):
                params['max_distance'] = 1.0
            elif any(word in response_lower for word in ['1-3', '1km-3km', 'xe máy', 'motorbike']):
                params['max_distance'] = 3.0
            elif any(word in response_lower for word in ['3-5', 'di chuyển dễ', 'easy']):
                params['max_distance'] = 5.0
            elif any(word in response_lower for word in ['5-10', 'chấp nhận', 'acceptable']):
                params['max_distance'] = 10.0
            elif any(word in response_lower for word in ['không quan trọng', 'doesn\'t matter', 'anywhere']):
                params['max_distance'] = None
        
        elif clarification_type == 'quality_vague':
            if any(word in response_lower for word in ['rating', '4.5', 'sao', 'star']):
                params['min_rating'] = 4.5
            elif any(word in response_lower for word in ['review', 'đông', 'popular', 'many']):
                params['min_reviews'] = 100
            elif any(word in response_lower for word in ['trending', 'nổi tiếng', 'hot', 'famous']):
                params['sort_by_trending'] = True
        
        elif clarification_type == 'cuisine_vague':
            # Extract cuisine from response
            if any(word in response_lower for word in ['việt', 'vietnamese', 'phở', 'bún', 'cơm']):
                params['cuisines'] = ['vietnamese']
            elif any(word in response_lower for word in ['nhật', 'japan', 'sushi', 'ramen']):
                params['cuisines'] = ['japanese']
            elif any(word in response_lower for word in ['hàn', 'korea', 'kimchi', 'bbq korea']):
                params['cuisines'] = ['korean']
            elif any(word in response_lower for word in ['thái', 'thai', 'tom yum']):
                params['cuisines'] = ['thai']
            elif any(word in response_lower for word in ['trung', 'chinese', 'dimsum']):
                params['cuisines'] = ['chinese']
            elif any(word in response_lower for word in ['ý', 'italy', 'pasta', 'pizza']):
                params['cuisines'] = ['italian']
            elif any(word in response_lower for word in ['pháp', 'french']):
                params['cuisines'] = ['french']
            elif any(word in response_lower for word in ['hải sản', 'seafood']):
                params['cuisines'] = ['seafood']
            elif any(word in response_lower for word in ['lẩu', 'hotpot', 'hot pot']):
                params['cuisines'] = ['hotpot']
        
        elif clarification_type == 'atmosphere_vague':
            if any(word in response_lower for word in ['lãng mạn', 'romantic', 'hẹn hò', 'date']):
                params['atmosphere'] = ['romantic']
            elif any(word in response_lower for word in ['sôi động', 'lively', 'vui', 'energetic']):
                params['atmosphere'] = ['lively']
            elif any(word in response_lower for word in ['yên tĩnh', 'quiet', 'peaceful', 'riêng tư']):
                params['atmosphere'] = ['quiet']
            elif any(word in response_lower for word in ['sang trọng', 'upscale', 'elegant', 'cao cấp']):
                params['atmosphere'] = ['luxury']
            elif any(word in response_lower for word in ['thoải mái', 'casual', 'bình dân', 'laid-back']):
                params['atmosphere'] = ['casual']
        
        elif clarification_type == 'time_vague':
            if any(word in response_lower for word in ['ngay', 'now', 'hiện tại', 'bây giờ']):
                params['filter_open_now'] = True
        
        return params


# Global instance
clarification_engine = ClarificationEngine()
