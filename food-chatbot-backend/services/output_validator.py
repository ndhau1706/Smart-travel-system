"""
Output Validation Layer - Anti-hallucination mechanism.
Validates LLM responses against actual restaurant data.
"""
from typing import Dict, Any, List, Optional
import re
import logging

logger = logging.getLogger(__name__)


class OutputValidator:
    """Validates LLM output to prevent hallucinations."""
    
    def validate_response(
        self,
        llm_output: str,
        actual_restaurants: List[Dict[str, Any]],
        query: str
    ) -> Dict[str, Any]:
        """
        Validate LLM response against actual data.
        
        Args:
            llm_output: Generated text from LLM
            actual_restaurants: Actual restaurant data from database
            query: Original user query
            
        Returns:
            Validation result with warnings/corrections
        """
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "corrections": [],
            "validated_output": llm_output
        }
        
        if not actual_restaurants:
            return validation_result
        
        # 1. Check restaurant count hallucination
        count_issues = self._check_count_hallucination(llm_output, actual_restaurants)
        if count_issues:
            validation_result["warnings"].extend(count_issues)
        
        # 2. Check restaurant name hallucination
        name_issues = self._check_name_hallucination(llm_output, actual_restaurants)
        if name_issues:
            validation_result["warnings"].extend(name_issues)
            validation_result["is_valid"] = False
        
        # 3. Check price hallucination
        price_issues = self._check_price_hallucination(llm_output, actual_restaurants)
        if price_issues:
            validation_result["warnings"].extend(price_issues)
        
        # 4. Check rating hallucination
        rating_issues = self._check_rating_hallucination(llm_output, actual_restaurants)
        if rating_issues:
            validation_result["warnings"].extend(rating_issues)
        
        # 5. Check location hallucination
        location_issues = self._check_location_hallucination(llm_output, actual_restaurants)
        if location_issues:
            validation_result["warnings"].extend(location_issues)
        
        return validation_result
    
    def _check_count_hallucination(
        self,
        output: str,
        restaurants: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if LLM claims wrong number of restaurants."""
        warnings = []
        actual_count = len(restaurants)
        
        # Pattern: "5 quán", "10 nhà hàng", etc.
        patterns = [
            r'(\d+)\s*(?:quán|nhà hàng|chỗ|nơi)',
            r'(?:tìm thấy|có)\s*(\d+)',
            r'(?:gợi ý|giới thiệu)\s*(\d+)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, output.lower())
            for match in matches:
                claimed_count = int(match)
                if claimed_count != actual_count:
                    warnings.append(
                        f"Count mismatch: LLM claims {claimed_count} but actual is {actual_count}"
                    )
                    break
        
        return warnings
    
    def _check_name_hallucination(
        self,
        output: str,
        restaurants: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if LLM mentions restaurants not in data."""
        warnings = []
        actual_names = {r['name'].lower() for r in restaurants}
        
        # Extract potential restaurant names from output
        # Pattern: quoted names or capitalized phrases
        quoted_names = re.findall(r'["""](.*?)["""]', output)
        
        for name in quoted_names:
            name_lower = name.lower()
            # Check if this name matches any actual restaurant
            found = any(name_lower in actual_name or actual_name in name_lower 
                       for actual_name in actual_names)
            
            if not found and len(name.split()) >= 2:  # At least 2 words
                warnings.append(f"Potential hallucinated restaurant: '{name}'")
        
        return warnings
    
    def _check_price_hallucination(
        self,
        output: str,
        restaurants: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if LLM invents price information."""
        warnings = []
        
        # Extract price mentions (e.g., "50k", "100,000đ")
        price_patterns = [
            r'(\d+)[k|K](?:\s*đ)?',  # 50k
            r'(\d{1,3}(?:,\d{3})+)(?:\s*đ)?',  # 100,000đ
        ]
        
        mentioned_prices = []
        for pattern in price_patterns:
            matches = re.findall(pattern, output)
            for match in matches:
                # Convert to int
                price_str = match.replace(',', '')
                if 'k' in output[output.find(match):output.find(match)+10].lower():
                    price = int(price_str) * 1000
                else:
                    price = int(price_str)
                mentioned_prices.append(price)
        
        # Check if prices are reasonable given restaurant data
        price_levels = {r.get('price_level') for r in restaurants}
        
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': (20000, 100000),
            'PRICE_LEVEL_MODERATE': (80000, 300000),
            'PRICE_LEVEL_EXPENSIVE': (250000, 600000),
            'PRICE_LEVEL_VERY_EXPENSIVE': (500000, 2000000)
        }
        
        for price in mentioned_prices:
            # Check if price matches any restaurant's price level
            valid = False
            for level in price_levels:
                if level in price_map:
                    min_p, max_p = price_map[level]
                    if min_p <= price <= max_p:
                        valid = True
                        break
            
            if not valid and len(price_levels) > 0:
                warnings.append(f"Suspicious price mention: {price}đ may not match restaurant data")
        
        return warnings
    
    def _check_rating_hallucination(
        self,
        output: str,
        restaurants: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if LLM invents rating information."""
        warnings = []
        
        # Extract rating mentions (e.g., "4.5 sao", "rating 4/5")
        rating_patterns = [
            r'(\d\.\d)\s*(?:sao|/5|điểm)',
            r'rating\s*(\d\.\d)',
        ]
        
        mentioned_ratings = []
        for pattern in rating_patterns:
            matches = re.findall(pattern, output.lower())
            mentioned_ratings.extend([float(m) for m in matches])
        
        # Check if ratings match actual data
        actual_ratings = {r.get('rating', 0) for r in restaurants}
        
        for rating in mentioned_ratings:
            if rating not in actual_ratings and not any(abs(rating - ar) < 0.2 for ar in actual_ratings):
                warnings.append(f"Rating mismatch: {rating} not found in data (actual: {actual_ratings})")
        
        return warnings
    
    def _check_location_hallucination(
        self,
        output: str,
        restaurants: List[Dict[str, Any]]
    ) -> List[str]:
        """Check if LLM invents location information."""
        warnings = []
        
        # Extract district mentions (e.g., "Quận 1", "District 3")
        district_pattern = r'(?:quận|district|q\.?)\s*(\d{1,2})'
        mentioned_districts = re.findall(district_pattern, output.lower())
        
        # Extract actual districts from restaurant addresses
        actual_districts = set()
        for r in restaurants:
            address = r.get('address', '').lower()
            district_matches = re.findall(district_pattern, address)
            actual_districts.update(district_matches)
        
        for district in mentioned_districts:
            if district not in actual_districts:
                warnings.append(f"District mismatch: Quận {district} mentioned but not in actual data")
        
        return warnings
    
    def apply_corrections(
        self,
        output: str,
        warnings: List[str],
        actual_restaurants: List[Dict[str, Any]]
    ) -> str:
        """
        Apply corrections to output based on warnings.
        
        Args:
            output: Original LLM output
            warnings: List of detected issues
            actual_restaurants: Actual data
            
        Returns:
            Corrected output
        """
        corrected = output
        
        # If count hallucination detected, fix it
        count_warnings = [w for w in warnings if 'Count mismatch' in w]
        if count_warnings:
            actual_count = len(actual_restaurants)
            # Replace wrong counts with correct count
            corrected = re.sub(
                r'\d+\s*(?:quán|nhà hàng)',
                f'{actual_count} nhà hàng',
                corrected,
                count=1
            )
        
        return corrected


# Global instance
output_validator = OutputValidator()
