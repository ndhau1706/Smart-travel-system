"""
Text processing utilities for Vietnamese and English.
"""
import re
import unicodedata
from typing import List, Dict
from unidecode import unidecode
from config import VIETNAMESE_FOOD_SYNONYMS, CUISINE_TYPES, ATMOSPHERE_KEYWORDS


# Teencode & slang mappings
TEENCODE_MAP = {
    # Teencode
    'cx': 'cũng', 'cug': 'cũng', 'cg': 'cũng',
    'j': 'gì', 'z': 'gì', 'dzì': 'gì',
    'vs': 'với', 'v': 'với',
    'hông': 'không', 'ko': 'không', 'k': 'không', 'hok': 'không',
    'đc': 'được', 'dc': 'được',
    'nè': 'này', 'ni': 'này', 'ny': 'này',
    'r': 'rồi', 'rùi': 'rồi',
    'nek': 'này', 'nka': 'này',
    'ntn': 'như thế nào', 'sao': 'thế nào',
    'trc': 'trước', 'trog': 'trong',
    'nek': 'nhé', 'nka': 'nhé', 'nha': 'nhé',
    'ma': 'mà', 'mak': 'mà',
    'wá': 'quá', 'wa': 'quá', 'qá': 'quá',
    'oy': 'ơi', 'oii': 'ơi',
    'vl': 'vậy', 'vậy': 'vậy',
    
    # Abbreviations
    'qs': 'quán', 'q': 'quán',
    'hs': 'hải sản',
    'qa': 'quán ăn',
    're': 'rẻ', 'r.e': 'rẻ',
    
    # Slang for quality
    'xịn': 'ngon', 'xịn xò': 'ngon chất lượng', 
    'bá': 'rất', 'bá cháy': 'rất ngon',
    'xỉu': 'rất', 'xỉu up': 'rất tốt',
    'oke': 'tốt', 'ok': 'tốt', 'oce': 'tốt',
    'top': 'tốt', 'chất': 'tốt',
    'ngầu': 'đẹp', 'xịn sò': 'sang trọng',
    
    # Slang for price
    'hạt dẻ': 'rẻ', 'hạt rẻ': 'rẻ',
    'mềm': 'rẻ', 'mềm móng': 'rẻ',
    'bèo': 'rẻ', 'bèo bọt': 'rẻ',
    'vài trăm': 'rẻ', 'vài chục': 'rẻ',
    'cháy túi': 'đắt', 'chát': 'đắt',
}


def normalize_teencode(text: str) -> str:
    """
    Normalize teencode and slang to standard Vietnamese.
    
    Args:
        text: Input text with teencode/slang
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    text_lower = text.lower()
    
    # Sort by length (longer phrases first to avoid partial matches)
    sorted_terms = sorted(TEENCODE_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    
    for teencode, standard in sorted_terms:
        # Use word boundaries for single letters, exact match for longer terms
        if len(teencode) == 1:
            text_lower = re.sub(r'\b' + re.escape(teencode) + r'\b', standard, text_lower)
        else:
            text_lower = text_lower.replace(teencode, standard)
    
    return text_lower


def strip_accents(text: str) -> str:
    """
    Remove Vietnamese accents from text.
    
    Args:
        text: Input text with accents
        
    Returns:
        Text without accents
    """
    if not text:
        return ""
    
    # Normalize unicode
    normalized = unicodedata.normalize('NFD', text)
    
    # Remove combining characters
    stripped = ''.join(char for char in normalized if unicodedata.category(char) != 'Mn')
    
    return stripped


def normalize_text(text: str, remove_accents: bool = False) -> str:
    """
    Normalize text for comparison.
    
    Args:
        text: Input text
        remove_accents: Whether to remove accents
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    # Remove accents if requested
    if remove_accents:
        text = strip_accents(text)
    
    return text


def tokenize_vietnamese(text: str) -> List[str]:
    """
    Simple tokenization for Vietnamese text.
    
    Args:
        text: Input text
        
    Returns:
        List of tokens
    """
    # Remove punctuation except for dash and apostrophe
    text = re.sub(r'[^\w\s\-\']', ' ', text)
    
    # Split on whitespace
    tokens = text.split()
    
    return [token.lower() for token in tokens if token]


def expand_synonyms(text: str) -> List[str]:
    """
    Expand text with synonyms for better matching.
    
    Args:
        text: Input text
        
    Returns:
        List of text variants including synonyms
    """
    normalized = normalize_text(text)
    variants = [normalized, text.lower()]  # Keep both normalized and lowercase original
    
    # Check for food synonyms in normalized text
    for canonical, synonyms in VIETNAMESE_FOOD_SYNONYMS.items():
        canonical_lower = canonical.lower()
        if canonical_lower in normalized.lower():
            for synonym in synonyms:
                # Replace in both normalized and original
                variant1 = normalized.lower().replace(canonical_lower, synonym.lower())
                variant2 = normalized.lower().replace(canonical_lower, synonym)  # Keep synonym case
                if variant1 not in variants:
                    variants.append(variant1)
                if variant2 not in variants:
                    variants.append(variant2)
    
    return list(set(variants))  # Remove duplicates


def detect_cuisine_type(text: str) -> List[str]:
    """
    Detect cuisine types mentioned in text.
    
    Args:
        text: Input text
        
    Returns:
        List of detected cuisine types
    """
    normalized = normalize_text(text, remove_accents=True)
    detected = []
    
    for cuisine, keywords in CUISINE_TYPES.items():
        for keyword in keywords:
            keyword_normalized = normalize_text(keyword, remove_accents=True)
            if keyword_normalized in normalized:
                detected.append(cuisine)
                break
    
    return detected


def detect_atmosphere(text: str) -> List[str]:
    """
    Detect atmosphere preferences in text.
    
    Args:
        text: Input text
        
    Returns:
        List of detected atmosphere types
    """
    normalized = normalize_text(text, remove_accents=True)
    detected = []
    
    for atmosphere, keywords in ATMOSPHERE_KEYWORDS.items():
        for keyword in keywords:
            keyword_normalized = normalize_text(keyword, remove_accents=True)
            if keyword_normalized in normalized:
                detected.append(atmosphere)
                break
    
    return detected


def extract_price_range(text: str) -> Dict[str, any]:
    """
    Extract price range from text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with price information
    """
    normalized = normalize_text(text, remove_accents=True)
    
    # Extract numeric values (Vietnamese uses . for thousands, , for decimals)
    numbers = re.findall(r'\d+(?:[.,]\d+)*', text)
    
    price_info = {
        "min": None,
        "max": None,
        "level": None
    }
    
    # Check for price level keywords
    if any(kw in normalized for kw in ["re", "binh dan", "gia re", "cheap", "budget"]):
        price_info["level"] = "PRICE_LEVEL_INEXPENSIVE"
    elif any(kw in normalized for kw in ["dat", "cao cap", "expensive", "luxury", "high-end"]):
        price_info["level"] = "PRICE_LEVEL_EXPENSIVE"
    elif any(kw in normalized for kw in ["trung binh", "vua phai", "moderate"]):
        price_info["level"] = "PRICE_LEVEL_MODERATE"
    
    # Extract numeric budget
    # NEW APPROACH: Check each number individually with its context
    text_lower = text.lower()
    
    if numbers:
        for num_str in numbers:
            try:
                budget = float(num_str.replace('.', '').replace(',', '.'))
                
                # Find position of this number in text
                num_pos = text_lower.find(num_str)
                if num_pos == -1:
                    continue
                
                # Check context around this number (10 chars before and after)
                context_start = max(0, num_pos - 10)
                context_end = min(len(text_lower), num_pos + len(num_str) + 10)
                context = text_lower[context_start:context_end]
                
                # Check if THIS specific number is about distance
                is_this_distance = 'km' in context or any(kw in context for kw in [
                    'khoảng cách', 'bán kính', 'radius'
                ])
                
                # Skip if this number is clearly about distance
                if is_this_distance:
                    continue
                
                # Check if THIS specific number has price indicators
                has_price_indicator = False
                
                # Check for 'k' (not 'km') near this number
                k_match = re.search(r'\d+\s*k(?!m)', context)
                if k_match:
                    has_price_indicator = True
                
                # Check for price words
                if any(word in context for word in ['nghìn', 'nghin', 'đồng', 'dong', 'giá', 'gia']):
                    has_price_indicator = True
                
                # If has price indicator, this is money
                if has_price_indicator:
                    if 'k' in context and 'km' not in context:
                        budget *= 1000
                    price_info["max"] = budget
                    break  # Found price, stop looking
                
                # Number without indicator but large enough (likely full price)
                elif budget >= 10000:
                    price_info["max"] = budget
                    break
                    
            except:
                continue
    
    return price_info


def extract_distance(text: str) -> Dict[str, any]:
    """
    Extract distance/radius information from text.
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with distance info: {"value": float, "unit": str}
    """
    distance_info = {
        "value": None,
        "unit": None
    }
    
    text_lower = text.lower()
    
    # Check for distance keywords
    distance_keywords = ['khoảng cách', 'bán kính', 'radius', 'distance', 'within']
    has_distance_keyword = any(kw in text_lower for kw in distance_keywords)
    
    # Look for "Xkm" pattern (number directly followed by km)
    km_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*km', text_lower)
    if km_pattern:
        try:
            value = float(km_pattern.group(1).replace(',', '.'))
            distance_info["value"] = value
            distance_info["unit"] = "km"
            return distance_info
        except:
            pass
    
    # If no "Xkm" pattern but has distance keywords, try to find nearby number
    if not has_distance_keyword:
        return distance_info
    
    # Find all numbers with their positions
    number_matches = list(re.finditer(r'\d+(?:[.,]\d+)?', text))
    if not number_matches:
        return distance_info
    
    # Find position of distance keywords
    keyword_positions = []
    for kw in distance_keywords:
        pos = text_lower.find(kw)
        if pos != -1:
            keyword_positions.append(pos)
    
    if not keyword_positions:
        return distance_info
    
    # Find number closest to a distance keyword
    min_keyword_pos = min(keyword_positions)
    closest_match = None
    min_distance = float('inf')
    
    for match in number_matches:
        dist = abs(match.start() - min_keyword_pos)
        if dist < min_distance:
            min_distance = dist
            closest_match = match
    
    if closest_match:
        try:
            value = float(closest_match.group().replace(',', '.'))
            distance_info["value"] = value
            distance_info["unit"] = "km"
        except:
            pass
    
    return distance_info


def extract_location(text: str) -> List[str]:
    """
    Extract location mentions from text.
    
    Args:
        text: Input text
        
    Returns:
        List of detected locations
    """
    # Common HCMC districts and areas
    locations = []
    
    district_pattern = r'(?:quan|quận|district)\s*(\d+)'
    matches = re.findall(district_pattern, text.lower())
    if matches:
        locations.extend([f"Quận {m}" for m in matches])
    
    # Common area names
    areas = [
        "bến thành", "bến nghé", "phú nhuận", "tân bình", "bình thạnh",
        "gò vấp", "thủ đức", "bình tân", "tân phú", "quận 1", "quận 2",
        "quận 3", "quận 4", "quận 5", "quận 6", "quận 7", "quận 8",
        "quận 9", "quận 10", "quận 11", "quận 12", "thảo điền",
        "nguyễn huệ", "đồng khởi", "lê lợi", "pasteur"
    ]
    
    normalized = normalize_text(text, remove_accents=True)
    for area in areas:
        area_norm = normalize_text(area, remove_accents=True)
        if area_norm in normalized:
            locations.append(area)
    
    return locations
