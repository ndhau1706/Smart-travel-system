"""
BUG #10 FIX: Semantic Search Hallucination Prevention

This module validates semantic search results to prevent hallucinations caused by:
1. Antonym confusion (yên tĩnh vs ồn ào)
2. Negation ignore (không phải Nhật → returns Nhật)
3. Opposite quality (sạch vs dơ)
4. Price inversion (đắt vs rẻ)
5. Location confusion (Quận 1 vs Quận 10)
6. Cuisine mix (Korean BBQ vs Japanese BBQ)
7. Atmosphere flip (sang trọng vs bình dân)
8. Time opposite (sáng vs tối)
9. Quality reverse (tệ vs ngon)
10. Semantic overlap (có WiFi vs không có WiFi)

Strategy:
- Negation detection and filtering
- Antonym pair checking
- Keyword validation (must contain required keywords)
- Exact match boosting
- Post-filtering based on query intent
"""
import re
import logging
from typing import List, Dict, Any, Tuple, Set, Optional

logger = logging.getLogger(__name__)


class SemanticValidator:
    """Validates semantic search results to prevent hallucination."""
    
    # BUG #10 FIX: Antonym pairs that should be detected and separated
    ANTONYM_PAIRS = {
        # Atmosphere
        ('yên tĩnh', 'ồn ào'), ('yên tĩnh', 'sôi động'), ('yên tĩnh', 'náo nhiệt'),
        ('quiet', 'noisy'), ('peaceful', 'loud'),
        
        # Quality
        ('sạch sẽ', 'dơ bẩn'), ('sạch', 'dơ'), ('clean', 'dirty'),
        ('ngon', 'tệ'), ('ngon', 'kém'), ('ngon', 'dở'),
        ('delicious', 'terrible'), ('good', 'bad'),
        ('tốt', 'xấu'), ('tốt', 'tệ'), ('chất lượng', 'kém chất lượng'),
        
        # Price
        ('đắt', 'rẻ'), ('đắt', 'bình dân'), ('đắt', 'giá mềm'),
        ('expensive', 'cheap'), ('luxury', 'budget'),
        ('sang trọng', 'bình dân'), ('cao cấp', 'bình dân'),
        
        # Size
        ('rộng', 'chật'), ('rộng rãi', 'nhỏ hẹp'), ('spacious', 'cramped'),
        
        # Time
        ('sáng', 'tối'), ('buổi sáng', 'buổi tối'), ('morning', 'night'),
        ('mở', 'đóng'), ('open', 'close'),
        
        # Rating
        ('5 sao', '1 sao'), ('cao', 'thấp'), ('high', 'low'),
        
        # Service
        ('nhanh', 'chậm'), ('fast', 'slow'),
        ('nhiệt tình', 'thờ ơ'), ('friendly', 'unfriendly'),
    }
    
    # BUG #10 FIX: Negation patterns (Vietnamese and English)
    NEGATION_PATTERNS = [
        r'\bkhông\b', r'\bkhông phải\b', r'\bchẳng\b', r'\bchả\b',
        r'\bnot\b', r'\bno\b', r'\bnever\b', r'\bnot?\s+\w+',
        r'\bđừng\b', r'\bcấm\b', r'\bchưa\b',
    ]
    
    # BUG #10 FIX: Location keywords for strict matching
    LOCATION_KEYWORDS = {
        'quận 1', 'q1', 'district 1',
        'quận 2', 'q2', 'district 2',
        'quận 3', 'q3', 'district 3',
        'quận 4', 'q4', 'district 4',
        'quận 5', 'q5', 'district 5',
        'quận 6', 'q6', 'district 6',
        'quận 7', 'q7', 'district 7',
        'quận 8', 'q8', 'district 8',
        'quận 9', 'q9', 'district 9',
        'quận 10', 'q10', 'district 10',
        'quận 11', 'q11', 'district 11',
        'quận 12', 'q12', 'district 12',
        'bình thạnh', 'gò vấp', 'tân bình', 'phú nhuận',
        'tân phú', 'thủ đức', 'bình tân',
    }
    
    # BUG #10 FIX: Cuisine types for strict matching
    CUISINE_KEYWORDS = {
        'nhật': ['nhật', 'japanese', 'japan', 'sushi', 'ramen', 'sashimi'],
        'hàn': ['hàn', 'korean', 'korea', 'kimchi', 'bbq hàn', 'korean bbq'],
        'trung': ['trung', 'chinese', 'china', 'dim sum', 'hủ tiếu'],
        'thái': ['thái', 'thai', 'thailand', 'tom yum'],
        'việt': ['việt', 'vietnamese', 'vietnam', 'phở', 'bún'],
        'ý': ['ý', 'italian', 'italy', 'pizza', 'pasta'],
        'pháp': ['pháp', 'french', 'france'],
        'mỹ': ['mỹ', 'american', 'america', 'burger', 'steak'],
    }
    
    # BUG #10 FIX: Binary features (WiFi, parking, etc.)
    BINARY_FEATURES = {
        'wifi': ['wifi', 'wi-fi', 'internet'],
        'parking': ['đỗ xe', 'parking', 'bãi xe', 'chỗ đậu xe'],
        'delivery': ['giao hàng', 'delivery', 'ship'],
        'outdoor': ['ngoài trời', 'outdoor', 'sân vườn'],
        'ac': ['điều hòa', 'air conditioning', 'máy lạnh'],
        'card': ['thẻ', 'card', 'credit card', 'atm'],
    }
    
    def __init__(self):
        """Initialize semantic validator."""
        # Precompile negation patterns for performance
        self._negation_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.NEGATION_PATTERNS]
        
        # Build antonym lookup for fast checking
        self._antonym_map = {}
        for word1, word2 in self.ANTONYM_PAIRS:
            self._antonym_map[word1] = word2
            self._antonym_map[word2] = word1
        
        logger.info("✅ SemanticValidator initialized with hallucination prevention")
    
    def detect_negation(self, query: str) -> Tuple[bool, List[str]]:
        """
        Detect negation in query.
        
        Args:
            query: Search query
            
        Returns:
            Tuple of (has_negation, negated_terms)
        """
        query_lower = query.lower()
        negated_terms = []
        
        for regex in self._negation_regex:
            match = regex.search(query_lower)
            if match:
                # Extract what's being negated (next 1-3 words after negation)
                start = match.end()
                remaining = query_lower[start:].strip()
                words = remaining.split()[:3]  # Get next 3 words
                
                # Filter out common stop words and "quán" (which is too generic)
                stop_words = {'quán', 'nhà', 'hàng', 'ăn', 'food', 'restaurant'}
                meaningful_words = [w for w in words if w not in stop_words]
                negated_terms.extend(meaningful_words)
        
        has_negation = len(negated_terms) > 0
        
        if has_negation:
            logger.info(f"🚫 BUG #10 FIX: Negation detected in '{query}' → negated terms: {negated_terms}")
        
        return has_negation, negated_terms
    
    def extract_required_keywords(self, query: str) -> Set[str]:
        """
        Extract keywords that MUST appear in results.
        
        Args:
            query: Search query
            
        Returns:
            Set of required keywords
        """
        query_lower = query.lower()
        required = set()
        
        # BUG #10 FIX: Location keywords are CRITICAL
        for location in self.LOCATION_KEYWORDS:
            if location in query_lower:
                required.add(location)
                logger.debug(f"📍 Required location: {location}")
        
        # BUG #10 FIX: Cuisine keywords are CRITICAL
        for cuisine, keywords in self.CUISINE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in query_lower:
                    required.add(cuisine)
                    logger.debug(f"🍽️ Required cuisine: {cuisine}")
                    break
        
        # BUG #10 FIX: Binary features are CRITICAL (WiFi, parking, etc.)
        for feature, keywords in self.BINARY_FEATURES.items():
            for keyword in keywords:
                if keyword in query_lower:
                    required.add(feature)
                    logger.debug(f"✨ Required feature: {feature}")
                    break
        
        return required
    
    def check_antonym_conflict(self, query: str, restaurant_text: str) -> bool:
        """
        Check if restaurant contains antonym of query term.
        
        Args:
            query: Search query
            restaurant_text: Restaurant description/name/features
            
        Returns:
            True if antonym conflict detected, False otherwise
        """
        query_lower = query.lower()
        restaurant_lower = restaurant_text.lower()
        
        # Check each antonym pair
        for word1, word2 in self.ANTONYM_PAIRS:
            # If query contains word1 and restaurant contains word2 (but NOT word1)
            if word1 in query_lower and word2 in restaurant_lower:
                # Make sure word1 is NOT in restaurant (to avoid false positives)
                if word1 not in restaurant_lower:
                    logger.warning(
                        f"⚠️ BUG #10 FIX: Antonym conflict! "
                        f"Query wants '{word1}' but restaurant has '{word2}' (without '{word1}')"
                    )
                    return True
            
            # Symmetric check: query contains word2, restaurant contains word1
            elif word2 in query_lower and word1 in restaurant_lower:
                if word2 not in restaurant_lower:
                    logger.warning(
                        f"⚠️ BUG #10 FIX: Antonym conflict! "
                        f"Query wants '{word2}' but restaurant has '{word1}' (without '{word2}')"
                    )
                    return True
        
        return False
    
    def validate_restaurant(
        self,
        query: str,
        restaurant: Dict[str, Any],
        required_keywords: Set[str],
        negated_terms: List[str],
        strict_mode: bool = False
    ) -> Tuple[bool, str]:
        """
        Validate if restaurant matches query intent (prevents hallucination).
        
        Args:
            query: Search query
            restaurant: Restaurant dict with name, description, cuisines, etc.
            required_keywords: Keywords that MUST appear
            negated_terms: Terms that should NOT appear
            strict_mode: If True, require ALL keywords to match
            
        Returns:
            Tuple of (is_valid, reason)
        """
        # Build searchable text from restaurant
        restaurant_text = ' '.join([
            str(restaurant.get('name', '')),
            str(restaurant.get('description', '')),
            str(restaurant.get('address', '')),
            ' '.join(restaurant.get('cuisines', [])),
            ' '.join(restaurant.get('specialties', [])),
            str(restaurant.get('atmosphere', '')),
        ]).lower()
        
        # BUG #10 FIX: Check 1 - Negation filtering
        for negated_term in negated_terms:
            if negated_term in restaurant_text:
                logger.debug(
                    f"❌ BUG #10 FIX: Restaurant '{restaurant.get('name')}' "
                    f"contains negated term '{negated_term}'"
                )
                return False, f"contains_negated_term:{negated_term}"
        
        # BUG #10 FIX: Check 2 - Antonym conflict
        if self.check_antonym_conflict(query, restaurant_text):
            return False, "antonym_conflict"
        
        # BUG #10 FIX: Check 3 - Required keyword matching
        if required_keywords:
            matched_keywords = 0
            for keyword in required_keywords:
                # Check for negated features first (e.g., "không có WiFi")
                # If restaurant text contains negation + keyword, it should NOT match
                has_negated_keyword = False
                for neg_word in ['không có', 'không', 'no ', 'without']:
                    neg_pattern = neg_word + r'[\s\w]*' + re.escape(keyword)
                    if re.search(neg_pattern, restaurant_text, re.IGNORECASE):
                        has_negated_keyword = True
                        logger.debug(
                            f"❌ BUG #10 FIX: Restaurant '{restaurant.get('name')}' "
                            f"has NEGATED keyword '{keyword}' ('{neg_word} {keyword}')"
                        )
                        break
                
                if has_negated_keyword:
                    # This is a negated keyword - do NOT count as match
                    continue
                
                # Special check for locations FIRST (strict matching - "quận 1" should not match "quận 10")
                if keyword in self.LOCATION_KEYWORDS:
                    # Use word boundary check for strict location matching
                    # "quận 1" should match "Quận 1" but NOT "Quận 10"
                    # Pattern: \bquận\s+1\b (word boundary on both sides)
                    location_pattern = r'\b' + re.escape(keyword).replace(r'\ ', r'\s+') + r'\b'
                    if re.search(location_pattern, restaurant_text, re.IGNORECASE):
                        matched_keywords += 1
                # Special check for cuisines (match against cuisine list)
                elif 'cuisines' in restaurant and keyword in self.CUISINE_KEYWORDS:
                    cuisine_words = self.CUISINE_KEYWORDS[keyword]
                    restaurant_cuisines_lower = [c.lower() for c in restaurant.get('cuisines', [])]
                    if any(cw in ' '.join(restaurant_cuisines_lower) for cw in cuisine_words):
                        matched_keywords += 1
                # Check in restaurant text (for other keywords)
                elif keyword in restaurant_text:
                    matched_keywords += 1
            
            if strict_mode:
                # ALL keywords must match
                if matched_keywords < len(required_keywords):
                    missing = []
                    for k in required_keywords:
                        if k in self.LOCATION_KEYWORDS:
                            pattern = r'\b' + re.escape(k).replace(r'\ ', r'\s+') + r'\b'
                            if not re.search(pattern, restaurant_text, re.IGNORECASE):
                                missing.append(k)
                        elif k not in restaurant_text:
                            missing.append(k)
                    
                    logger.debug(
                        f"❌ BUG #10 FIX: Restaurant '{restaurant.get('name')}' "
                        f"missing required keywords: {missing}"
                    )
                    return False, f"missing_keywords:{set(missing)}"
            else:
                # At least ONE keyword must match (for multi-keyword queries)
                if len(required_keywords) > 1 and matched_keywords == 0:
                    logger.debug(
                        f"❌ BUG #10 FIX: Restaurant '{restaurant.get('name')}' "
                        f"has ZERO matching keywords from: {required_keywords}"
                    )
                    return False, f"no_keyword_match"
        
        # All checks passed
        return True, "valid"
    
    def filter_results(
        self,
        query: str,
        restaurants: List[Dict[str, Any]],
        confidence_threshold: float = 0.5
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        BUG #10 FIX: Filter semantic search results to prevent hallucination.
        
        Args:
            query: Search query
            restaurants: List of restaurant dicts
            confidence_threshold: Minimum confidence to keep result (0-1)
            
        Returns:
            Tuple of (filtered_restaurants, validation_stats)
        """
        # Parse query for validation criteria
        has_negation, negated_terms = self.detect_negation(query)
        required_keywords = self.extract_required_keywords(query)
        
        # Determine strict mode
        # Use strict mode for specific queries (location, cuisine, features)
        strict_mode = len(required_keywords) > 0
        
        logger.info(
            f"🔍 BUG #10 FIX: Validating {len(restaurants)} results for query '{query}' "
            f"(negation={has_negation}, required={required_keywords}, strict={strict_mode})"
        )
        
        # Filter restaurants
        filtered = []
        rejected = []
        rejection_reasons = {}
        
        for restaurant in restaurants:
            is_valid, reason = self.validate_restaurant(
                query=query,
                restaurant=restaurant,
                required_keywords=required_keywords,
                negated_terms=negated_terms,
                strict_mode=strict_mode
            )
            
            if is_valid:
                filtered.append(restaurant)
            else:
                rejected.append(restaurant)
                rejection_reasons[restaurant.get('name', 'unknown')] = reason
        
        # Log validation results
        if rejected:
            logger.warning(
                f"⚠️ BUG #10 FIX: Filtered out {len(rejected)}/{len(restaurants)} "
                f"hallucinated results. Reasons: {rejection_reasons}"
            )
        
        validation_stats = {
            'total_input': len(restaurants),
            'passed': len(filtered),
            'rejected': len(rejected),
            'rejection_reasons': rejection_reasons,
            'has_negation': has_negation,
            'negated_terms': negated_terms,
            'required_keywords': list(required_keywords),
            'strict_mode': strict_mode,
        }
        
        return filtered, validation_stats


# Global instance
semantic_validator = SemanticValidator()
