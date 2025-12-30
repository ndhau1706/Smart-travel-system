"""Utils package."""
from .text_processing import (
    strip_accents,
    normalize_text,
    tokenize_vietnamese,
    expand_synonyms,
    detect_cuisine_type,
    detect_atmosphere,
    extract_price_range,
    extract_distance,
    extract_location,
    normalize_teencode,
)
from .language_utils import detect_language, is_food_related
from .restaurant_utils import (
    is_restaurant_open,
    calculate_distance,
    format_distance,
    calculate_trending_score,
    get_restaurant_badges,
    analyze_review_sentiment,
    extract_signature_dishes,
    format_review_insights,
    detect_group_size,
    is_group_friendly
)

# NEW: Advanced modules for GPT-level understanding
from .advanced_input_processor import (
    normalize_advanced,
    check_spelling_vietnamese,
    extract_entities_advanced,
    get_normalization_confidence,
)
from .food_taxonomy import (
    SemanticUnderstandingEngine,
    semantic_engine,
    FOOD_TAXONOMY,
    COOKING_METHODS,
    TASTE_PROFILES,
    INGREDIENTS,
    ATMOSPHERE_TYPES,
)
from .intent_classifier import (
    IntentClassifier,
    IntentType,
    SubIntent,
    intent_classifier,
)
from .input_validator import (
    InputValidator,
    input_validator,
)
from .error_recovery import (
    ErrorRecoveryEngine,
    FallbackResponseGenerator,
)
from .restaurant_validator import (
    RestaurantValidator,
    restaurant_validator,
)

__all__ = [
    # Original exports
    "strip_accents",
    "normalize_text",
    "tokenize_vietnamese",
    "expand_synonyms",
    "detect_cuisine_type",
    "detect_atmosphere",
    "extract_price_range",
    "extract_distance",
    "extract_location",
    "normalize_teencode",
    "detect_language",
    "is_food_related",
    "is_restaurant_open",
    "calculate_distance",
    "format_distance",
    "calculate_trending_score",
    "get_restaurant_badges",
    "analyze_review_sentiment",
    "extract_signature_dishes",
    "format_review_insights",
    "detect_group_size",
    "is_group_friendly",
    
    # NEW: Advanced modules
    "normalize_advanced",
    "check_spelling_vietnamese",
    "extract_entities_advanced",
    "get_normalization_confidence",
    "SemanticUnderstandingEngine",
    "semantic_engine",
    "FOOD_TAXONOMY",
    "COOKING_METHODS",
    "TASTE_PROFILES",
    "INGREDIENTS",
    "ATMOSPHERE_TYPES",
    "IntentClassifier",
    "IntentType",
    "SubIntent",
    "intent_classifier",
    "ErrorRecoveryEngine",
    "FallbackResponseGenerator",
    "RestaurantValidator",
    "restaurant_validator",
]
