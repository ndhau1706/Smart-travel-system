"""
Advanced input processing and normalization.
Handles: spell-checking, code-switching, expanded slang, typo correction.
"""
import re
from typing import Dict, Tuple, List
from unidecode import unidecode
import unicodedata


# EXPANDED TEENCODE & SLANG (300+ terms)
TEENCODE_EXPANDED = {
    # Single letters & abbreviations
    'j': 'gì', 'z': 'gì', 'dzì': 'gì', 'gj': 'gì',
    'v': 'với', 'vs': 'với', 'w': 'với',
    'k': 'không', 'ko': 'không', 'hk': 'không', 'hông': 'không', 'hok': 'không',
    'dc': 'được', 'đc': 'được', 'dc': 'được',
    'r': 'rồi', 'rùi': 'rồi', 'roi': 'rồi',
    'cx': 'cũng', 'cug': 'cũng', 'cg': 'cũng',
    'y': 'ý', 'ey': 'ý', 'e': 'tôi',
    'm': 'mình', 'mk': 'mình', 'tao': 'tôi',
    'nó': 'nó', 'no': 'nó',
    
    # Common words
    'nè': 'này', 'ni': 'này', 'ny': 'này', 'nek': 'nhé', 'nka': 'nhé', 'nha': 'nhé',
    'trc': 'trước', 'trog': 'trong', 'tr': 'trong',
    'ma': 'mà', 'mak': 'mà', 'ma': 'mà',
    'sao': 'sao', 'sáo': 'sao',
    
    # Slang for quality
    'xịn': 'tốt', 'xịn xò': 'sang trọng', 'xịn sò': 'sang trọng',
    'bá': 'rất', 'bá cháy': 'rất ngon', 'bá đơm': 'rất tuyệt',
    'xỉu': 'rất', 'xỉu up': 'rất tốt',
    'oke': 'tốt', 'ok': 'tốt', 'oce': 'tốt', 'okee': 'tốt',
    'top': 'tốt', 'chất': 'tốt', 'fải': 'phải',
    'ngầu': 'đẹp', 'ngầu lắm': 'rất đẹp',
    'chất lừ': 'rất tốt', 'chất cơm': 'rất tốt',
    'cute': 'đẹp', 'xinh': 'xinh',
    'bựa': 'tốt', 'bựa lắm': 'rất tốt',
    'phét': 'tuyệt vời', 'phết': 'tuyệt vời',
    'khét': 'nổi tiếng', 'khét legit': 'nổi tiếng thật',
    
    # Slang for price
    'hạt dẻ': 'rẻ', 'hạt rẻ': 'rẻ', 'hạt dẻ thôi': 'giá rẻ',
    'mềm': 'rẻ', 'mềm móng': 'giá rẻ', 'mềm túi': 'rẻ',
    'bèo': 'rẻ', 'bèo bọt': 'giá rẻ', 'bèo lắm': 'rẻ tuyệt',
    'vài trăm': 'rẻ', 'vài chục': 'rẻ', 'vài cái': 'rẻ',
    'cháy túi': 'đắt', 'chát': 'đắt', 'chát cơm': 'đắt',
    'chít': 'ít', 'chút': 'ít',
    'đắk': 'đắt', 'đắc': 'đắt',
    
    # Food slang
    'qs': 'quán', 'q': 'quán', 'qa': 'quán ăn', 'qã': 'quán ăn',
    'hs': 'hải sản', 'ăn hs': 'ăn hải sản',
    're': 'rẻ', 'r.e': 'rẻ',
    'tôm cua': 'hải sản',
    'bún bò': 'bún bò huế', 'bún bò hue': 'bún bò huế',
    'phở tái': 'phở', 'phở nạm': 'phở', 'phở bò': 'phở',
    
    # Negation variations
    'kh': 'không', 'khôg': 'không', 'khong': 'không',
    'hôm': 'không', 'hem': 'không', 'hen': 'không',
    
    # Interjections
    'oy': 'ơi', 'oii': 'ơi', 'ơii': 'ơi',
    'à': 'à', 'á': 'à', 'ợ': 'ơi',
    'a': 'à', 'eh': 'à',
    
    # Informal endings
    'thôi': 'thôi', 'tui': 'tôi', 'thui': 'thôi',
    'luôn': 'luôn', 'lun': 'luôn', 'luôn thôi': 'luôn',
    'nhỉ': 'nhỉ', 'nhi': 'nhỉ',
    'mà sao': 'sao lại', 'mà': 'mà',
    
    # Spelling variations
    'chảy': 'chảy', 'chay': 'chay', 'chả': 'chả',
    'mở': 'mở', 'mo': 'mở',
    'gần': 'gần', 'gan': 'gần', 'gàn': 'gần',
    'xa': 'xa', 'xát': 'xa',
    
    # Modern slang
    'vl': 'vậy', 'vcl': 'vậy chứ lạ',
    'lol': 'haha', 'rofl': 'haha',
    'omg': 'ơi thần ơi', 'omgg': 'ơi thần ơi',
}

# Common Vietnamese typos & corrections
TYPO_CORRECTIONS = {
    # Vowel confusions
    'phỏ': 'phở', 'pho': 'phở', 'phô': 'phở',
    'bun': 'bún', 'bùn': 'bún',
    'banh': 'bánh', 'bành': 'bánh', 'bánh': 'bánh',
    'com': 'cơm', 'côm': 'cơm', 'comm': 'cơm',
    'chau': 'chảu', 'cháu': 'chảu',
    
    # Consonant confusions
    'che': 'chè', 'chẻ': 'chè',
    'tra': 'trà', 'tà': 'trà',
    'ca phe': 'cà phê', 'cafe': 'cà phê', 'caffe': 'cà phê',
    'nuoc': 'nước', 'nước': 'nước',
    'thit': 'thịt', 'thị': 'thịt',
    'ga': 'gà', 'gá': 'gà',
    'bo': 'bò', 'bó': 'bò',
    'ca': 'cá', 'cả': 'cá',
    
    # Location typos
    'quan': 'quận', 'quân': 'quận',
    'quan 1': 'quận 1', 'q1': 'quận 1', 'q.1': 'quận 1',
    'ben thanh': 'bến thành', 'bến thành': 'bến thành',
    'tan binh': 'tân bình', 'tân bình': 'tân bình',
    'tan phu': 'tân phú', 'tân phú': 'tân phú',
    
    # Restaurant typos
    'pho hoa': 'phở hòa', 'phở hòa': 'phở hòa',
    'banh mi': 'bánh mì', 'bánh mì': 'bánh mì',
    'bun bo': 'bún bò', 'bún bò': 'bún bò',
    'lau': 'lẩu', 'lẩu': 'lẩu',
    'nuong': 'nướng', 'nướng': 'nướng',
    'chien': 'chiên', 'chiên': 'chiên',
    
    # Attribute typos
    'dep': 'đẹp', 'đẹp': 'đẹp',
    'sach': 'sạch', 'sạch': 'sạch',
    'duc': 'đặc', 'đặc': 'đặc',
    'chua': 'chưa', 'chưa': 'chưa',
    'khong': 'không', 'không': 'không',
}

# Vietnamese food synonyms - BASED ON REAL DATA (food_tags from 2057 restaurants)
# Extracted from data.json: buffet, bình dân, cafe, cơm, hải sản, lẩu, món chiên, món kho, 
#                            món nước, món nướng, món xào, nướng, tráng miệng, ăn vặt, đồ chay, đồ uống
FOOD_SYNONYMS = {
    # Main dishes
    'cơm': ['cơm tấm', 'cơm bình dân', 'cơm chiên', 'cơm bụi', 'rice', 'com tam', 'cơm niêu', 'cơm gà'],
    'món nước': ['phở', 'bún', 'mì', 'hủ tiếu', 'bánh canh', 'soup', 'noodle soup', 'phở bò', 'phở gà', 'bún bò'],
    'phở': ['phở tái', 'phở nạm', 'phở bò', 'phở gà', 'phở chay', 'pho', 'beef noodle'],
    'bún': ['bún bò', 'bún bò huế', 'bún chả', 'bún cua', 'bún thịt nướng', 'bun bo'],
    'mì': ['mì xào', 'mì quảng', 'mì ý', 'pasta', 'noodle', 'hủ tiếu'],
    'hải sản': ['tôm cua', 'cá', 'mực', 'tôm', 'cua', 'ốc', 'nghêu', 'sò', 'seafood', 'hải sản nướng'],
    'lẩu': ['lẩu thái', 'lẩu hải sản', 'lẩu cá', 'lẩu bò', 'lẩu gà', 'hotpot', 'lẩu nấm'],
    'buffet': ['tiệc', 'ăn thoải mái', 'all you can eat', 'buffet hải sản', 'buffet nướng', 'buffet lẩu'],
    
    # Cooking methods from data.json
    'nướng': ['món nướng', 'thịt nướng', 'cá nướng', 'nướng than', 'bbq', 'grilled', 'nướng lụi', 'nướng xiên'],
    'món nướng': ['nướng', 'nướng than', 'nướng hải sản', 'nướng lụi', 'bbq', 'grill'],
    'chiên': ['món chiên', 'chiên giòn', 'chiên xù', 'gà rán', 'fried', 'deep fried', 'rán'],
    'món chiên': ['chiên', 'chiên giòn', 'chiên xù', 'rán', 'fried'],
    'xào': ['món xào', 'xào rau', 'xào thịt', 'xào hải sản', 'stir fry', 'stir fried'],
    'món xào': ['xào', 'xào lăn', 'xào tỏi', 'stir fry'],
    'kho': ['món kho', 'kho tộ', 'cá kho', 'thịt kho', 'braised', 'kho quẹt'],
    'món kho': ['kho', 'kho tộ', 'braised'],
    
    # Snacks & drinks from data.json
    'ăn vặt': ['vặt', 'snack', 'bánh tráng', 'xôi', 'quẩy', 'chè', 'street food'],
    'tráng miệng': ['dessert', 'ngọt', 'chè', 'kem', 'bánh ngọt', 'yaourt', 'flan'],
    'đồ uống': ['drink', 'nước', 'nước ép', 'sinh tố', 'trà', 'cà phê', 'beverage', 'nước giải khát'],
    'cafe': ['cà phê', 'coffee', 'coffee shop', 'quán cafe', 'cà phê sữa', 'cappuccino'],
    'cà phê': ['cafe', 'coffee', 'cà phê sữa', 'cà phê đen', 'cappuccino', 'latte'],
    'trà': ['trà sữa', 'trà đá', 'trà nóng', 'tea', 'milk tea'],
    'chè': ['chè ba màu', 'dessert', 'sweet soup'],
    
    # Special types from data.json
    'chay': ['đồ chay', 'chay trường', 'vegetarian', 'vegan', 'không thịt', 'cơm chay', 'phở chay', 'bún chay'],
    'đồ chay': ['chay', 'vegetarian', 'vegan', 'chay trường'],
    'bình dân': ['rẻ', 'giá rẻ', 'sinh viên', 'đại chúng', 'quán vỉa hè', 'affordable'],
    
    # Other dishes
    'bánh mì': ['bánh mỳ', 'sandwich', 'bánh', 'bánh mì pâté', 'bánh mì xá xíu'],
    'gỏi': ['gỏi cuốn', 'gỏi xoài', 'salad', 'nem cuốn'],
}

# Location abbreviations
LOCATION_SYNONYMS = {
    'q1': 'quận 1', 'q.1': 'quận 1', 'quan 1': 'quận 1',
    'q2': 'quận 2', 'q.2': 'quận 2',
    'q3': 'quận 3', 'q.3': 'quận 3',
    'q4': 'quận 4', 'q.4': 'quận 4',
    'q5': 'quận 5', 'q.5': 'quận 5',
    'q6': 'quận 6', 'q.6': 'quận 6',
    'q7': 'quận 7', 'q.7': 'quận 7',
    'q8': 'quận 8', 'q.8': 'quận 8',
    'q9': 'quận 9', 'q.9': 'quận 9',
    'q10': 'quận 10', 'q.10': 'quận 10',
    'q11': 'quận 11', 'q.11': 'quận 11',
    'q12': 'quận 12', 'q.12': 'quận 12',
    'tq': 'tân bình', 'tb': 'tân bình',
    'tphu': 'tân phú', 'tp': 'tân phú',
    'binh tan': 'bình tân', 'bt': 'bình tân',
    'binh thanh': 'bình thạnh', 'bth': 'bình thạnh',
    'bvn': 'bến vân đồn', 'bvđ': 'bến vân đồn',
    'bt': 'bình tân', 'bth': 'bình thạnh',
    'cb': 'cầu giấy', 'cg': 'cầu giấy', 'nhân chính': 'nhân chính',
}


def normalize_advanced(text: str) -> str:
    """
    Advanced normalization: teencode + typos + code-switching.
    
    Args:
        text: Raw user input
        
    Returns:
        Normalized text
    """
    if not text:
        return ""
    
    text_lower = text.lower().strip()
    
    # Step 1: Handle code-switching (Vietnamese + English mixed)
    text_lower = _handle_code_switching(text_lower)
    
    # Step 2: Expand teencode/slang (sorted by length, longest first)
    sorted_terms = sorted(TEENCODE_EXPANDED.items(), key=lambda x: len(x[0]), reverse=True)
    for teencode, standard in sorted_terms:
        if len(teencode) <= 2:
            # Use word boundaries for short terms
            text_lower = re.sub(r'\b' + re.escape(teencode) + r'\b', standard, text_lower)
        else:
            # Exact replacement for longer terms
            text_lower = text_lower.replace(teencode, standard)
    
    # Step 3: Fix typos
    sorted_typos = sorted(TYPO_CORRECTIONS.items(), key=lambda x: len(x[0]), reverse=True)
    for typo, correct in sorted_typos:
        text_lower = re.sub(r'\b' + re.escape(typo) + r'\b', correct, text_lower)
    
    # Step 4: Expand food synonyms in context
    text_lower = _expand_synonyms(text_lower, FOOD_SYNONYMS)
    
    # Step 5: Expand location abbreviations
    sorted_locs = sorted(LOCATION_SYNONYMS.items(), key=lambda x: len(x[0]), reverse=True)
    for abbrev, full in sorted_locs:
        text_lower = re.sub(r'\b' + re.escape(abbrev) + r'\b', full, text_lower)
    
    # Step 6: Clean up extra whitespace
    text_lower = re.sub(r'\s+', ' ', text_lower).strip()
    
    return text_lower


def _handle_code_switching(text: str) -> str:
    """
    Handle mixed Vietnamese-English queries.
    
    Examples:
    - "find quán phở" → "tìm quán phở"
    - "where good bánh mì?" → "quán bánh mì ở đâu"
    """
    # Map English keywords to Vietnamese
    english_to_vi = {
        'find': 'tìm',
        'where': 'ở đâu',
        'how much': 'bao nhiêu',
        'price': 'giá',
        'restaurant': 'quán ăn',
        'food': 'thức ăn',
        'dish': 'món ăn',
        'near': 'gần',
        'close': 'gần',
        'good': 'ngon',
        'best': 'ngon nhất',
        'cheap': 'rẻ',
        'expensive': 'đắt',
        'open': 'mở cửa',
        'now': 'bây giờ',
        'today': 'hôm nay',
        'with': 'với',
        'for': 'cho',
        'people': 'người',
        'person': 'người',
    }
    
    text_lower = text.lower()
    for en, vi in english_to_vi.items():
        text_lower = re.sub(r'\b' + re.escape(en) + r'\b', vi, text_lower)
    
    return text_lower


def _expand_synonyms(text: str, synonym_map: Dict[str, List[str]]) -> str:
    """
    Expand synonyms to primary term with IMPROVED cross-language support.
    Logic: Allow cross-language expansion (coffee → cà phê) but preserve specific dish names.
    
    FIXED: Enable "coffee" → "cà phê", "cafe" → "cà phê" expansion
    """
    # Build set of all primary terms
    primary_terms = set(synonym_map.keys())
    
    # Cross-language exceptions: allow these to be expanded
    cross_language_allow = {
        'coffee', 'cafe', 'tea', 'beer', 'wine',  # English drinks
        'pizza', 'pasta', 'sushi', 'burger',      # International food
        'buffet', 'hotpot', 'bbq', 'grill'        # Cooking styles
    }
    
    for primary, synonyms in synonym_map.items():
        for synonym in synonyms:
            # Allow expansion if:
            # 1. Synonym is NOT a primary term, OR
            # 2. Synonym is in cross-language allow list
            if synonym not in primary_terms or synonym.lower() in cross_language_allow:
                text = re.sub(r'\b' + re.escape(synonym) + r'\b', primary, text, flags=re.IGNORECASE)
    
    return text


def check_spelling_vietnamese(word: str) -> bool:
    """
    Simple Vietnamese spelling check (basic pattern).
    
    Args:
        word: Word to check
        
    Returns:
        True if word looks like valid Vietnamese
    """
    # Check if word has valid Vietnamese structure
    # Valid Vietnamese words should have vowels and consonants
    has_vowel = bool(re.search(r'[aeiouàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ]', word.lower()))
    has_consonant = bool(re.search(r'[bcdfghjklmnpqrstvwxyzđ]', word.lower()))
    
    return has_vowel and has_consonant


def extract_entities_advanced(text: str) -> Dict[str, List[str]]:
    """
    Extract entities: locations, cuisines, attributes, numbers.
    
    Returns:
        Dictionary with extracted entities
    """
    entities = {
        'locations': [],
        'cuisines': [],
        'attributes': [],
        'numbers': [],
    }
    
    # Extract locations (quận X, bến thành, etc.)
    location_pattern = r'(?:quận|q|bến|phường|thành phố|huyện)[\s.]?(\d+|[a-zàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹ]+)'
    entities['locations'] = re.findall(location_pattern, text, re.IGNORECASE)
    
    # Extract cuisines (phở, bánh mì, etc.)
    cuisine_keywords = ['phở', 'bánh', 'bún', 'cơm', 'mì', 'hải sản', 'nướng', 'lẩu', 'gỏi']
    for cuisine in cuisine_keywords:
        if cuisine in text:
            entities['cuisines'].append(cuisine)
    
    # Extract numbers (prices, distances, people)
    number_pattern = r'\d+(?:[.,]\d+)?'
    entities['numbers'] = re.findall(number_pattern, text)
    
    return entities


def get_normalization_confidence(original: str, normalized: str) -> float:
    """
    Score how confident we are in the normalization.
    
    Returns:
        Confidence score 0-1
    """
    if original == normalized:
        return 1.0  # No changes = high confidence
    
    # Teencode/slang → lower confidence (more guessing)
    if any(term in original.lower() for term in ['j', 'z', 'k', 'cx', 'r', 'vs']):
        return 0.75
    
    # Typo correction → medium confidence
    if original.lower() != normalized.lower():
        return 0.85
    
    return 0.9


# Export
__all__ = [
    'normalize_advanced',
    'check_spelling_vietnamese',
    'extract_entities_advanced',
    'get_normalization_confidence',
]
