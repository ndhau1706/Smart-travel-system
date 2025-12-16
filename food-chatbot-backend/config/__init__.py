"""Configuration package."""
from .settings import settings
from .synonyms import (
    VIETNAMESE_FOOD_SYNONYMS,
    CUISINE_TYPES,
    ATMOSPHERE_KEYWORDS,
    PRICE_KEYWORDS
)

__all__ = [
    "settings",
    "VIETNAMESE_FOOD_SYNONYMS",
    "CUISINE_TYPES",
    "ATMOSPHERE_KEYWORDS",
    "PRICE_KEYWORDS"
]
