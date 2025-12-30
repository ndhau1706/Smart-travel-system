"""
BUG #13 FIX: Context-Aware Synonym Filter
Prevents synonym explosion by limiting and filtering synonyms based on query context.
"""
from typing import List, Dict, Set
import re
from config import VIETNAMESE_FOOD_SYNONYMS, CUISINE_TYPES


class SynonymFilter:
    """
    Context-aware synonym filter to prevent over-expansion.
    
    Key Features:
    - Max 5 synonyms per term (prevents explosion)
    - Cuisine-specific filtering (no Korean in Vietnamese query)
    - Ambiguity detection (skip ambiguous terms)
    - Context validation (only relevant synonyms)
    """
    
    # Max synonyms to return per term
    MAX_SYNONYMS_PER_TERM = 5
    
    # Cuisine markers for context detection
    CUISINE_MARKERS = {
        'vietnamese': ['việt', 'viet', 'vietnamese', 'vn', 'sài gòn', 'hà nội', 'huế'],
        'japanese': ['nhật', 'japan', 'japanese', 'sushi', 'ramen', 'tokyo'],
        'korean': ['hàn', 'korea', 'korean', 'kimchi', 'seoul', 'k-'],
        'thai': ['thái', 'thailand', 'thai', 'bangkok'],
        'chinese': ['trung', 'china', 'chinese', 'beijing'],
        'western': ['âu', 'tây', 'western', 'europe'],
        'italian': ['ý', 'italy', 'italian'],
    }
    
    # Ambiguous terms that should NOT be expanded
    AMBIGUOUS_TERMS = {
        'cay',  # spicy vs plant name
        'bơ',  # butter vs avocado
        'cafe',  # cafe music vs coffee shop
        'bánh mỳ',  # pasta vs sandwich (context-dependent)
        'chè',  # too generic (all desserts)
    }
    
    # Regional-specific terms (don't expand across regions)
    REGIONAL_TERMS = {
        'phở hà nội': {'region': 'hanoi'},
        'phở nam định': {'region': 'namdinh'},
        'phở sài gòn': {'region': 'saigon'},
        'cơm tấm sài gòn': {'region': 'saigon'},
        'bún bò huế': {'region': 'hue'},
    }
    
    # Cuisine-specific dishes (don't leak to other cuisines)
    CUISINE_SPECIFIC_DISHES = {
        'korean': ['kimchi', 'bulgogi', 'bibimbap', 'tteokbokki', 'samgyeopsal'],
        'japanese': ['sushi', 'sashimi', 'ramen', 'tempura', 'udon'],
        'thai': ['tom yum', 'pad thai', 'som tam'],
        'chinese': ['dimsum', 'dim sum', 'xá xíu'],
        'vietnamese': ['phở', 'bún', 'bánh mì', 'cơm tấm'],
    }
    
    def __init__(self):
        self._synonym_cache = {}
    
    def detect_cuisine_context(self, query: str) -> Set[str]:
        """
        Detect which cuisines are mentioned in the query.
        
        Args:
            query: User query
            
        Returns:
            Set of detected cuisine types
        """
        query_lower = query.lower()
        detected = set()
        
        for cuisine, markers in self.CUISINE_MARKERS.items():
            if any(marker in query_lower for marker in markers):
                detected.add(cuisine)
        
        return detected
    
    def is_cuisine_specific_term(self, term: str, cuisine: str) -> bool:
        """
        Check if a term is specific to a cuisine.
        
        Args:
            term: Term to check
            cuisine: Cuisine type
            
        Returns:
            True if term is specific to this cuisine
        """
        term_lower = term.lower()
        dishes = self.CUISINE_SPECIFIC_DISHES.get(cuisine, [])
        return any(dish in term_lower for dish in dishes)
    
    def filter_synonyms_by_context(
        self,
        canonical: str,
        synonyms: List[str],
        query_context: str
    ) -> List[str]:
        """
        Filter synonyms based on query context.
        
        Args:
            canonical: Canonical term
            synonyms: List of synonyms
            query_context: Full query for context
            
        Returns:
            Filtered list of synonyms (max 5)
        """
        # Detect cuisine context from query
        detected_cuisines = self.detect_cuisine_context(query_context)
        
        filtered = []
        
        for synonym in synonyms:
            # Skip if already at max
            if len(filtered) >= self.MAX_SYNONYMS_PER_TERM:
                break
            
            synonym_lower = synonym.lower()
            
            # Check 1: Skip cuisine-specific terms if wrong cuisine
            skip = False
            for cuisine, dishes in self.CUISINE_SPECIFIC_DISHES.items():
                # If query mentions cuisine A, skip synonyms from cuisine B
                if detected_cuisines and cuisine not in detected_cuisines:
                    if any(dish in synonym_lower for dish in dishes):
                        skip = True
                        break
            
            if skip:
                continue
            
            # Check 2: Skip regional variants if different region mentioned
            if any(region in synonym_lower for region in ['hà nội', 'nam định', 'sài gòn', 'huế']):
                # Only include if region matches query
                region_in_synonym = None
                for region_term, info in self.REGIONAL_TERMS.items():
                    if region_term in synonym_lower:
                        region_in_synonym = info['region']
                        break
                
                if region_in_synonym:
                    region_in_query = None
                    for region_term, info in self.REGIONAL_TERMS.items():
                        if region_term in query_context.lower():
                            region_in_query = info['region']
                            break
                    
                    # Skip if regions don't match and query specified a region
                    if region_in_query and region_in_query != region_in_synonym:
                        continue
            
            # Check 3: Prioritize exact translations over variations
            # E.g., "coffee" → "cà phê" is higher priority than "cà phê sữa đá"
            if ' ' not in synonym_lower or len(synonym_lower.split()) <= 2:
                # Prioritize simple synonyms (1-2 words)
                filtered.insert(0, synonym)
            else:
                filtered.append(synonym)
        
        # Limit to max synonyms
        return filtered[:self.MAX_SYNONYMS_PER_TERM]
    
    def get_filtered_synonyms(
        self,
        text: str,
        query_context: str = None
    ) -> Dict[str, List[str]]:
        """
        Get filtered synonyms for all terms in text.
        
        Args:
            text: Input text to expand
            query_context: Full query for context (optional)
            
        Returns:
            Dictionary of {canonical: [filtered_synonyms]}
        """
        if query_context is None:
            query_context = text
        
        # Cache key
        cache_key = f"{text}::{query_context}"
        if cache_key in self._synonym_cache:
            return self._synonym_cache[cache_key]
        
        result = {}
        text_lower = text.lower()
        
        for canonical, synonyms in VIETNAMESE_FOOD_SYNONYMS.items():
            canonical_lower = canonical.lower()
            
            # Check if canonical term is in text
            if canonical_lower not in text_lower:
                continue
            
            # Skip ambiguous terms
            if canonical_lower in self.AMBIGUOUS_TERMS:
                # Only use exact match, no expansion
                result[canonical] = [canonical]
                continue
            
            # Filter synonyms by context
            filtered = self.filter_synonyms_by_context(
                canonical,
                synonyms,
                query_context
            )
            
            if filtered:
                result[canonical] = filtered
        
        # Cache result
        self._synonym_cache[cache_key] = result
        return result
    
    def expand_with_context(
        self,
        text: str,
        query_context: str = None,
        max_variants: int = 10
    ) -> List[str]:
        """
        Expand text with context-aware synonyms.
        
        Args:
            text: Text to expand
            query_context: Full query for context
            max_variants: Maximum number of variants to return
            
        Returns:
            List of text variants (limited)
        """
        if query_context is None:
            query_context = text
        
        variants = [text, text.lower()]
        
        # Get filtered synonyms
        filtered_synonyms = self.get_filtered_synonyms(text, query_context)
        
        for canonical, synonyms in filtered_synonyms.items():
            canonical_lower = canonical.lower()
            
            for synonym in synonyms[:3]:  # Max 3 synonyms per term in expansion
                # Replace canonical with synonym
                if canonical_lower in text.lower():
                    variant = text.lower().replace(canonical_lower, synonym.lower())
                    if variant not in variants:
                        variants.append(variant)
                
                # Stop if reached max variants
                if len(variants) >= max_variants:
                    break
            
            if len(variants) >= max_variants:
                break
        
        return variants[:max_variants]


# Global instance
synonym_filter = SynonymFilter()
