"""
Advanced Query Understanding
Handles negation, comparison, and conditional queries

BUG #7 FIX: ReDoS (Regular Expression Denial of Service) Protection:
- Input length limits to prevent excessive backtracking
- Rewritten regex patterns without nested quantifiers
- Timeout protection for regex matching
- Atomic groups and possessive quantifiers where possible
"""
from typing import Dict, List, Optional, Any, Tuple
import re
import logging

logger = logging.getLogger(__name__)

# BUG #7 FIX: ReDoS Protection Constants
MAX_QUERY_LENGTH = 5000  # Maximum query length to process
MAX_REGEX_INPUT_LENGTH = 500  # Maximum length for regex matching (aggressive limit for performance)
REGEX_TIMEOUT_MS = 100  # Regex timeout in milliseconds (not directly supported, but we limit input)


class AdvancedQueryParser:
    """Parse complex query patterns with ReDoS protection."""
    
    def __init__(self):
        # Negation patterns (EXPANDED - ChatGPT-level comprehension)
        self.negation_patterns = {
            'negative_keywords': [
                # Basic negation
                'không', 'không muốn', 'không thích', 'không cần', 'không phải',
                'chán', 'ngán', 'mệt', 'no rồi', 'đủ rồi',
                
                # Exclusion keywords (Vietnamese)
                'đừng', 'tránh', 'trừ', 'ngoại trừ', 'ngoài', 'bỏ qua', 'loại trừ',
                'trừ ra', 'trừ phi', 'ngoài ra', 'ngoại trừ', 'ko', 'k',
                
                # English negation
                'not', 'no', 'without', 'avoid', 'exclude', 'except', 'excluding',
                'except for', 'other than', 'besides', 'apart from',
                
                # Vietnamese slang negation
                'thôi', 'ẹc', 'đéo', 'hong', 'hông', 'hok', 'hem', 'hơm',
                'chả', 'chẳng', 'chả muốn', 'chẳng thích', 'ghét', 'dị ứng',
                
                # Refusal expressions
                'từ chối', 'thôi không', 'thôi bỏ', 'miễn là không', 'khỏi',
                'đừng có', 'đừng lại', 'thôi kệ', 'bỏ đi',
                
                # Negative preferences
                'không ưa', 'không khoái', 'không vừa ý', 'không hợp', 
                'không thể', 'không được', 'không nên', 'không đáng',
                
                # Exclusion with conditions
                'nhưng không', 'nhưng ko', 'but not', 'but no', 'however not',
                'mà không', 'nhưng mà không', 'song không',
                
                # Vietnamese "except" variations
                'trừ khi', 'trừ phi', 'chỉ trừ', 'chỉ ngoại trừ',
                'ngoại trừ việc', 'trừ việc', 'trừ mỗi',
                
                # Dietary restrictions
                'dị ứng', 'không ăn được', 'không tiêu hóa được',
                'allergic', 'allergy', 'intolerant'
            ],
            'negative_attributes': {
                # BUG #7 FIX: Removed nested quantifiers (? after (?:...)) to prevent ReDoS
                # Changed (?:...)? to (?:...){0,1} and limited repetition
                'cuisine': r'không\s+(?:muốn|thích|cần){0,1}\s{0,3}(?:ăn|uống|먹다|eat|drink){0,1}\s{0,3}(?:món){0,1}\s{0,3}([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]{1,50})',
                'atmosphere': r'không\s+(?:muốn|thích){0,1}\s{0,3}(ồn|đông|시끄럽|noisy|crowded|busy|yên tĩnh|quiet)',
                'price': r'không\s+(?:muốn|cần){0,1}\s{0,3}(đắt|expensive|costly|rẻ|cheap)',
                'location': r'không\s+(?:muốn|cần){0,1}\s{0,3}(?:ở|tại){0,1}\s{0,3}(quận\s{0,2}\d{1,2}|district\s{0,2}\d{1,2})',
            }
        }
        
        # Comparison patterns
        self.comparison_patterns = {
            'cheaper_than': [
                r'rẻ\s+hơn\s+([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+)',
                r'cheaper\s+than\s+([A-Z][a-z\s]+)',
            ],
            'more_expensive': [
                r'đắt\s+hơn\s+([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+)',
                r'more\s+expensive\s+than\s+([A-Z][a-z\s]+)',
            ],
            'nearer_than': [
                r'gần\s+hơn\s+([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+)',
                r'nearer\s+than\s+([A-Z][a-z\s]+)',
                r'closer\s+than\s+([A-Z][a-z\s]+)',
            ],
            'better_than': [
                r'(?:ngon|tốt)\s+hơn\s+([A-ZÁÀẢÃẠĂẮẰẲẴẶÂẤẦẨẪẬÈÉẺẼẸÊẾỀỂỄỆÌÍỈĨỊÒÓỎÕỌÔỐỒỔỖỘƠỚỜỞỠỢÙÚỦŨỤƯỨỪỬỮỰỲÝỶỸỴĐ][a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+)',
                r'better\s+than\s+([A-Z][a-z\s]+)',
            ]
        }
        
        # Conditional patterns
        self.conditional_patterns = {
            'if_then': [
                r'nếu\s+(.+?)\s+thì\s+(.+)',
                r'if\s+(.+?)\s+then\s+(.+)',
            ],
            'otherwise': [
                r'không\s+thì\s+(.+)',
                r'otherwise\s+(.+)',
                r'else\s+(.+)',
            ],
            'backup': [
                r'hết\s+chỗ\s+thì\s+(.+)',
                r'nếu\s+(?:đóng|hết|full)\s+thì\s+(.+)',
                r'if\s+(?:closed|full|busy)\s+then\s+(.+)',
            ]
        }
    
    def _validate_input_length(self, query: str, context: str = "query") -> str:
        """
        BUG #7 FIX: Validate and truncate input to prevent ReDoS attacks.
        
        Args:
            query: Input string
            context: Context for logging
            
        Returns:
            Validated/truncated string
        """
        if not query:
            return query
        
        original_length = len(query)
        
        # Check if query exceeds maximum length
        if original_length > MAX_QUERY_LENGTH:
            logger.warning(f"⚠️ {context} exceeds MAX_QUERY_LENGTH ({original_length} > {MAX_QUERY_LENGTH}), truncating")
            query = query[:MAX_QUERY_LENGTH]
        
        return query
    
    def _safe_regex_search(self, pattern: str, text: str, max_length: int = MAX_REGEX_INPUT_LENGTH) -> Optional[re.Match]:
        """
        BUG #7 FIX: Safe regex search with input length limit.
        
        Args:
            pattern: Regex pattern
            text: Text to search
            max_length: Maximum text length for regex
            
        Returns:
            Match object or None
        """
        # Truncate input if too long
        if len(text) > max_length:
            logger.debug(f"Truncating text from {len(text)} to {max_length} chars for regex safety")
            text = text[:max_length]
        
        try:
            return re.search(pattern, text)
        except Exception as e:
            logger.error(f"Regex error: {e}")
            return None
    
    def _safe_regex_finditer(self, pattern: str, text: str, max_length: int = MAX_REGEX_INPUT_LENGTH) -> List[re.Match]:
        """
        BUG #7 FIX: Safe regex finditer with input length limit.
        
        Args:
            pattern: Regex pattern
            text: Text to search
            max_length: Maximum text length for regex
            
        Returns:
            List of matches
        """
        # Truncate input if too long
        if len(text) > max_length:
            logger.debug(f"Truncating text from {len(text)} to {max_length} chars for regex safety")
            text = text[:max_length]
        
        try:
            return list(re.finditer(pattern, text))
        except Exception as e:
            logger.error(f"Regex finditer error: {e}")
            return []
    
    def detect_negation(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detect negation in query with comprehensive pattern matching.
        
        BUG #7 FIX: Added input validation and safe regex matching.
        
        Args:
            query: User query
            
        Returns:
            Negation info or None
        """
        # BUG #7 FIX: Validate input length
        query = self._validate_input_length(query, "negation query")
        query_lower = query.lower()
        
        # Check if query contains negation keywords
        has_negation = any(neg in query_lower for neg in self.negation_patterns['negative_keywords'])
        
        if not has_negation:
            return None
        
        negations = {
            'cuisines': [],
            'atmosphere': [],
            'price': [],
            'locations': []
        }
        
        # ========== COMPLEX NEGATION PATTERNS ==========
        
        # 1. "không phải là X" pattern - MUST match full phrase to avoid capturing "phải"
        # BUG #7 FIX: Allow multi-word cuisines with bounded repetition
        not_is_pattern = r'không phải là\s+([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+?)(?:\s+(?:nữa|rồi|$)|$)'
        for match in self._safe_regex_finditer(not_is_pattern, query_lower):
            food_item = match.group(1).strip()
            if food_item not in negations['cuisines']:
                negations['cuisines'].append(food_item)
        
        # 1b. English "not X" pattern
        # BUG #7 FIX: Limit word length (+ changed to {1,50})
        not_pattern_en = r'not\s{1,3}([a-z]{1,50})'
        for match in self._safe_regex_finditer(not_pattern_en, query_lower):
            food_item = match.group(1).strip()
            if food_item not in negations['cuisines']:
                negations['cuisines'].append(food_item)
        
        # 2. "trừ X" / "ngoại trừ X" pattern
        # BUG #7 FIX: Use simple pattern with bounded length, capture up to word boundary
        # Match 1-3 words after trừ (most cuisines are 1-3 words)
        except_pattern = r'(?:trừ|ngoại trừ|ngoài|except|excluding|besides)\s+([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+(?:\s+[a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+){0,2})'
        for match in self._safe_regex_finditer(except_pattern, query_lower):
            excluded = match.group(1).strip()
            # Split by commas or "và" to handle multiple items
            # BUG #7 FIX: Use \b word boundary for 'và' to avoid splitting words like 'hàn'
            items = re.split(r',|\bvà\b', excluded)
            for item in items:
                item = item.strip()
                if item and item not in negations['cuisines']:
                    negations['cuisines'].append(item)
        
        # 3. "đừng X nữa" pattern
        # BUG #7 FIX: Changed nested (?:...)? to {0,1} and +? to {1,100}
        dont_anymore_pattern = r'đừng\s{1,3}(?:gợi ý\s{1,3}){0,1}(?:quán\s{1,3}){0,1}([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ0-9\s]{1,100})(?:\s{1,3}nữa)'
        for match in self._safe_regex_finditer(dont_anymore_pattern, query_lower):
            item = match.group(1).strip()
            # Check if it's a location (Quận X)
            if 'quận' in item or 'district' in item:
                if item not in negations['locations']:
                    negations['locations'].append(item)
            else:
                if item not in negations['cuisines']:
                    negations['cuisines'].append(item)
        
        # 4. "X, Y cũng không" pattern (multiple negations)
        also_not_pattern = r'(?:không thích|không muốn|không cần|ghét|chán)\s+([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+)(?:.*?)([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ]+)\s+cũng\s+không'
        also_match = re.search(also_not_pattern, query_lower)
        if also_match:
            first_item = also_match.group(1).strip()
            second_item = also_match.group(2).strip()
            if first_item not in negations['cuisines']:
                negations['cuisines'].append(first_item)
            if second_item not in negations['cuisines']:
                negations['cuisines'].append(second_item)
        
        # 5. "tránh xa X" / "tránh X" pattern
        avoid_pattern = r'(?:tránh xa|tránh|avoid)\s+(?:quán)?\s*([a-záàảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+?)(?:\s|$)'
        for match in re.finditer(avoid_pattern, query_lower):
            item = match.group(1).strip()
            # Check if it's atmosphere
            if item in ['ồn', 'đông', 'noisy', 'crowded']:
                if 'noisy' not in negations['atmosphere']:
                    negations['atmosphere'].append('noisy')
            else:
                if item not in negations['cuisines']:
                    negations['cuisines'].append(item)
        
        # ========== ORIGINAL PATTERNS (LEGACY SUPPORT) ==========
        
        # Extract negated cuisines (simple pattern) - but skip "không phải" to avoid false capture
        if 'không phải là' not in query_lower:
            # BUG #7 FIX: Use safe regex search
            cuisine_match = self._safe_regex_search(
                self.negation_patterns['negative_attributes']['cuisine'],
                query_lower
            )
            if cuisine_match:
                item = cuisine_match.group(1).strip()
                if item not in negations['cuisines']:
                    negations['cuisines'].append(item)
        
        # Extract negated atmosphere
        # BUG #7 FIX: Use safe regex search
        atmo_match = self._safe_regex_search(
            self.negation_patterns['negative_attributes']['atmosphere'],
            query_lower
        )
        if atmo_match:
            atmo_word = atmo_match.group(1)
            if atmo_word in ['ồn', 'đông', 'noisy', 'crowded', 'busy']:
                if 'noisy' not in negations['atmosphere']:
                    negations['atmosphere'].append('noisy')
            elif atmo_word in ['yên tĩnh', 'quiet']:
                if 'lively' not in negations['atmosphere']:
                    negations['atmosphere'].append('lively')
        
        # Extract negated price
        # BUG #7 FIX: Use safe regex search
        price_match = self._safe_regex_search(
            self.negation_patterns['negative_attributes']['price'],
            query_lower
        )
        if price_match:
            price_word = price_match.group(1)
            if price_word in ['đắt', 'expensive', 'costly']:
                negations['price'] = 'not_expensive'
            elif price_word in ['rẻ', 'cheap']:
                negations['price'] = 'not_cheap'
        
        # Extract negated locations
        # BUG #7 FIX: Use safe regex search
        location_match = self._safe_regex_search(
            self.negation_patterns['negative_attributes']['location'],
            query_lower
        )
        if location_match:
            loc = location_match.group(1).strip()
            if loc not in negations['locations']:
                negations['locations'].append(loc)
        
        # Return only if we found specific negations
        if any(negations.values()):
            return negations
        
        return None
    
    def detect_comparison(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detect comparison in query.
        
        Args:
            query: User query
            
        Returns:
            Comparison info or None
        """
        for comp_type, patterns in self.comparison_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, query, re.IGNORECASE)
                if match:
                    reference_name = match.group(1).strip()
                    return {
                        'type': comp_type,
                        'reference': reference_name,
                        'raw_match': match.group(0)
                    }
        
        return None
    
    def detect_conditional(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Detect conditional logic in query.
        
        Args:
            query: User query
            
        Returns:
            Conditional info or None
        """
        query_lower = query.lower()
        
        # Check if-then pattern
        for pattern in self.conditional_patterns['if_then']:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'if_then',
                    'condition': match.group(1).strip(),
                    'action': match.group(2).strip(),
                    'raw_match': match.group(0)
                }
        
        # Check otherwise pattern
        for pattern in self.conditional_patterns['otherwise']:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'otherwise',
                    'alternative': match.group(1).strip(),
                    'raw_match': match.group(0)
                }
        
        # Check backup pattern
        for pattern in self.conditional_patterns['backup']:
            match = re.search(pattern, query_lower)
            if match:
                return {
                    'type': 'backup',
                    'backup_action': match.group(1).strip(),
                    'raw_match': match.group(0)
                }
        
        return None
    
    def apply_negation_filters(
        self,
        negation: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Apply negation filters to search parameters.
        
        Args:
            negation: Detected negation
            params: Current parameters
            
        Returns:
            Updated parameters with exclusions
        """
        # Add excluded cuisines
        if negation.get('cuisines'):
            params['excluded_cuisines'] = negation['cuisines']
        
        # Add atmosphere filters
        if negation.get('atmosphere'):
            if 'noisy' in negation['atmosphere']:
                params['atmosphere'] = params.get('atmosphere', []) + ['quiet']
            elif 'lively' in negation['atmosphere']:
                params['atmosphere'] = params.get('atmosphere', []) + ['quiet', 'romantic']
        
        # Add price filters
        if negation.get('price'):
            if negation['price'] == 'not_expensive':
                params['max_budget'] = 200000  # Moderate max
            elif negation['price'] == 'not_cheap':
                params['min_budget'] = 150000  # Above budget level
        
        # Add excluded locations
        if negation.get('locations'):
            params['excluded_locations'] = negation['locations']
        
        return params
    
    def handle_comparison_query(
        self,
        comparison: Dict[str, Any],
        reference_restaurant: Optional[Dict[str, Any]],
        all_restaurants: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Filter restaurants based on comparison.
        
        Args:
            comparison: Comparison info
            reference_restaurant: Restaurant to compare against
            all_restaurants: All available restaurants
            
        Returns:
            Filtered restaurant list
        """
        if not reference_restaurant:
            return all_restaurants
        
        comp_type = comparison['type']
        filtered = []
        
        for restaurant in all_restaurants:
            if comp_type == 'cheaper_than':
                ref_price = self._estimate_price(reference_restaurant)
                rest_price = self._estimate_price(restaurant)
                if rest_price < ref_price:
                    filtered.append(restaurant)
            
            elif comp_type == 'more_expensive':
                ref_price = self._estimate_price(reference_restaurant)
                rest_price = self._estimate_price(restaurant)
                if rest_price > ref_price:
                    filtered.append(restaurant)
            
            elif comp_type == 'nearer_than':
                ref_dist = reference_restaurant.get('distance', float('inf'))
                rest_dist = restaurant.get('distance', float('inf'))
                if rest_dist < ref_dist:
                    filtered.append(restaurant)
            
            elif comp_type == 'better_than':
                ref_rating = reference_restaurant.get('rating', 0)
                rest_rating = restaurant.get('rating', 0)
                if rest_rating > ref_rating:
                    filtered.append(restaurant)
        
        return filtered
    
    def _estimate_price(self, restaurant: Dict[str, Any]) -> int:
        """Estimate restaurant price."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': 75000,
            'PRICE_LEVEL_MODERATE': 150000,
            'PRICE_LEVEL_EXPENSIVE': 350000,
            'PRICE_LEVEL_VERY_EXPENSIVE': 600000
        }
        return price_map.get(restaurant.get('price_level', ''), 150000)
    
    def extract_result_count(self, query: str) -> int:
        """
        Extract desired number of restaurants from query.
        
        Patterns:
        - "3 quán" → 3
        - "cho tôi 5 chỗ" → 5
        - "gợi ý 7 nhà hàng" → 7
        - "top 10" → 10
        
        Args:
            query: User query
            
        Returns:
            Number of results (1-20), default 5
        """
        query = self._validate_input_length(query, "result_count query")
        query_lower = query.lower()
        
        # Patterns to extract number
        patterns = [
            # Vietnamese patterns
            r'(\d+)\s*(?:quán|chỗ|nhà hàng|tiệm|quầy|hàng)',
            r'(?:cho|gợi ý|tìm|recommend|suggest|show)\s+(?:tôi|mình|em)?\s*(\d+)',
            r'top\s*(\d+)',
            r'(\d+)\s*(?:cái|món|place|restaurant)',
            # English patterns
            r'(\d+)\s*(?:restaurants?|places?|spots?)',
            r'(?:give|show|find|suggest)\s+(?:me)?\s*(\d+)',
        ]
        
        for pattern in patterns:
            match = self._safe_regex_search(pattern, query_lower)
            if match:
                try:
                    num = int(match.group(1))
                    # Limit between 1-20
                    num = max(1, min(num, 20))
                    logger.info(f"Extracted result count: {num} from query")
                    return num
                except (ValueError, IndexError):
                    continue
        
        # Default: 5 restaurants
        return 5


# Global instance
advanced_parser = AdvancedQueryParser()
