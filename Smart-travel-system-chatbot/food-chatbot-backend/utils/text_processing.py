"""
Text processing utilities for Vietnamese and English.
"""
import re
import unicodedata
from typing import List, Dict, Optional
from unidecode import unidecode
from config import VIETNAMESE_FOOD_SYNONYMS, CUISINE_TYPES, ATMOSPHERE_KEYWORDS


# Teencode & slang mappings
TEENCODE_MAP = {
    # Teencode - FIXED: More comprehensive mapping
    'cx': 'cũng', 'cug': 'cũng', 'cg': 'cũng',
    'j': 'gì', 'z': 'vậy', 'dzì': 'gì', 'zị': 'gì', 'zai': 'vãi',
    'vs': 'với', 'v': 'với',
    'hông': 'không', 'ko': 'không', 'k': 'không', 'hok': 'không',
    'đc': 'được', 'dc': 'được', 'đk': 'được',
    'nè': 'này', 'ni': 'này', 'ny': 'này',
    'r': 'rồi', 'rùi': 'rồi',
    'nek': 'này', 'nka': 'này',
    'ntn': 'như thế nào', 'sao': 'thế nào',
    'trc': 'trước', 'trog': 'trong',
    'nek': 'nhé', 'nka': 'nhé', 'nha': 'nhé',
    'ma': 'mà', 'mak': 'mà',
    'wá': 'quá', 'wa': 'quá', 'qá': 'quá',
    'oy': 'ơi', 'oii': 'ơi',
    'vl': 'vậy', 'tr': 'trời', 'iu': 'yêu', 'mún': 'muốn', 'mn': 'mọi người',
    
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
    'sinh viên': 'rẻ', 'giá sinh viên': 'rẻ',
    'tiết kiệm': 'rẻ', 'phải chăng': 'rẻ',
    'sang trọng': 'đắt', 'cao cấp': 'đắt',
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
    
    # Use unidecode for proper Vietnamese accent removal (đ → d)
    return unidecode(text)


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
    
    # First, normalize teencode/slang
    text = normalize_teencode(text)
    
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


def expand_synonyms(text: str, query_context: str = None) -> List[str]:
    """
    BUG #13 FIX: Expand text with CONTEXT-AWARE synonyms.
    Limits expansion to prevent noise and respects cuisine context.
    
    Args:
        text: Input text
        query_context: Full query for context-aware filtering
        
    Returns:
        List of text variants including synonyms (limited to 10)
    """
    # BUG #13 FIX: Use new synonym filter
    from utils.synonym_filter import synonym_filter
    
    normalized = normalize_text(text)
    
    # Context-aware expansion (max 10 variants)
    variants = synonym_filter.expand_with_context(
        normalized,
        query_context=query_context or text,
        max_variants=10  # BUG #13 FIX: Limit variants to 10 (was unlimited)
    )
    
    # Add original text if not included
    if text.lower() not in [v.lower() for v in variants]:
        variants.insert(0, text.lower())
    
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


def parse_price_to_int(price_value: any) -> Optional[int]:
    """
    BUG #9 FIX: Parse price value to integer, handling string formats.
    
    Converts various price formats to integer:
    - "50k" → 50000
    - "2 triệu" → 2000000  
    - "100,000" → 100000
    - 50000.0 → 50000
    - "rẻ" → None (not numeric)
    
    Args:
        price_value: Price value in various formats (str, int, float)
        
    Returns:
        Integer price in VND, or None if cannot parse
    """
    if price_value is None:
        return None
    
    # Already numeric - just convert to int
    if isinstance(price_value, (int, float)):
        try:
            return int(price_value)
        except (ValueError, OverflowError):
            return None
    
    # String format - need to parse
    if isinstance(price_value, str):
        price_str = price_value.strip().lower()
        
        # Remove common separators EXCEPT decimal point (need for "1.5 triệu")
        price_str = price_str.replace(',', '')
        
        try:
            # Check for 'k' suffix (thousands)
            if 'k' in price_str and 'km' not in price_str:
                num_str = price_str.replace('k', '').replace('.', '').strip()
                return int(float(num_str) * 1000)
            
            # BUG #9 FIX: Check for 'tỷ' / 'ty' / 'billion' (billions) - HIGHEST PRIORITY
            if any(word in price_str for word in ['tỷ', 'ty', 'billion', 'bil']):
                import re
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 1_000_000_000)
            
            # Check for 'trăm triệu' (hundred millions) - BEFORE 'triệu'
            # Use regex to ensure exact phrase match, not substring
            import re
            if re.search(r'trăm\s+triệu|tram\s+trieu', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 100_000_000)
            
            # Check for 'chục triệu' (tens of millions) - BEFORE 'triệu'
            if re.search(r'chục\s+triệu|chuc\s+trieu', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 10_000_000)
            
            # Check for 'triệu' / 'million' (millions)
            # BUG FIX: Must use word boundary for 'tr' to avoid matching 'trăm'
            if 'triệu' in price_str or 'million' in price_str or re.search(r'\btr\b', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 1_000_000)
            
            # Check for 'trăm ngàn' / 'trăm nghìn' (hundred thousands) - BEFORE 'nghìn'
            if re.search(r'trăm\s+(ngàn|nghìn)|tram\s+(ngan|nghin)', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 100_000)
            
            # Check for 'chục ngàn' / 'chục nghìn' (tens of thousands) - BEFORE 'nghìn'
            if re.search(r'chục\s+(ngàn|nghìn)|chuc\s+(ngan|nghin)', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 10_000)
            
            # Check for 'nghìn' / 'ngàn' (thousands)
            if any(word in price_str for word in ['nghìn', 'nghin', 'ngàn', 'ngan']):
                import re
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 1000)
            
            # Check for 'trăm' / 'tram' (hundreds) - STANDALONE ONLY (not part of compound)
            # Must NOT match "trăm triệu" or "trăm nghìn" (those are handled above)
            import re
            # Negative lookahead: trăm NOT followed by triệu/nghìn/ngàn
            if re.search(r'trăm(?!\s*(triệu|nghìn|ngàn|ngan|nghin))', price_str) or \
               re.search(r'tram(?!\s*(trieu|nghin|ngan))', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 100)
            
            # Check for 'chục' / 'chuc' (tens) - STANDALONE ONLY (not part of compound)
            # Must NOT match "chục triệu" or "chục nghìn" (those are handled above)
            if re.search(r'chục(?!\s*(triệu|nghìn|ngàn|ngan|nghin))', price_str) or \
               re.search(r'chuc(?!\s*(trieu|nghin|ngan))', price_str):
                match = re.search(r'([\d.]+)', price_str)
                if match:
                    num = float(match.group(1))
                    return int(num * 10)
            
            # Plain number - remove dots now (Vietnamese thousand separator)
            price_str = price_str.replace('.', '')
            return int(float(price_str))
            
        except (ValueError, AttributeError):
            return None
    
    # Unknown type
    return None


def extract_price_range(text: str) -> Dict[str, any]:
    """
    Extract price range from text.
    
    BUG #9 FIX: Always returns INTEGER prices, never strings.
    This prevents lexicographic comparison bugs where "200k" < "50k".
    
    Args:
        text: Input text
        
    Returns:
        Dictionary with price information:
        - "min": Optional[int] - minimum price in VND
        - "max": Optional[int] - maximum price in VND  
        - "level": Optional[str] - price level category
    """
    # DON'T normalize teencode yet - it ruins patterns like "3 cây k" → "3 cây không"
    # Only normalize for keyword matching
    normalized = normalize_text(text, remove_accents=True)
    
    # Extract numeric values (Vietnamese uses . for thousands, , for decimals)
    numbers = re.findall(r'\d+(?:[.,]\d+)*', text)
    
    price_info = {
        "min": None,
        "max": None,
        "level": None
    }
    
    # Check for price level keywords (normalized text has accents removed)
    # Note: teencode normalization in normalize_text() converts things, so check carefully
    if any(kw in normalized for kw in ["re", "binh dan", "gia re", "cheap", "budget", "sinh vien", "tiet kiem", "mem", "beo", "phai chang", "ngan"]):
        price_info["level"] = "PRICE_LEVEL_INEXPENSIVE"
    elif any(kw in normalized for kw in ["dat", "cao cap", "expensive", "luxury", "high-end", "dat cung", "khong quan trong gia"]):
        price_info["level"] = "PRICE_LEVEL_EXPENSIVE"
    elif any(kw in normalized for kw in ["trung binh", "vua phai", "moderate", "hop ly"]):
        price_info["level"] = "PRICE_LEVEL_MODERATE"
    
    # Extract numeric budget
    # NEW APPROACH: Check each number individually with its context
    text_lower = text.lower()  # Use ORIGINAL text to preserve "cây k" patterns
    
    # BUG #9 FIX: Check for RANGE pattern first: "từ X đến Y", "X-Y", "X đến Y"
    # Updated to capture COMPOUND units like "trăm nghìn", "chục triệu"
    # Capture up to 3 words after number for compound units
    range_patterns = [
        r'từ\s+([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*?)\s+đến\s+([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*)',
        r'([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*?)\s*-\s*([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*)',
        r'([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*?)\s+đến\s+([\d.,]+)\s*([a-záàảãạăắằẳẵặâấầẩẫậéèẻẽẹêếềểễệíìỉĩịóòỏõọôốồổỗộơớờởỡợúùủũụưứừửữựýỳỷỹỵ\s]*)',
    ]
    
    for pattern in range_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                # BUG #9 FIX: Use parse_price_to_int() for consistent parsing
                min_num_str = match.group(1).replace('.', '').replace(',', '.')
                min_unit = match.group(2).strip() if len(match.groups()) >= 2 else ''
                max_num_str = match.group(3).replace('.', '').replace(',', '.')
                max_unit = match.group(4).strip() if len(match.groups()) >= 4 else ''
                
                # Construct price strings for parsing
                min_price_str = f"{min_num_str} {min_unit}".strip()
                max_price_str = f"{max_num_str} {max_unit}".strip()
                
                # Parse using helper function for consistency
                min_val = parse_price_to_int(min_price_str)
                max_val = parse_price_to_int(max_price_str)
                
                # Only set if both parsed successfully
                if min_val is not None and max_val is not None:
                    price_info["min"] = min_val
                    price_info["max"] = max_val
                    return price_info
            except:
                pass  # Continue to single price extraction
    
    # Check for "vài chục ngàn" BEFORE number extraction (no specific number)
    if 'vài chục' in text_lower and 'ngàn' in text_lower:
        price_info["max"] = int(50000)  # BUG #9 FIX: Ensure integer
        return price_info
    
    if numbers:
        for num_str in numbers:
            try:
                # Find position of this number in text
                num_pos = text_lower.find(num_str)
                if num_pos == -1:
                    continue
                
                # Check context around this number (10 chars before and after)
                context_start = max(0, num_pos - 10)
                context_end = min(len(text_lower), num_pos + len(num_str) + 10)
                context = text_lower[context_start:context_end]
                
                # ========== BUG 11 FIX: COMPREHENSIVE NUMBER FILTERING ==========
                
                # FILTER 1: Skip PHONE NUMBERS (10+ digits)
                if len(num_str.replace('.', '').replace(',', '')) >= 10:
                    continue  # Phone number, skip!
                
                # FILTER 2: Skip RATING numbers (x.x format with "rating" or "sao")
                # "rating 4.5", "4.5 sao", "đánh giá 4.5"
                # Check BEFORE converting to avoid "4.5" → "45" issue
                if '.' in num_str or ',' in num_str:
                    # Parse as original decimal to check if small (rating-like)
                    original_value = float(num_str.replace(',', '.'))
                    
                    # Check if it's a rating (small decimal number <= 5.0)
                    if original_value <= 5.0:
                        wide_context_start = max(0, num_pos - 15)
                        wide_context_end = min(len(text_lower), num_pos + len(num_str) + 15)
                        wide_context = text_lower[wide_context_start:wide_context_end]
                        
                        rating_keywords = ['rating', 'sao', 'star', 'đánh giá', 'review', 'đánh']
                        if any(kw in wide_context for kw in rating_keywords):
                            continue  # It's a rating, skip!
                
                # NOW convert budget (after rating filter)
                budget = float(num_str.replace('.', '').replace(',', '.'))
                
                # BUG #22 FIX: Track if we've already applied a multiplier from "cây ngàn/đồng"
                # to prevent double multiplication
                already_multiplied_by_cay = False
                
                # FILTER 3: Skip SIZE/MEASUREMENT numbers
                # "size 9", "9 inch", "12 inch pizza"
                # Use NARROW context to avoid false positives
                narrow_context_start = max(0, num_pos - 8)
                narrow_context_end = min(len(text_lower), num_pos + len(num_str) + 8)
                narrow_context = text_lower[narrow_context_start:narrow_context_end]
                
                # Check if THIS specific number is directly attached to measurement unit
                measurement_patterns = [
                    r'\b' + re.escape(num_str) + r'\s*(?:inch|cm|người|person)',
                    r'size\s+' + re.escape(num_str),
                ]
                
                is_measurement = any(re.search(pattern, narrow_context) for pattern in measurement_patterns)
                if is_measurement:
                    continue  # It's a size/measurement, skip!
                
                # FILTER 4: Skip DISTRICT numbers (but only if not price context)
                # "Quận 7", "District 9"
                district_pattern = r'(?:quận|district|q\.?)\s*' + re.escape(num_str)
                if re.search(district_pattern, text_lower):
                    # Only skip if there's NO price indicator nearby
                    has_price_nearby = any(kw in wide_context for kw in ['giá', 'k', 'đồng', 'nghìn', 'budget'])
                    if not has_price_nearby:
                        continue  # It's a district, skip!
                
                # ========== ORIGINAL LOGIC (DISTANCE FILTERING) ==========
                
                # 1. Check for STRONG distance context (overrides everything)
                strong_distance_context = re.search(
                    r'(trong|trong vòng|khoảng|bán kính|gần nhất|max|cách|cách đây)\s+' + re.escape(num_str),
                    text_lower
                )
                if strong_distance_context:
                    continue  # Skip this number - it's distance!
                
                # 2. Check for explicit km/m unit
                if 'km' in context or re.search(r'\d+\s*m(?:\s|$)', context):
                    continue  # It's distance
                
                # 3. Check for distance keywords near this number
                has_distance_keyword = any(kw in context for kw in [
                    'khoảng cách', 'bán kính', 'radius', 'distance'
                ])
                if has_distance_keyword:
                    continue  # It's distance
                
                # 4. IMPROVED: Special handling for "cây" ambiguity with better context analysis
                # "cây k" in PRICE context = price
                # "cây" with DISTANCE keyword = distance (even with 'k'!)
                if 'cây' in context or 'cay' in context:  # Handle typos like "câyk"
                    # Check wider context for strong distance signals
                    wide_context_start = max(0, num_pos - 30)
                    wide_context_end = min(len(text_lower), num_pos + len(num_str) + 20)
                    wide_context = text_lower[wide_context_start:wide_context_end]
                    
                    # PRIORITY 1: Strong distance keywords (BEFORE the number)
                    # "trong 10 cây", "bán kính 5 cây", "gần 3 cây", "xa 15 cây"
                    strong_distance_before = any(
                        re.search(rf'\b{kw}\s+\d+\s*cây', wide_context)
                        for kw in ['trong', 'bán kính', 'gần', 'max', 'khoảng cách', 'cách', 'cách đây', 'trong vòng', 'xa']
                    )
                    
                    if strong_distance_before:
                        continue  # Distance wins!
                    
                    # PRIORITY 2: Distance context words near this specific "cây"
                    # Look for distance words within 15 chars before
                    context_before_cay = text_lower[max(0, num_pos - 15):num_pos + len(num_str)]
                    has_distance_nearby = any(kw in context_before_cay for kw in [
                        'trong', 'bán kính', 'gần', 'cách', 'xa', 'khoảng cách'
                    ])
                    
                    if has_distance_nearby:
                        continue  # Distance context wins!
                    
                    # PRIORITY 3: Check if this is FIRST or SECOND occurrence of "cây"
                    # "Buffet 50 cây gần 5 cây" → First "50 cây" = price, second "5 cây" = distance
                    all_cay_positions = [m.start() for m in re.finditer(r'\d+\s*cây', text_lower)]
                    if len(all_cay_positions) >= 2:
                        current_cay_pos = num_pos
                        # Find which occurrence this is
                        occurrence_index = sum(1 for pos in all_cay_positions if pos <= current_cay_pos)
                        
                        # Check if later occurrence has distance context
                        for idx, pos in enumerate(all_cay_positions, 1):
                            if idx > occurrence_index:
                                context_around_later = text_lower[max(0, pos - 15):min(len(text_lower), pos + 20)]
                                if any(kw in context_around_later for kw in ['gần', 'cách', 'trong', 'xa']):
                                    # Current "cây" is likely price, later one is distance
                                    # Continue to check if current has price indicators
                                    break
                    
                    # PRIORITY 4: CASE "X cây giá rẻ" - "cây" alone WITHOUT 'k' and WITH 'giá' keyword
                    # This means "cây" is distance, "giá rẻ" is separate price info
                    has_price_keyword_after = any(re.search(rf'\d+\s*cây\s+[^\d]*{kw}', wide_context) 
                                                   for kw in ['giá', 'budget', 'chi phí'])
                    has_cay_alone = 'cây' in wide_context and not re.search(r'cây\s*k\b', wide_context)
                    
                    if has_cay_alone and has_price_keyword_after:
                        # "5 cây giá rẻ" → skip "5" (it's distance), process "giá rẻ" separately
                        continue  # Skip this number
                    
                    # PRIORITY 5: Check for price context words
                    # "dưới 10 cây", "tầm 20 cây", "giá 15 cây", "chỉ 20 cây"
                    price_context_before = any(kw in context_before_cay for kw in [
                        'dưới', 'trên', 'tầm', 'giá', 'budget', 'chi phí', 'khoảng', 'chỉ', 'không quá'
                    ])
                    
                    # If has price context and NO distance context, it's likely price
                    # But continue to check for explicit price indicators below
                    # Don't skip yet - let price indicator check handle it
                
                # Check if THIS specific number has price indicators
                has_price_indicator = False
                
                # Check for 'k' (not 'km') near this number
                k_match = re.search(r'\d+\s*k(?!m)', context)
                if k_match:
                    has_price_indicator = True
                
                # Check for 'cây' as price slang (check wider context)
                # "5 cây k" = 5000đ, "3 cây km" = 3000đ (slang!), "10 cây đồng" = 10000đ
                # Check in wider context (30 chars)
                wide_context_start = max(0, num_pos - 15)
                wide_context_end = min(len(text_lower), num_pos + len(num_str) + 20)
                wide_context = text_lower[wide_context_start:wide_context_end]
                
                # IMPROVED: Match "cây k/km/đồng/nghìn/ngàn" with typo handling
                # Handle: "câyk" (typo no space), "cây ki lô" (variant), "cay k" (missing accent)
                # FIX BUG #22: Add support for "cây ngàn" and "cây đồng" (Vietnamese slang for price)
                # "50 cây ngàn" = 50,000 VNĐ, "100 cây đồng" = 100,000 VNĐ
                cay_price_pattern = re.search(
                    r'\d+\s*c[aâ]y\s*(?:k[im]?\s*l[oô]|k[m]?\b|\bđồng\b|\bnghìn\b|\bngàn\b)',
                    wide_context
                )
                
                # Also check for typo: "100câyk" (no space between digits and cây)
                cay_typo_pattern = re.search(r'\d+c[aâ]yk', wide_context)
                
                # NEW: Check if distance context appears AFTER the "cây k" pattern
                # "Quán 15 cây k từ đây" → distance ("từ đây" after = distance wins!)
                if cay_price_pattern or cay_typo_pattern:
                    # Check context AFTER the pattern
                    context_after = text_lower[num_pos:min(len(text_lower), num_pos + 50)]
                    has_distance_after_cay_k = any(kw in context_after for kw in [
                        'từ đây', 'đến', 'về', 'gần', 'xa', 'cách'
                    ])
                    
                    # If distance context AFTER "cây k", it's distance, not price!
                    if has_distance_after_cay_k:
                        continue  # Skip this number - it's distance!
                    
                    has_price_indicator = True
                    # 'cây' in price context means thousands
                    # BUG #22 FIX: Track that we already applied multiplier for "cây ngàn/đồng"
                    # to prevent double multiplication later
                    already_multiplied_by_cay = True
                    budget *= 1000
                
                # Check for "giá X cây" or "X cây" without distance context
                # But NOT if followed by distance context words
                elif 'cây' in context and ('giá' in context or 'tầm' in context or 'dưới' in context or 'chỉ' in context):
                    # Check it's not "cây số" (distance) or "cây km"
                    if 'cây số' not in context and 'cây km' not in context:
                        # Additional check: no distance words AFTER this number
                        context_after = text_lower[num_pos:min(len(text_lower), num_pos + 40)]
                        has_distance_after = any(kw in context_after for kw in [
                            'gần', 'cách', 'trong', 'xa', 'bán kính'
                        ])
                        
                        if not has_distance_after:
                            has_price_indicator = True
                            budget *= 1000
                
                # Check for price words and apply multipliers
                # BUG #9 FIX: Add all Vietnamese currency units with priority order
                if 'tỷ' in context or 'ty' in context or 'billion' in context:
                    has_price_indicator = True
                    budget *= 1_000_000_000  # Billions
                elif 'trăm triệu' in context or 'tram trieu' in context:
                    has_price_indicator = True
                    budget *= 100_000_000  # Hundred millions
                elif 'chục triệu' in context or 'chuc trieu' in context:
                    has_price_indicator = True
                    budget *= 10_000_000  # Tens of millions
                elif 'triệu' in context or 'trieu' in context:
                    has_price_indicator = True
                    budget *= 1_000_000  # Millions
                elif 'trăm nghìn' in context or 'tram nghin' in context or 'trăm ngàn' in context or 'tram ngan' in context:
                    has_price_indicator = True
                    budget *= 100_000  # Hundred thousands
                elif 'chục nghìn' in context or 'chuc nghin' in context or 'chục ngàn' in context or 'chuc ngan' in context:
                    has_price_indicator = True
                    budget *= 10_000  # Tens of thousands
                elif 'nghìn' in context or 'nghin' in context or 'ngàn' in context or 'ngan' in context:
                    # BUG #22 FIX: Skip if already multiplied by "cây ngàn/đồng"
                    # "50 cây ngàn" should be 50k, NOT 50k * 1000 = 50M
                    if not already_multiplied_by_cay:
                        has_price_indicator = True
                        budget *= 1000  # Thousands
                elif re.search(r'trăm(?!\s*(triệu|nghìn|ngàn))', context) or re.search(r'tram(?!\s*(trieu|nghin|ngan))', context):
                    # Standalone 'trăm' (not part of compound)
                    has_price_indicator = True
                    budget *= 100  # Hundreds
                elif re.search(r'chục(?!\s*(triệu|nghìn|ngàn))', context) or re.search(r'chuc(?!\s*(trieu|nghin|ngan))', context):
                    # Standalone 'chục' (not part of compound)
                    has_price_indicator = True
                    budget *= 10  # Tens
                elif any(word in context for word in ['đồng', 'dong', 'giá', 'gia']):
                    has_price_indicator = True
                
                # Check for "vài chục" pattern with "ngàn"
                if ('vài chục' in text_lower and 'ngàn' in text_lower) or 'vài ba chục' in text_lower:
                    price_info["max"] = 50000
                    return price_info
                
                # BUG 11 FIX: PRIORITIZE explicit price markers
                # If has price indicator, this is DEFINITELY money
                if has_price_indicator:
                    if 'k' in context and 'km' not in context and 'cây k' not in context:
                        budget *= 1000
                    
                    # BUG #2 FIX: Add upper bound check to prevent integer overflow
                    # BUG #9 FIX: Increased limit to support 'tỷ' (billions)
                    # Maximum reasonable budget: 10 billion VND (for luxury properties, etc.)
                    MAX_REASONABLE_PRICE = 10_000_000_000
                    
                    if budget > MAX_REASONABLE_PRICE:
                        # Log warning for debugging
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.warning(f"⚠️ Price overflow detected: {budget:,.0f}đ. Capping at {MAX_REASONABLE_PRICE:,.0f}đ")
                        budget = MAX_REASONABLE_PRICE
                    
                    # Also check for negative values (shouldn't happen, but defensive)
                    if budget < 0:
                        budget = 0
                    
                    # BUG #9 FIX: Ensure integer type
                    price_info["max"] = int(budget)
                    return price_info  # IMMEDIATELY return - highest priority!
                
                # Number without indicator but large enough (likely full price)
                # Store as candidate but keep looking for better match
                elif budget >= 10000:
                    # BUG #2 FIX: Apply same bounds check here
                    MAX_REASONABLE_PRICE = 10_000_000_000
                    
                    if budget > MAX_REASONABLE_PRICE:
                        budget = MAX_REASONABLE_PRICE
                    
                    if not price_info["max"]:  # Only set if we haven't found better
                        price_info["max"] = int(budget)  # BUG #9 FIX: Ensure integer
                    # Don't break - continue looking for explicit markers
                    
            except:
                continue
    
    # Check verbal price patterns that don't have numbers
    # "vài ba cây" = ~3000đ (3 nghìn)
    if ('vài ba cây' in text_lower or 'vài cây' in text_lower) and 'giá' in text_lower:
        price_info["max"] = int(3000)  # BUG #9 FIX: Ensure integer
        return price_info
    
    # FALLBACK: If we have price level but no explicit max_budget, set default
    # "giá rẻ" without number → assume reasonable default
    if price_info["level"] and not price_info["max"]:
        if price_info["level"] == "PRICE_LEVEL_INEXPENSIVE":
            price_info["max"] = int(150000)  # BUG #9 FIX: Cheap default
        elif price_info["level"] == "PRICE_LEVEL_MODERATE":
            price_info["max"] = int(300000)  # BUG #9 FIX: Moderate default
        # Don't set default for EXPENSIVE - leave it open
    
    # BUG #2 FIX: Final safety check - ensure no price exceeds maximum
    if price_info["max"] is not None:
        MAX_REASONABLE_PRICE = 100_000_000
        if price_info["max"] > MAX_REASONABLE_PRICE:
            price_info["max"] = MAX_REASONABLE_PRICE
        
        # Also check minimum (defensive)
        if price_info["max"] < 0:
            price_info["max"] = None  # Invalid, reset
    
    # BUG #9 FIX: Type safety - ensure prices are ALWAYS integers, never strings
    # This prevents lexicographic comparison bugs: "200k" < "50k" (True, WRONG!)
    # vs 200000 < 50000 (False, CORRECT!)
    if price_info["min"] is not None:
        price_info["min"] = int(price_info["min"])
    
    if price_info["max"] is not None:
        price_info["max"] = int(price_info["max"])
    
    return price_info


def extract_distance(text: str) -> Dict[str, any]:
    """
    Extract distance/radius information from text.
    
    IMPROVED: Context-aware disambiguation for 'cây' (km) vs 'cây k' (1000đ)
    
    Priority:
    1. Explicit 'km' unit
    2. Distance keywords (bán kính, trong, gần) + number
    3. 'cây' in distance context (NOT followed by 'k/đồng/nghìn')
    4. Proximity keywords (gần nhất, max, trong) override 'k' suffix
    
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
    
    # Check for distance keywords (high priority)
    distance_keywords = ['khoảng cách', 'bán kính', 'radius', 'distance', 'within']
    has_distance_keyword = any(kw in text_lower for kw in distance_keywords)
    
    # Check for proximity keywords (medium priority)
    proximity_keywords = ['gần', 'gần đây', 'gần nhất', 'trong', 'trong vòng', 'max', 'khoảng', 'cách', 'cách đây']
    has_proximity_keyword = any(kw in text_lower for kw in proximity_keywords)
    
    # PRIORITY 1: Look for "Xkm" pattern (number directly followed by km) - HIGHEST PRIORITY
    km_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*km', text_lower)
    if km_pattern:
        try:
            value = float(km_pattern.group(1).replace(',', '.'))
            distance_info["value"] = value
            distance_info["unit"] = "km"
            return distance_info
        except:
            pass
    
    # PRIORITY 2: "trong/bán kính/gần/cách đây + X cây" patterns (WITH context)
    # These distance keywords OVERRIDE the 'k' suffix!
    # Example: "bán kính 10 cây k" → 10km (distance keyword wins)
    # Example: "cách đây 5 cây k" → 5km (k = không, not price)
    # Example: "trong 3 cây" → 3km (distance context)
    strong_distance_pattern = re.search(
        r'(trong|trong vòng|khoảng|bán kính|gần|gần nhất|max|cách|cách đây)\s+(\d+(?:[.,]\d+)?)\s*cây',
        text_lower
    )
    if strong_distance_pattern:
        try:
            value = float(strong_distance_pattern.group(2).replace(',', '.'))
            distance_info["value"] = value
            distance_info["unit"] = "km"
            return distance_info  # Strong match - return immediately
        except:
            pass
    
    # IMPROVED: PRIORITY 2.5: "X cây k" / "X cây km" disambiguation with better context analysis
    # "3 cây k từ đây" → 3km (has "từ đây" context AFTER)
    # "Tìm trong 5 cây k" → 5km (has "tìm", "trong" context BEFORE)
    # "Buffet dưới 2 cây k" → 2000đ (NO distance context → price!)
    # "100câyk" → 100km if has distance context, else 100k price (typo)
    # "10 cây ki lô" → 10km (variant spelling)
    
    # Enhanced pattern to catch typos and variants
    cay_k_match = re.search(
        r'(\d+(?:[.,]\d+)?)\s*c[aâ]y\s*(?:k[im]?\s*l[oô]|k(?:m)?\b)',
        text_lower
    )
    
    # Also check for typo: "100câyk" (no space)
    if not cay_k_match:
        cay_k_match = re.search(r'(\d+)c[aâ]yk', text_lower)
    
    if cay_k_match:
        # Check context before AND after "cây k"
        start_pos = max(0, cay_k_match.start() - 35)
        end_pos = min(len(text_lower), cay_k_match.end() + 25)
        context_before = text_lower[start_pos:cay_k_match.start()]
        context_after = text_lower[cay_k_match.end():end_pos]
        
        # IMPROVED: More comprehensive distance context words
        distance_context_words = [
            'trong', 'gần', 'khoảng', 'bán kính', 'radius', 'max', 'cách', 'cách đây',
            'từ đây', 'tìm', 'đến', 'về', 'xa', 'trong vòng', 'khoảng cách',
            'tìm quán', 'có quán', 'quán nào'
        ]
        
        # Check BOTH before and after, with priority to BEFORE
        has_distance_before = any(word in context_before for word in distance_context_words)
        has_distance_after = any(word in context_after for word in distance_context_words)
        
        # NEW: Check for price context words that override distance
        # NOTE: 'buffet' và 'món' là food context, KHÔNG phải price context!
        price_context_words = ['giá', 'budget', 'chi phí', 'dưới', 'trên', 'tầm']
        has_price_before = any(word in context_before for word in price_context_words)
        
        # Decision logic:
        # 1. Distance BEFORE context = definitely distance
        # 2. Distance AFTER context (like "từ đây") = distance
        # 3. Price BEFORE context + NO distance context = definitely price
        # 4. Ambiguous = default to price
        
        is_distance = False
        if has_distance_before or has_distance_after:
            is_distance = True  # Distance context (before OR after)
        elif has_price_before:
            is_distance = False  # Explicit price context
        # else: ambiguous, default to price
        
        if is_distance:
            try:
                value = float(cay_k_match.group(1).replace(',', '.'))
                distance_info["value"] = value
                distance_info["unit"] = "km"
                return distance_info
            except:
                pass
        # else: No clear distance context → "cây k" = price (2 cây k = 2000đ)
    
    # PRIORITY 3: "X cây" without price indicators (ambiguous case)
    # Only match if NOT followed by price markers: 'k', 'đồng', 'nghìn', 'ngàn'
    cay_distance_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*cây(?!\s*(?:k\b|đồng|nghìn|ngàn))', text_lower)
    if cay_distance_pattern:
        # Additional context check
        num_pos = cay_distance_pattern.start()
        context_start = max(0, num_pos - 20)
        context_end = min(len(text_lower), num_pos + 30)
        context = text_lower[context_start:context_end]
        
        # Check for distance context signals
        has_distance_context = any(word in context for word in [
            'trong', 'gần', 'khoảng cách', 'bán kính', 'radius', 'max', 'cách', 'cách đây', 'xa'
        ])
        
        # Check for IMMEDIATE price context (within "X cây" phrase)
        # "5 cây k" → immediate price context
        # "5 cây giá rẻ" → "giá" is SEPARATE, not immediate
        immediate_price_context = any(word in context[:15] for word in [
            'đồng', 'nghìn', 'ngàn'
        ])
        
        # If has distance context and NO immediate price context, it's distance
        if has_distance_context and not immediate_price_context:
            try:
                value = float(cay_distance_pattern.group(1).replace(',', '.'))
                distance_info["value"] = value
                distance_info["unit"] = "km"
                return distance_info
            except:
                pass
        
        # SPECIAL CASE: "X cây giá Y" - "cây" is distance, "giá" is price
        # Pattern: number + cây + space/words + giá
        # "5 cây giá rẻ" → "5 cây" is distance
        separate_price_pattern = re.search(r'\d+\s*cây\s+[^\d]*giá', text_lower)
        if separate_price_pattern and not immediate_price_context:
            try:
                value = float(cay_distance_pattern.group(1).replace(',', '.'))
                distance_info["value"] = value
                distance_info["unit"] = "km"
                return distance_info
            except:
                pass
        
        # Even without explicit context, if has proximity keyword, assume distance
        elif has_proximity_keyword and not immediate_price_context:
            try:
                value = float(cay_distance_pattern.group(1).replace(',', '.'))
                distance_info["value"] = value
                distance_info["unit"] = "km"
                return distance_info
            except:
                pass
    
    # Look for "cây số" pattern explicitly
    cay_so_pattern = re.search(r'(\d+(?:[.,]\d+)?)\s*cây\s*số', text_lower)
    if cay_so_pattern:
        try:
            value = float(cay_so_pattern.group(1).replace(',', '.'))
            distance_info["value"] = value
            distance_info["unit"] = "km"
            return distance_info
        except:
            pass
    
    # Look for "Xm" pattern (meters) - including "trong 500m"
    m_pattern = re.search(r'(\d+)\s*m(?:\s|$|[^a-zà-ỹ])', text_lower)
    if m_pattern:
        try:
            value = float(m_pattern.group(1))
            distance_info["value"] = value / 1000  # Convert to km
            distance_info["unit"] = "km"
            return distance_info
        except:
            pass
    
    # Check for verbal distance expressions
    if 'đi bộ' in text_lower or 'walking' in text_lower:
        distance_info["value"] = 1.0
        distance_info["unit"] = "km"
        return distance_info
    
    # "xe máy 10 phút" ~ 3km
    motorbike_pattern = re.search(r'xe\s*máy\s*(\d+)\s*phút', text_lower)
    if motorbike_pattern:
        try:
            minutes = int(motorbike_pattern.group(1))
            distance_info["value"] = minutes * 0.3  # 0.3km per minute
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
    BUG #14 FIX: Extract location mentions from text with context awareness.
    
    Fixes 10 scenarios:
    1. Ambiguous District: "Quận 10 11" (address)
    2. Street Name: "Đường Quận 1"
    3. Restaurant Name: "Phở Quận 7"
    4. Multiple Locations: "Quận 1 hoặc Quận 3"
    5. Nested Location: "Gần Bến Thành, Quận 1"
    6. Abbreviation: "Q1" → "Quận 1"
    7. Old Name: "Sài Gòn" → "TP.HCM"
    8. English Mix: "District 1"
    9. Typo: "Quậnn 1" (fuzzy matching)
    10. Landmark: "Gần Landmark 81" → "Quận Bình Thạnh"
    
    Args:
        text: Input text
        
    Returns:
        List of detected locations (normalized)
    """
    # BUG #14 FIX: Use advanced location parser
    from utils.location_parser import extract_locations_advanced
    return extract_locations_advanced(text)
