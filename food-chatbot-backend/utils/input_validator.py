"""
Input Validation Layer - SQL Injection Protection
Validates and sanitizes all user inputs before processing.
"""
import re
from typing import Any, Dict, Optional


class InputValidator:
    """Validate and sanitize user inputs to prevent injection attacks."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\bor\b|\band\b).*=.*",  # OR/AND conditions
        r"union\s+select",          # UNION SELECT
        r"drop\s+table",            # DROP TABLE
        r"delete\s+from",           # DELETE FROM
        r"insert\s+into",           # INSERT INTO
        r"update\s+.*\s+set",       # UPDATE SET
        r"exec\s*\(",               # EXEC(
        r"execute\s*\(",            # EXECUTE(
        r"--",                      # SQL comments
        r"/\*.*\*/",                # Block comments
        r"xp_cmdshell",             # SQL Server command
        r";\s*drop",                # Command chaining
        r"'\s*or\s*'1'\s*=\s*'1",  # Classic injection
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"onerror\s*=",
        r"onload\s*=",
        r"onclick\s*=",
    ]
    
    @staticmethod
    def validate_query(query: str, max_length: int = 500) -> Dict[str, Any]:
        """
        Validate user query for safety.
        
        Args:
            query: User input query
            max_length: Maximum allowed length
            
        Returns:
            {
                "is_valid": bool,
                "sanitized": str,
                "warnings": List[str]
            }
        """
        warnings = []
        
        # Check length
        if len(query) > max_length:
            warnings.append(f"Query too long (max {max_length} chars)")
            query = query[:max_length]
        
        # Check for SQL injection attempts
        query_lower = query.lower()
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                warnings.append(f"Potential SQL injection detected: {pattern}")
                # Don't reject, just log
        
        # Check for XSS attempts
        for pattern in InputValidator.XSS_PATTERNS:
            if re.search(pattern, query, re.IGNORECASE):
                warnings.append(f"Potential XSS detected: {pattern}")
                # Sanitize by removing
                query = re.sub(pattern, "", query, flags=re.IGNORECASE)
        
        # Remove null bytes
        query = query.replace('\x00', '')
        
        # Normalize whitespace
        query = ' '.join(query.split())
        
        return {
            "is_valid": len(warnings) == 0 or all('Potential' not in w for w in warnings),
            "sanitized": query.strip(),
            "warnings": warnings
        }
    
    @staticmethod
    def validate_session_id(session_id: str) -> bool:
        """
        Validate session ID format.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if valid
        """
        # Session ID should be alphanumeric with hyphens only
        if not session_id or len(session_id) > 100:
            return False
        
        return bool(re.match(r'^[a-zA-Z0-9\-_]+$', session_id))
    
    @staticmethod
    def validate_user_id(user_id: str) -> bool:
        """
        Validate user ID format.
        
        Args:
            user_id: User identifier
            
        Returns:
            True if valid
        """
        if not user_id or len(user_id) > 100:
            return False
        
        return bool(re.match(r'^[a-zA-Z0-9\-_@.]+$', user_id))
    
    @staticmethod
    def validate_coordinates(lat: Optional[float], lon: Optional[float]) -> bool:
        """
        Validate geographic coordinates.
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            True if valid
        """
        if lat is None or lon is None:
            return False
        
        # Vietnam bounds: lat 8-24, lon 102-110
        if not (8.0 <= lat <= 24.0):
            return False
        if not (102.0 <= lon <= 110.0):
            return False
        
        return True
    
    @staticmethod
    def sanitize_restaurant_name(name: str) -> str:
        """
        Sanitize restaurant name for display.
        
        Args:
            name: Restaurant name
            
        Returns:
            Sanitized name
        """
        # Remove HTML tags
        name = re.sub(r'<[^>]+>', '', name)
        
        # Remove control characters
        name = ''.join(char for char in name if ord(char) >= 32 or char == '\n')
        
        # Normalize whitespace
        name = ' '.join(name.split())
        
        return name.strip()


# Global validator instance
input_validator = InputValidator()
