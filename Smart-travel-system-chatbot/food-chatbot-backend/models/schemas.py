"""
Pydantic models for API requests and responses.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union, Tuple, ClassVar
from datetime import datetime
import re
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


def validate_url_safe(url: str) -> Optional[str]:
    """
    Validate URL for security issues.
    
    Blocks:
    - javascript: protocol (XSS)
    - data: protocol (XSS)
    - file: protocol (local file access)
    - vbscript: protocol
    - UNC paths (Windows)
    - Protocol-relative URLs without explicit http/https
    - URLs with @ symbol (credential phishing)
    - Homograph attacks (non-ASCII domains)
    
    Args:
        url: URL string to validate
        
    Returns:
        Validated URL or None if invalid/dangerous
    """
    if not url or not isinstance(url, str):
        return None
    
    url = url.strip()
    
    # Empty or whitespace-only
    if not url:
        return None
    
    # Block dangerous protocols
    dangerous_protocols = [
        'javascript:', 'data:', 'file:', 'vbscript:', 'about:',
        'jar:', 'ms-its:', 'mhtml:', 'x-javascript:'
    ]
    
    url_lower = url.lower()
    for protocol in dangerous_protocols:
        if url_lower.startswith(protocol):
            logger.warning(f"Blocked dangerous URL protocol: {protocol}")
            return None
    
    # Block UNC paths (Windows)
    if url.startswith('\\\\'):
        logger.warning("Blocked UNC path")
        return None
    
    # Block protocol-relative URLs (//evil.com)
    if url.startswith('//'):
        logger.warning("Blocked protocol-relative URL")
        return None
    
    # Parse URL
    try:
        parsed = urlparse(url)
    except Exception as e:
        logger.warning(f"Failed to parse URL: {e}")
        return None
    
    # Must have explicit http or https scheme
    if parsed.scheme not in ['http', 'https']:
        logger.warning(f"Invalid URL scheme: {parsed.scheme}")
        return None
    
    # Check for @ symbol (credential phishing)
    # http://legitimate.com@evil.com
    if '@' in parsed.netloc:
        logger.warning("Blocked URL with @ symbol (credential phishing)")
        return None
    
    # Check for homograph attacks (non-ASCII characters in domain)
    if parsed.netloc:
        try:
            # Try to encode as ASCII - will fail if contains non-ASCII
            parsed.netloc.encode('ascii')
        except UnicodeEncodeError:
            logger.warning("Blocked URL with non-ASCII domain (homograph attack)")
            return None
    
    # Check for suspicious patterns
    # Multiple dots: chatbot....com
    if '..' in parsed.netloc:
        logger.warning("Blocked URL with consecutive dots")
        return None
    
    # CRLF injection
    if '\r' in url or '\n' in url:
        logger.warning("Blocked URL with CRLF characters")
        return None
    
    # Null bytes
    if '\x00' in url:
        logger.warning("Blocked URL with null byte")
        return None
    
    # Reconstruct URL to remove any encoding tricks
    # This normalizes the URL
    try:
        safe_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            safe_url += f"?{parsed.query}"
        if parsed.fragment:
            safe_url += f"#{parsed.fragment}"
        return safe_url
    except Exception as e:
        logger.warning(f"Failed to reconstruct URL: {e}")
        return None


class ChatRequest(BaseModel):
    """Chat request model with comprehensive validation."""
    session_id: Optional[str] = None
    message: str = Field(..., min_length=1, max_length=2000, description="User message (1-2000 chars)")
    user_id: Optional[str] = None
    user_location: Optional[Union[Dict[str, float], List[float], Tuple[float, float]]] = Field(
        None, 
        description="User's location: dict {'lat': float, 'lon': float}, list [lat, lon], or tuple (lat, lon)"
    )
    
    @validator('message')
    def validate_message(cls, v):
        """Validate message for security and quality."""
        if not v or not v.strip():
            raise ValueError('Message cannot be empty or whitespace only')
        
        # Remove leading/trailing whitespace
        v = v.strip()
        
        # Security: Check for potential XSS/injection patterns
        dangerous_patterns = [
            r'<script[^>]*>.*?</script>',
            r'javascript:',
            r'onerror\s*=',
            r'onclick\s*=',
            r'<iframe',
            r'<object',
            r'<embed',
        ]
        for pattern in dangerous_patterns:
            if re.search(pattern, v, re.IGNORECASE):
                raise ValueError('Invalid content detected')
        
        # Length validation (already in Field, but double-check)
        if len(v) > 2000:
            raise ValueError('Message too long (max 2000 characters)')
        
        return v
    
    @validator('session_id')
    def validate_session_id(cls, v):
        """Validate session ID format."""
        if v is not None:
            # Check format (UUID or alphanumeric)
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Invalid session ID format')
            if len(v) > 100:
                raise ValueError('Session ID too long')
        return v
    
    @validator('user_location')
    def validate_location(cls, v):
        """
        BUG #12 FIX: Validate user location coordinates with comprehensive checks.
        
        Supports multiple formats:
        - {'lat': float, 'lon': float}
        - {'lat': float, 'lng': float}
        - [lat, lon] list/tuple
        """
        if v is not None:
            from utils.location_utils import validate_location_format, parse_location
            
            # Validate format
            is_valid, error_msg = validate_location_format(v)
            if not is_valid:
                raise ValueError(f'Invalid location: {error_msg}')
            
            # Parse to ensure it's processable
            parsed = parse_location(v)
            if parsed is None:
                raise ValueError('Location could not be parsed (invalid coordinates)')
            
            # Normalize to standard format (dict with lat/lon)
            lat, lon = parsed
            return {'lat': lat, 'lon': lon}
        
        return v

class RestaurantInfo(BaseModel):
    """Restaurant information model with length validation."""
    
    # BUG #28 FIX: Add max_length to prevent memory exhaustion
    MAX_NAME_LENGTH: ClassVar[int] = 500
    MAX_ADDRESS_LENGTH: ClassVar[int] = 1000
    MAX_PHONE_LENGTH: ClassVar[int] = 50
    MAX_WEBSITE_LENGTH: ClassVar[int] = 2048  # Standard max URL length
    MAX_PRICE_LEVEL_LENGTH: ClassVar[int] = 20
    MAX_DISTANCE_TEXT_LENGTH: ClassVar[int] = 100
    MAX_OPEN_STATUS_LENGTH: ClassVar[int] = 200
    MAX_REVIEW_INSIGHTS_LENGTH: ClassVar[int] = 5000
    MAX_LIST_SIZE: ClassVar[int] = 100  # Max items in lists (food_tags, badges, etc.)
    MAX_TAG_LENGTH: ClassVar[int] = 100  # Max length of individual tag
    
    id: Optional[int] = None
    name: str = Field(..., max_length=500, description="Restaurant name (max 500 chars)")
    address: Optional[str] = Field(None, max_length=1000, description="Address (max 1000 chars)")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number (max 50 chars)")
    website: Optional[str] = Field(None, max_length=2048, description="Website URL (max 2048 chars)")
    rating: Optional[float] = None
    rating_count: Optional[int] = None
    price_level: Optional[str] = Field(None, max_length=20, description="Price level (max 20 chars)")
    food_tags: Optional[List[str]] = None
    coordinates_lat: Optional[float] = None
    coordinates_lon: Optional[float] = None
    distance: Optional[float] = None
    distance_text: Optional[str] = Field(None, max_length=100, description="Distance text (max 100 chars)")
    relevance_score: Optional[float] = None
    trending_score: Optional[float] = None
    is_open: Optional[bool] = None
    open_status: Optional[str] = Field(None, max_length=200, description="Open status (max 200 chars)")
    badges: Optional[List[str]] = None
    signature_dishes: Optional[List[str]] = None
    review_insights: Optional[str] = Field(None, max_length=5000, description="Review insights (max 5000 chars)")
    
    @validator('website')
    def validate_website(cls, v):
        """
        Validate website URL for security.
        
        Prevents:
        - XSS via javascript: protocol
        - Phishing via malicious domains
        - Local file access via file: protocol
        - Data URIs
        - Protocol-relative URLs
        - Homograph attacks
        """
        if v is None:
            return None
        
        # Validate and sanitize URL
        safe_url = validate_url_safe(v)
        
        if safe_url is None:
            # Invalid/dangerous URL - return None instead of raising
            # This prevents data poisoning from crashing the system
            logger.warning(f"Invalid website URL rejected: {v}")
            return None
        
        return safe_url
    
    @validator('food_tags', 'badges', 'signature_dishes')
    def validate_list_fields(cls, v):
        """BUG #28 FIX: Validate list fields for size and item length."""
        if v is None:
            return None
        
        # Check list size
        if len(v) > cls.MAX_LIST_SIZE:
            raise ValueError(f'List too large: {len(v)} items (max {cls.MAX_LIST_SIZE})')
        
        # Check individual item lengths
        for item in v:
            if isinstance(item, str) and len(item) > cls.MAX_TAG_LENGTH:
                raise ValueError(f'List item too long: {len(item)} chars (max {cls.MAX_TAG_LENGTH})')
        
        return v
    relevance_score: Optional[float] = None
    explanation: Optional[str] = None  # Why this restaurant was recommended


class ChatResponse(BaseModel):
    """Chat response model with length validation."""
    
    # BUG #28 FIX: Add max_length to prevent memory exhaustion
    MAX_SESSION_ID_LENGTH: ClassVar[int] = 100
    MAX_MESSAGE_LENGTH: ClassVar[int] = 10000  # 10KB for response messages
    MAX_LANGUAGE_LENGTH: ClassVar[int] = 10
    MAX_EXPLANATION_LENGTH: ClassVar[int] = 5000
    MAX_RESTAURANTS_COUNT: ClassVar[int] = 50  # Max restaurants in response
    
    session_id: str = Field(..., max_length=100)
    message: str = Field(..., max_length=10000, description="Response message (max 10KB)")
    restaurants: Optional[List[RestaurantInfo]] = None
    language: str = Field(..., max_length=10)
    explanation: Optional[str] = Field(None, max_length=5000, description="Explanation (max 5KB)")
    metadata: Optional[Dict[str, Any]] = None
    
    @validator('restaurants')
    def validate_restaurants(cls, v):
        """BUG #28 FIX: Validate restaurant list size."""
        if v is None:
            return None
        
        if len(v) > cls.MAX_RESTAURANTS_COUNT:
            raise ValueError(f'Too many restaurants: {len(v)} (max {cls.MAX_RESTAURANTS_COUNT})')
        
        return v
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """BUG #28 FIX: Validate metadata JSON size."""
        if v is None:
            return None
        
        import json
        try:
            serialized = json.dumps(v)
            if len(serialized) > 50000:  # 50KB max
                raise ValueError(f'Metadata too large: {len(serialized)} bytes (max 50KB)')
        except (TypeError, ValueError) as e:
            raise ValueError(f'Invalid metadata: {e}')
        
        return v


class SessionCreate(BaseModel):
    """Session creation request with length validation."""
    
    # BUG #28 FIX: Add max_length to prevent memory exhaustion
    MAX_USER_ID_LENGTH: ClassVar[int] = 100
    MAX_TITLE_LENGTH: ClassVar[int] = 500
    MAX_LANGUAGE_LENGTH: ClassVar[int] = 10
    
    user_id: Optional[str] = Field(None, max_length=100, description="User ID (max 100 chars)")
    title: Optional[str] = Field("New Chat", max_length=500, description="Session title (max 500 chars)")
    language: Optional[str] = Field("vi", max_length=10, description="Language code (max 10 chars)")


class SessionInfo(BaseModel):
    """Session information."""
    id: str
    user_id: Optional[str] = None
    title: str
    language: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0


class MessageInfo(BaseModel):
    """Message information with length validation."""
    
    # BUG #28 FIX: Add max_length to prevent memory exhaustion
    MAX_SESSION_ID_LENGTH: ClassVar[int] = 100
    MAX_ROLE_LENGTH: ClassVar[int] = 50
    MAX_CONTENT_LENGTH: ClassVar[int] = 10000  # 10KB for stored messages (larger than input to allow system messages)
    
    id: int
    session_id: str = Field(..., max_length=100)
    role: str = Field(..., max_length=50)
    content: str = Field(..., max_length=10000, description="Message content (max 10KB)")
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    @validator('metadata')
    def validate_metadata(cls, v):
        """BUG #28 FIX: Validate metadata JSON size."""
        if v is None:
            return None
        
        # Check JSON size when serialized
        import json
        try:
            serialized = json.dumps(v)
            if len(serialized) > 50000:  # 50KB max for metadata JSON
                raise ValueError(f'Metadata too large: {len(serialized)} bytes (max 50KB)')
        except (TypeError, ValueError) as e:
            raise ValueError(f'Invalid metadata: {e}')
        
        return v


class FeedbackRequest(BaseModel):
    """User feedback request with length validation."""
    
    # BUG #28 FIX: Add max_length to prevent memory exhaustion
    MAX_SESSION_ID_LENGTH: ClassVar[int] = 100
    MAX_COMMENT_LENGTH: ClassVar[int] = 5000  # 5KB for detailed feedback
    
    session_id: str = Field(..., max_length=100, description="Session ID (max 100 chars)")
    message_id: Optional[int] = None
    restaurant_id: Optional[int] = None
    feedback_type: str = Field(..., pattern="^(positive|negative|neutral)$")
    rating: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=5000, description="Feedback comment (max 5000 chars)")


class FeedbackResponse(BaseModel):
    """Feedback response."""
    success: bool
    message: str


class SessionListResponse(BaseModel):
    """Session list response."""
    sessions: List[SessionInfo]
    total: int


class SessionHistoryResponse(BaseModel):
    """Session history response."""
    session: SessionInfo
    messages: List[MessageInfo]


class ErrorResponse(BaseModel):
    """Error response."""
    error: str
    detail: Optional[str] = None
