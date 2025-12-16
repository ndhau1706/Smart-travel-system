"""
Advanced restaurant utility functions for enhanced recommendations.
Includes: time-aware filtering, distance calculation, trending score, review analysis, dish extraction.
"""
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, time
import re
import math
from collections import Counter


def parse_time_range(time_str: str) -> Optional[Tuple[time, time]]:
    """
    Parse time range string like "09:00–23:30" to (start_time, end_time).
    
    Args:
        time_str: Time range string
        
    Returns:
        Tuple of (start_time, end_time) or None if parsing fails
    """
    if not time_str or time_str == "Closed" or time_str == "Đóng cửa":
        return None
    
    try:
        # Handle various formats: "09:00–23:30", "09:00-23:30", "9:00 - 23:30"
        time_str = time_str.replace(" ", "").replace("–", "-").replace("—", "-")
        
        if "-" not in time_str:
            return None
            
        start_str, end_str = time_str.split("-", 1)
        
        # Parse start time
        start_hour, start_min = map(int, start_str.split(":"))
        start = time(start_hour, start_min)
        
        # Parse end time
        end_hour, end_min = map(int, end_str.split(":"))
        end = time(end_hour, end_min)
        
        return (start, end)
    except:
        return None


def is_restaurant_open(opening_hours: Dict[str, str], check_time: Optional[datetime] = None) -> Tuple[bool, str]:
    """
    Check if restaurant is currently open.
    
    Args:
        opening_hours: Dictionary of weekday -> time range (or JSON string)
        check_time: Time to check (defaults to now)
        
    Returns:
        Tuple of (is_open: bool, status_message: str)
    """
    if not opening_hours:
        return (True, "")  # Assume open if no hours provided
    
    # Handle case where opening_hours is a JSON string (from FAISS/BM25 storage)
    if isinstance(opening_hours, str):
        try:
            import json
            opening_hours = json.loads(opening_hours)
        except (json.JSONDecodeError, ValueError):
            # If it's not valid JSON, can't parse hours
            return (True, "")
    
    # If still not a dict, can't process
    if not isinstance(opening_hours, dict):
        return (True, "")
    
    if check_time is None:
        check_time = datetime.now()
    
    # Map Vietnamese weekday names to datetime weekday (0=Monday, 6=Sunday)
    weekday_map = {
        "Thứ Hai": 0,
        "Thứ Ba": 1,
        "Thứ Tư": 2,
        "Thứ Năm": 3,
        "Thứ Sáu": 4,
        "Thứ Bảy": 5,
        "Chủ Nhật": 6
    }
    
    current_weekday = check_time.weekday()
    current_time = check_time.time()
    
    # Find today's hours
    today_hours = None
    for vn_day, day_num in weekday_map.items():
        if day_num == current_weekday and vn_day in opening_hours:
            today_hours = opening_hours[vn_day]
            break
    
    if not today_hours:
        return (True, "")
    
    time_range = parse_time_range(today_hours)
    if not time_range:
        return (False, "Đóng cửa")
    
    start, end = time_range
    
    # Handle overnight hours (e.g., 22:00-02:00)
    if end < start:
        is_open = current_time >= start or current_time <= end
    else:
        is_open = start <= current_time <= end
    
    if is_open:
        # Calculate closing time
        closing_str = today_hours.split("–")[-1].split("-")[-1].strip()
        return (True, f"Đang mở cửa (đóng lúc {closing_str})")
    else:
        # Calculate opening time
        opening_str = today_hours.split("–")[0].split("-")[0].strip()
        return (False, f"Đã đóng cửa (mở lúc {opening_str})")


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.
    
    Args:
        lat1, lon1: First coordinate
        lat2, lon2: Second coordinate
        
    Returns:
        Distance in kilometers
    """
    # Radius of Earth in kilometers
    R = 6371.0
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return round(distance, 2)


def format_distance(distance_km: float, language: str = "vi") -> str:
    """
    Format distance with appropriate unit and emoji.
    
    Args:
        distance_km: Distance in kilometers
        language: Language for formatting
        
    Returns:
        Formatted distance string
    """
    if distance_km < 1:
        meters = int(distance_km * 1000)
        if language == "vi":
            return f"📍 Cách bạn {meters}m"
        else:
            return f"📍 {meters}m away"
    else:
        if language == "vi":
            return f"📍 Cách bạn {distance_km}km"
        else:
            return f"📍 {distance_km}km away"


def calculate_trending_score(rating: float, rating_count: int) -> float:
    """
    Calculate trending/popularity score for restaurant.
    
    Formula: rating * 0.4 + log10(rating_count + 1) * 0.6
    This balances quality (rating) with popularity (review count).
    
    Args:
        rating: Restaurant rating (0-5)
        rating_count: Number of ratings
        
    Returns:
        Trending score (0-10)
    """
    if rating is None or rating_count is None:
        return 0.0
    
    # Normalize rating to 0-10 scale
    rating_score = (rating / 5.0) * 10.0
    
    # Log scale for review count (diminishing returns for very popular places)
    # log10(1000) ≈ 3, log10(10000) ≈ 4
    popularity_score = math.log10(rating_count + 1) * 2.5  # Scale to 0-10 range
    
    # Weighted combination
    trending_score = (rating_score * 0.4) + (popularity_score * 0.6)
    
    return round(min(trending_score, 10.0), 2)


def get_restaurant_badges(
    rating: float,
    rating_count: int,
    trending_score: float,
    is_open: bool,
    distance: Optional[float] = None
) -> List[str]:
    """
    Generate badges for restaurant based on various criteria.
    
    Args:
        rating: Restaurant rating
        rating_count: Number of ratings
        trending_score: Calculated trending score
        is_open: Whether restaurant is currently open
        distance: Distance from user (km)
        
    Returns:
        List of badge strings
    """
    badges = []
    
    # Status badge
    if is_open:
        badges.append("🟢 ĐANG MỞ")
    else:
        badges.append("🔴 ĐÓNG CỬA")
    
    # Quality badges
    if rating >= 4.5:
        badges.append("⭐ TOP RATED")
    
    # Popularity badges
    if rating_count >= 5000:
        badges.append("🔥 HOT")
    elif rating_count >= 1000:
        badges.append("👍 PHỔ BIẾN")
    
    # Trending badge
    if trending_score >= 8.0:
        badges.append("📈 TRENDING")
    
    # Distance badge
    if distance is not None:
        if distance < 1:
            badges.append("🚶 GẦN BẠN")
        elif distance < 3:
            badges.append("🚴 DỄ TỚI")
    
    return badges


def analyze_review_sentiment(comments: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze reviews to extract insights about food, service, price, atmosphere.
    
    Args:
        comments: List of comment dictionaries with 'text' and 'rating'
        
    Returns:
        Dictionary with sentiment analysis results
    """
    if not comments:
        return {}
    
    # Keywords for different aspects
    food_positive = ['ngon', 'tuyệt vời', 'hảo hạng', 'chất lượng', 'tươi ngon', 'đậm đà', 'thơm ngon', 'delicious', 'tasty', 'amazing']
    food_negative = ['dở', 'tệ', 'không ngon', 'nhạt', 'mặn', 'chua', 'bad', 'terrible', 'bland']
    
    service_positive = ['nhiệt tình', 'chu đáo', 'tốt', 'chuyên nghiệp', 'nhanh', 'thân thiện', 'friendly', 'professional', 'nice']
    service_negative = ['tệ', 'chậm', 'lạnh lùng', 'thiếu', 'không', 'bad service', 'rude', 'slow']
    
    price_positive = ['rẻ', 'hợp lý', 'bình dân', 'phải chăng', 'affordable', 'cheap', 'reasonable']
    price_negative = ['đắt', 'mắc', 'cao', 'không hợp lý', 'expensive', 'overpriced']
    
    atmosphere_positive = ['đẹp', 'sang trọng', 'thoáng', 'yên tĩnh', 'ấm cúng', 'beautiful', 'cozy', 'nice atmosphere']
    atmosphere_negative = ['chật', 'ồn', 'bẩn', 'cũ', 'crowded', 'noisy', 'dirty']
    
    insights = {
        'food': {'positive': 0, 'negative': 0, 'comments': []},
        'service': {'positive': 0, 'negative': 0, 'comments': []},
        'price': {'positive': 0, 'negative': 0, 'comments': []},
        'atmosphere': {'positive': 0, 'negative': 0, 'comments': []}
    }
    
    for comment in comments[:10]:  # Analyze top 10 recent comments
        # Skip None comments
        if comment is None or not isinstance(comment, dict):
            continue
        
        try:
            text = comment.get('text', '').lower() if comment.get('text') else ''
            rating = comment.get('rating', 3)
        except (AttributeError, TypeError):
            # Skip comments that can't be processed
            continue
        
        # Food analysis
        if any(word in text for word in food_positive):
            insights['food']['positive'] += 1
            if rating >= 4:
                insights['food']['comments'].append(text[:100])
        elif any(word in text for word in food_negative):
            insights['food']['negative'] += 1
        
        # Service analysis
        if any(word in text for word in service_positive):
            insights['service']['positive'] += 1
            if rating >= 4:
                insights['service']['comments'].append(text[:100])
        elif any(word in text for word in service_negative):
            insights['service']['negative'] += 1
        
        # Price analysis
        if any(word in text for word in price_positive):
            insights['price']['positive'] += 1
        elif any(word in text for word in price_negative):
            insights['price']['negative'] += 1
        
        # Atmosphere analysis
        if any(word in text for word in atmosphere_positive):
            insights['atmosphere']['positive'] += 1
        elif any(word in text for word in atmosphere_negative):
            insights['atmosphere']['negative'] += 1
    
    return insights


def extract_signature_dishes(comments: List[Dict[str, Any]], top_n: int = 5) -> List[str]:
    """
    Extract signature/recommended dishes from reviews.
    
    Args:
        comments: List of comment dictionaries
        top_n: Number of top dishes to return
        
    Returns:
        List of dish names mentioned frequently in positive reviews
    """
    if not comments:
        return []
    
    # Common Vietnamese dish patterns
    dish_patterns = [
        r'(phở|bún|cơm|bánh|lẩu|gỏi|chả|nem|mì|hủ tiếu|bò|gà|heo|tôm|cá|sườn|chả cá)\s+\w+',
        r'món\s+(\w+\s+\w+)',
    ]
    
    dish_mentions = []
    
    for comment in comments:
        # Skip None comments
        if comment is None or not isinstance(comment, dict):
            continue
            
        text = comment.get('text', '')
        if not text:  # Skip empty text
            continue
            
        rating = comment.get('rating', 3)
        
        # Only extract from positive reviews
        if rating >= 4:
            # Find dish mentions
            for pattern in dish_patterns:
                try:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    dish_mentions.extend(matches)
                except (TypeError, AttributeError):
                    continue
    
    # Count frequency
    if not dish_mentions:
        return []
    
    dish_counter = Counter([dish.strip().lower() for dish in dish_mentions if dish.strip()])
    top_dishes = [dish for dish, count in dish_counter.most_common(top_n)]
    
    return top_dishes


def format_review_insights(insights: Dict[str, Any], language: str = "vi") -> str:
    """
    Format review insights into human-readable text.
    
    Args:
        insights: Dictionary from analyze_review_sentiment
        language: Language for formatting
        
    Returns:
        Formatted insight text
    """
    if not insights:
        return ""
    
    messages = []
    
    # Food insights
    if insights['food']['positive'] > insights['food']['negative'] and insights['food']['positive'] >= 3:
        if language == "vi":
            messages.append("⭐ Nhiều người khen đồ ăn ngon")
        else:
            messages.append("⭐ Food highly praised")
    
    # Service insights
    if insights['service']['positive'] > insights['service']['negative'] and insights['service']['positive'] >= 3:
        if language == "vi":
            messages.append("👍 Phục vụ nhiệt tình")
        else:
            messages.append("👍 Great service")
    elif insights['service']['negative'] > insights['service']['positive'] and insights['service']['negative'] >= 2:
        if language == "vi":
            messages.append("⚠️ Một số phàn nàn về phục vụ")
        else:
            messages.append("⚠️ Some service complaints")
    
    # Price insights
    if insights['price']['positive'] > insights['price']['negative'] and insights['price']['positive'] >= 2:
        if language == "vi":
            messages.append("💰 Giá cả hợp lý")
        else:
            messages.append("💰 Good value")
    elif insights['price']['negative'] > insights['price']['positive'] and insights['price']['negative'] >= 2:
        if language == "vi":
            messages.append("⚠️ Có người cho rằng hơi đắt")
        else:
            messages.append("⚠️ Some find it pricey")
    
    # Atmosphere insights
    if insights['atmosphere']['positive'] >= 3:
        if language == "vi":
            messages.append("🏠 Không gian đẹp, thoải mái")
        else:
            messages.append("🏠 Nice atmosphere")
    
    return " • ".join(messages) if messages else ""


def detect_group_size(query: str) -> Optional[int]:
    """
    Detect group size from query.
    
    Args:
        query: User query
        
    Returns:
        Number of people or None
    """
    # Patterns for Vietnamese
    patterns = [
        r'(\d+)\s*người',
        r'tụi\s+(?:tôi|mình|bọn)\s+(\d+)',
        r'nhóm\s+(\d+)',
        r'nhóm\s+(\d+)\s*người',  # NEW: "nhóm 10 người" pattern
        r'cho\s+nhóm\s+(\d+)',  # NEW: "cho nhóm 10" pattern
        r'cho\s+nhóm\s+(\d+)\s*người',  # NEW: "cho nhóm 10 người" pattern
        r'group\s+of\s+(\d+)',
        r'(\d+)\s+people',
        r'(\d+)\s+pax'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except:
                pass
    
    return None


def is_group_friendly(
    restaurant: Dict[str, Any],
    group_size: int
) -> Tuple[bool, List[str]]:
    """
    Check if restaurant is suitable for groups.
    
    Args:
        restaurant: Restaurant data
        group_size: Number of people
        
    Returns:
        Tuple of (is_suitable, reasons)
    """
    reasons = []
    
    # Check food variety (groups need diverse menu)
    food_tags = restaurant.get('food_tags', [])
    if len(food_tags) >= 3:
        reasons.append("Menu đa dạng")
    
    # Check price level (groups prefer reasonable prices)
    price_level = restaurant.get('price_level', '')
    if 'MODERATE' in price_level or 'INEXPENSIVE' in price_level:
        reasons.append("Giá phù hợp nhóm")
    
    # Check category (some types are better for groups)
    category = restaurant.get('category', '')
    if any(word in category.lower() for word in ['nhà hàng', 'restaurant', 'buffet', 'lẩu', 'bbq']):
        reasons.append("Phù hợp nhóm đông")
    
    # Large groups (>6) need specific types
    if group_size > 6:
        if any(word in category.lower() for word in ['buffet', 'lẩu', 'bbq', 'nhà hàng']):
            reasons.append(f"Phục vụ nhóm {group_size} người")
    
    is_suitable = len(reasons) >= 2
    return (is_suitable, reasons)
