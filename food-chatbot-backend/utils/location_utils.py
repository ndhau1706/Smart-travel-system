"""
BUG #12 FIX: Location parsing utilities
Safe parsing and validation for user location data.
"""
from typing import Optional, Tuple, Union, Dict, List
import math


def parse_location(location: Union[Dict, List, Tuple, None]) -> Optional[Tuple[float, float]]:
    """
    BUG #12 FIX: Safely parse location from various formats.
    
    Supports:
    - Dict with 'lat'/'lon' keys
    - Dict with 'lat'/'lng' keys  
    - List/Tuple with [lat, lon]
    - None (returns None)
    
    Returns:
        Tuple[float, float] or None if invalid
        
    Prevents:
    - KeyError from wrong dict keys
    - IndexError from short lists
    - TypeError from string/nested values
    - ValueError from NaN/Infinity
    """
    if location is None:
        return None
    
    try:
        # Case 1: Dictionary with lat/lon or lat/lng
        if isinstance(location, dict):
            # Try 'lon' first (our standard)
            if 'lat' in location and 'lon' in location:
                lat = location['lat']
                lon = location['lon']
            # Try 'lng' as alternative
            elif 'lat' in location and 'lng' in location:
                lat = location['lat']
                lon = location['lng']
            # Try 'latitude'/'longitude' as fallback
            elif 'latitude' in location and 'longitude' in location:
                lat = location['latitude']
                lon = location['longitude']
            else:
                # Missing required keys
                return None
                
        # Case 2: List or Tuple
        elif isinstance(location, (list, tuple)):
            # Must have exactly 2 elements
            if len(location) != 2:
                return None
            lat, lon = location[0], location[1]
            
        # Case 3: Invalid type (string, int, etc.)
        else:
            return None
        
        # Convert to float (may raise TypeError or ValueError)
        lat = float(lat)
        lon = float(lon)
        
        # Validate: No NaN, No Infinity
        if math.isnan(lat) or math.isnan(lon):
            return None
        if math.isinf(lat) or math.isinf(lon):
            return None
        
        # Validate: Valid coordinate ranges
        if lat < -90 or lat > 90:
            return None
        if lon < -180 or lon > 180:
            return None
        
        return (lat, lon)
        
    except (TypeError, ValueError, KeyError, IndexError):
        # Any parsing error → return None
        return None


def validate_location_format(location: Union[Dict, List, Tuple, None]) -> Tuple[bool, Optional[str]]:
    """
    BUG #12 FIX: Validate location format and return helpful error message.
    
    Returns:
        (is_valid, error_message)
    """
    if location is None:
        return (True, None)  # None is valid (optional)
    
    # Check type
    if not isinstance(location, (dict, list, tuple)):
        return (False, f"Location must be dict or list/tuple, got {type(location).__name__}")
    
    # Check dict
    if isinstance(location, dict):
        has_lat_lon = 'lat' in location and 'lon' in location
        has_lat_lng = 'lat' in location and 'lng' in location
        has_latitude_longitude = 'latitude' in location and 'longitude' in location
        
        if not (has_lat_lon or has_lat_lng or has_latitude_longitude):
            keys = list(location.keys())
            return (False, f"Location dict must have 'lat'/'lon' or 'lat'/'lng' keys, got: {keys}")
        
        # Check value types
        lat_key = 'lat' if 'lat' in location else 'latitude'
        lon_key = 'lon' if 'lon' in location else ('lng' if 'lng' in location else 'longitude')
        
        lat_val = location.get(lat_key)
        lon_val = location.get(lon_key)
        
        if not isinstance(lat_val, (int, float)):
            return (False, f"Latitude must be number, got {type(lat_val).__name__}")
        if not isinstance(lon_val, (int, float)):
            return (False, f"Longitude must be number, got {type(lon_val).__name__}")
    
    # Check list/tuple
    if isinstance(location, (list, tuple)):
        if len(location) != 2:
            return (False, f"Location list/tuple must have exactly 2 elements, got {len(location)}")
        
        if not isinstance(location[0], (int, float)):
            return (False, f"Latitude must be number, got {type(location[0]).__name__}")
        if not isinstance(location[1], (int, float)):
            return (False, f"Longitude must be number, got {type(location[1]).__name__}")
    
    # Try to parse
    result = parse_location(location)
    if result is None:
        return (False, "Invalid coordinates (NaN, Infinity, or out of range)")
    
    return (True, None)
