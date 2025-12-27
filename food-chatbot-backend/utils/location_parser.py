"""
BUG #14 FIX: Advanced Location Parser
Fixes location extraction errors for complex and ambiguous addresses.

Solves 10 scenarios:
1. Ambiguous District: "Quận 10 11" (address) vs actual district
2. Street Name: "Đường Quận 1" (street name contains "Quận")
3. Restaurant Name: "Phở Quận 7" (restaurant name)
4. Multiple Locations: "Quận 1 hoặc Quận 3"
5. Nested Location: "Gần Bến Thành, Quận 1"
6. Abbreviation: "Q1" → "Quận 1"
7. Old Name: "Sài Gòn" → "TP.HCM"
8. English Mix: "District 1" → "Quận 1"
9. Typo: "Quậnn 1" → "Quận 1" (fuzzy matching)
10. Landmark: "Gần Landmark 81" → "Quận Bình Thạnh"
"""

import re
from typing import List, Set, Tuple, Optional
from difflib import get_close_matches


class LocationParser:
    """Context-aware location extraction with fuzzy matching and landmark support."""
    
    # Valid HCMC districts (1-12 + special districts)
    VALID_DISTRICTS = {
        'quận 1', 'quận 2', 'quận 3', 'quận 4', 'quận 5', 'quận 6',
        'quận 7', 'quận 8', 'quận 9', 'quận 10', 'quận 11', 'quận 12',
        'bình thạnh', 'tân bình', 'tân phú', 'phú nhuận', 'gò vấp',
        'bình tân', 'thủ đức', 'hóc môn', 'củ chi', 'bình chánh',
        'nhà bè', 'cần giờ'
    }
    
    # District abbreviations
    ABBREVIATIONS = {
        'q1': 'quận 1', 'q2': 'quận 2', 'q3': 'quận 3', 'q4': 'quận 4',
        'q5': 'quận 5', 'q6': 'quận 6', 'q7': 'quận 7', 'q8': 'quận 8',
        'q9': 'quận 9', 'q10': 'quận 10', 'q11': 'quận 11', 'q12': 'quận 12',
    }
    
    # English to Vietnamese mapping
    ENGLISH_MAPPING = {
        'district 1': 'quận 1', 'district 2': 'quận 2', 'district 3': 'quận 3',
        'district 4': 'quận 4', 'district 5': 'quận 5', 'district 6': 'quận 6',
        'district 7': 'quận 7', 'district 8': 'quận 8', 'district 9': 'quận 9',
        'district 10': 'quận 10', 'district 11': 'quận 11', 'district 12': 'quận 12',
    }
    
    # Old names / Alternative names
    OLD_NAMES = {
        'sài gòn': 'tp.hcm',
        'tp.hcm': 'tp.hcm',
        'hồ chí minh': 'tp.hcm',
        'saigon': 'tp.hcm',
    }
    
    # Landmark to district mapping
    LANDMARKS = {
        'landmark 81': 'bình thạnh',
        'landmark81': 'bình thạnh',
        'bitexco': 'quận 1',
        'bến thành': 'quận 1',
        'chợ bến thành': 'quận 1',
        'nhà thờ đức bà': 'quận 1',
        'bưu điện trung tâm': 'quận 1',
        'dinh độc lập': 'quận 1',
        'phố đi bộ nguyễn huệ': 'quận 1',
        'đường sách': 'quận 1',
        'phạm ngũ lão': 'quận 1',
        'bùi viện': 'quận 1',
        'vivo city': 'quận 7',
        'crescent mall': 'quận 7',
        'phú mỹ hưng': 'quận 7',
        'aeon mall': 'tân phú',
        'đầm sen': 'quận 11',
        'văn thánh': 'bình thạnh',
        'vincom center': 'quận 1',
    }
    
    # Restaurant name patterns (to avoid false positives)
    RESTAURANT_NAME_PATTERNS = [
        r'^phở\s+quận\s+\d+',  # "Phở Quận 7" at start
        r'^bún\s+quận\s+\d+',  # "Bún Quận 10"
        r'^quán\s+quận\s+\d+', # "Quán Quận 3"
        r'^cơm\s+quận\s+\d+',  # "Cơm Quận 1"
        r'^lẩu\s+quận\s+\d+',  # "Lẩu Quận 2"
    ]
    
    # Street name indicators (to avoid false positives)
    STREET_INDICATORS = [
        r'đường\s+quận\s+\d+',  # "Đường Quận 1"
        r'đ\.\s*quận\s+\d+',    # "Đ. Quận 1"
        r'street\s+quận\s+\d+', # "Street Quận 1"
    ]
    
    # Address number patterns (to avoid "10-11" being parsed as districts)
    ADDRESS_NUMBER_PATTERNS = [
        r'\d+-\d+\s+(?:đường|street|đ\.)',  # "10-11 Đường X"
        r'số\s+\d+-\d+',                     # "Số 10-11"
        r'\d+/\d+',                          # "10/11" (building/street)
    ]
    
    # Typo corrections (fuzzy matching candidates)
    TYPO_CANDIDATES = {
        'quận': ['quậnn', 'quân', 'quan', 'quậng', 'quậm'],
        'district': ['distict', 'distrct', 'distirct'],
    }
    
    def __init__(self):
        """Initialize location parser with caching."""
        self._cache = {}  # Cache for parsed locations
    
    def extract_locations(self, text: str) -> List[str]:
        """
        Extract location mentions from text with context awareness.
        
        Args:
            text: Input query text
            
        Returns:
            List of normalized district names
        """
        # BUG #14 FIX: Cache check
        cache_key = text.lower()
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        locations = set()
        text_lower = text.lower()
        
        # SCENARIO #7: Old names / Alternative names
        for old_name, canonical in self.OLD_NAMES.items():
            if old_name in text_lower:
                locations.add(canonical)
        
        # SCENARIO #10: Landmark mapping
        for landmark, district in self.LANDMARKS.items():
            if landmark in text_lower:
                locations.add(district)
        
        # SCENARIO #6: Abbreviations (Q1 → Quận 1)
        for abbr, full in self.ABBREVIATIONS.items():
            # Use word boundary to avoid matching "q10" in "Q101"
            pattern = r'\b' + re.escape(abbr) + r'\b'
            if re.search(pattern, text_lower):
                # BUG #14 FIX: Check context before adding
                if not self._is_false_positive(text_lower, abbr):
                    locations.add(full)
        
        # SCENARIO #8: English "District 1" → "Quận 1"
        for en, vi in self.ENGLISH_MAPPING.items():
            if en in text_lower:
                if not self._is_false_positive(text_lower, en):
                    locations.add(vi)
        
        # SCENARIO #9: Fuzzy matching for typos
        # Extract potential typo patterns
        typo_matches = self._extract_with_fuzzy_matching(text_lower)
        locations.update(typo_matches)
        
        # SCENARIO #1, 2, 3, 4, 5: Standard extraction with context checks
        standard_matches = self._extract_standard_districts(text_lower)
        locations.update(standard_matches)
        
        # BUG #14 FIX: Validate all extracted locations
        validated = [loc for loc in locations if loc in self.VALID_DISTRICTS or loc == 'tp.hcm']
        
        # Cache result
        self._cache[cache_key] = validated
        
        return validated
    
    def _extract_standard_districts(self, text: str) -> Set[str]:
        """
        Extract districts using standard patterns with context validation.
        
        Handles:
        - SCENARIO #1: Ambiguous "Quận 10 11" (address)
        - SCENARIO #2: "Đường Quận 1" (street name)
        - SCENARIO #3: "Phở Quận 7" (restaurant name)
        - SCENARIO #4: "Quận 1 hoặc Quận 3" (multiple)
        - SCENARIO #5: "Gần Bến Thành, Quận 1" (nested)
        """
        locations = set()
        
        # BUG #14 FIX: Context-aware patterns
        # Pattern 1: "Quận X" or "quận X"
        district_pattern = r'quận\s+(\d{1,2})'
        matches = re.finditer(district_pattern, text)
        
        for match in matches:
            district_num = match.group(1)
            district_name = f"quận {district_num}"
            start_pos = match.start()
            end_pos = match.end()
            
            # SCENARIO #1: Check for address number pattern (10-11)
            # Look ahead for "-number" pattern
            ahead_pattern = r'^\s*-?\s*\d+\s+(?:đường|street|đ\.|nguyễn|lê|trần)'
            text_ahead = text[end_pos:end_pos+30]
            if re.match(ahead_pattern, text_ahead):
                # This is likely an address "10-11 Đường X", skip
                continue
            
            # SCENARIO #2: Check for street name indicator
            # Look behind for "đường", "đ.", "street"
            behind_pattern = r'(?:đường|street|đ\.)\s+$'
            text_behind = text[max(0, start_pos-20):start_pos]
            if re.search(behind_pattern, text_behind):
                # This is "Đường Quận X", skip
                continue
            
            # SCENARIO #3: Check for restaurant name pattern
            # Look behind for food words AT START of text or after sentence boundary
            behind_food_pattern = r'(?:^|[.!?]\s*)(?:phở|bún|quán|cơm|lẩu|bánh|chè)\s+$'
            # Expand context to check from start
            text_behind_food = text[:start_pos]
            # Check if this is at start: "Phở Quận 7" or "Tìm Phở Quận 7"
            # Check last 20 chars for food word
            last_20 = text_behind_food[-20:] if len(text_behind_food) > 20 else text_behind_food
            
            # BUG #14 FIX: More specific restaurant name check
            # Only skip if:
            # 1. Food word IMMEDIATELY before (Phở Quận 7)
            # 2. At beginning of query (^Phở Quận 7)
            if re.search(r'(?:phở|bún|quán|cơm|lẩu|bánh|chè)\s+$', last_20):
                # Check if there's location context word nearby (ở, tại, gần)
                # If yes, it's a location, not restaurant name
                context_pattern = r'(?:ở|tại|gần|quanh|tìm.*ở)\s+'
                # Look further back for context
                text_behind_long = text[:start_pos]
                if not re.search(context_pattern, text_behind_long[-50:] if len(text_behind_long) > 50 else text_behind_long):
                    # No location context, likely restaurant name
                    continue
            
            # Passed all context checks, add district
            if int(district_num) <= 12:  # Valid districts 1-12
                locations.add(district_name)
        
        # SCENARIO #4: Multiple locations with "hoặc", "hay", "or"
        # Already handled above - all valid matches are added
        
        # SCENARIO #5: Nested locations with landmarks
        # Extract from common area names
        for area in ['bến thành', 'bình thạnh', 'tân bình', 'phú nhuận', 'gò vấp',
                     'bình tân', 'tân phú', 'thủ đức']:
            if area in text:
                locations.add(area)
        
        return locations
    
    def _extract_with_fuzzy_matching(self, text: str) -> Set[str]:
        """
        SCENARIO #9: Fuzzy matching for typos ("Quậnn 1" → "Quận 1").
        
        Uses difflib to find close matches for common typos.
        """
        locations = set()
        
        # Extract potential typo words
        words = text.split()
        
        for i, word in enumerate(words):
            # Check if word is close to "quận" or "district"
            if self._is_fuzzy_match(word, ['quận', 'quan'], cutoff=0.75):
                # Look for number after the typo
                if i + 1 < len(words):
                    next_word = words[i + 1]
                    # Check if next word is a number
                    if next_word.isdigit() and 1 <= int(next_word) <= 12:
                        district_name = f"quận {next_word}"
                        # Check context before adding
                        if not self._is_false_positive(text, district_name):
                            locations.add(district_name)
        
        return locations
    
    def _is_fuzzy_match(self, word: str, candidates: List[str], cutoff: float = 0.8) -> bool:
        """Check if word is a fuzzy match for any candidate."""
        matches = get_close_matches(word, candidates, n=1, cutoff=cutoff)
        return len(matches) > 0
    
    def _is_false_positive(self, text: str, location: str) -> bool:
        """
        Check if location mention is a false positive.
        
        Returns True if:
        - Part of restaurant name
        - Part of street name
        - Part of address number
        """
        # Check restaurant name patterns
        for pattern in self.RESTAURANT_NAME_PATTERNS:
            if re.search(pattern, text):
                return True
        
        # Check street indicators
        for pattern in self.STREET_INDICATORS:
            if re.search(pattern, text):
                return True
        
        # Check address number patterns
        for pattern in self.ADDRESS_NUMBER_PATTERNS:
            if re.search(pattern, text):
                return True
        
        return False
    
    def normalize_location(self, location: str) -> str:
        """
        Normalize location to canonical form.
        
        Examples:
        - "Q1" → "quận 1"
        - "District 7" → "quận 7"
        - "Sài Gòn" → "tp.hcm"
        """
        location_lower = location.lower().strip()
        
        # Check abbreviations
        if location_lower in self.ABBREVIATIONS:
            return self.ABBREVIATIONS[location_lower]
        
        # Check English
        if location_lower in self.ENGLISH_MAPPING:
            return self.ENGLISH_MAPPING[location_lower]
        
        # Check old names
        if location_lower in self.OLD_NAMES:
            return self.OLD_NAMES[location_lower]
        
        # Check landmarks
        if location_lower in self.LANDMARKS:
            return self.LANDMARKS[location_lower]
        
        # Return as-is if already normalized
        if location_lower in self.VALID_DISTRICTS:
            return location_lower
        
        return location_lower
    
    def clear_cache(self):
        """Clear the location parsing cache."""
        self._cache.clear()


# Singleton instance
_location_parser = LocationParser()


def extract_locations_advanced(text: str) -> List[str]:
    """
    BUG #14 FIX: Advanced location extraction with context awareness.
    
    Public API for location extraction.
    """
    return _location_parser.extract_locations(text)


def normalize_location_name(location: str) -> str:
    """
    BUG #14 FIX: Normalize location name to canonical form.
    
    Public API for location normalization.
    """
    return _location_parser.normalize_location(location)
