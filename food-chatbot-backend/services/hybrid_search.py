"""
Hybrid search combining FAISS semantic search and BM25 keyword search.
"""
from typing import List, Dict, Any, Tuple
import aiosqlite
import json
import logging
from config import settings
from database import db_manager
from services.vector_store import vector_store
from services.bm25_search import bm25_search
from utils import extract_price_range, extract_location, normalize_text

logger = logging.getLogger(__name__)


class HybridSearch:
    """Combines semantic and keyword search with ranking."""
    
    def __init__(self):
        self.semantic_weight = settings.SEMANTIC_WEIGHT
        self.bm25_weight = settings.BM25_WEIGHT
    
    async def search(
        self,
        query: str,
        top_k: int = None,
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results
            filters: Additional filters (price, location, etc.)
            
        Returns:
            List of ranked restaurants
        """
        if top_k is None:
            top_k = settings.MAX_RESULTS
        
        # Skip semantic search if weight is 0
        if self.semantic_weight > 0:
            semantic_results = vector_store.search(query, top_k=top_k * 3)
            semantic_scores = self._normalize_scores(semantic_results, reverse=True)
        else:
            semantic_scores = {}
        
        # Skip BM25 if weight is 0
        if self.bm25_weight > 0:
            bm25_results = bm25_search.search(query, top_k=top_k * 3)
            bm25_scores = self._normalize_scores(bm25_results, reverse=False)
        else:
            bm25_scores = {}
        
        # Combine scores
        combined_scores = {}
        
        for restaurant_id, score in semantic_scores.items():
            combined_scores[restaurant_id] = score * self.semantic_weight
        
        for restaurant_id, score in bm25_scores.items():
            if restaurant_id in combined_scores:
                combined_scores[restaurant_id] += score * self.bm25_weight
            else:
                combined_scores[restaurant_id] = score * self.bm25_weight
        
        # Sort by combined score
        sorted_ids = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
        
        # Get restaurant details
        restaurants = await self._get_restaurant_details(sorted_ids[:top_k * 2])
        
        # Apply filters
        if filters:
            restaurants = self._apply_filters(restaurants, filters)
        
        # Add scores and rank
        for restaurant in restaurants:
            restaurant['relevance_score'] = combined_scores.get(restaurant['id'], 0.0)
        
        # DISABLED: ranking can shuffle results incorrectly
        # Use hybrid search relevance_score ONLY
        # ranked_restaurants = self._rank_results(restaurants, filters)
        
        # Sort by relevance_score (hybrid BM25 + semantic)
        restaurants_sorted = sorted(restaurants, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        return restaurants_sorted[:top_k]
    
    def _normalize_scores(
        self,
        results: List[Tuple[int, float]],
        reverse: bool = False
    ) -> Dict[int, float]:
        """
        Normalize scores to [0, 1] range.
        
        Args:
            results: List of (id, score) tuples
            reverse: If True, lower scores are better (for distance)
            
        Returns:
            Dictionary of normalized scores
        """
        if not results:
            return {}
        
        scores = [score for _, score in results]
        min_score = min(scores)
        max_score = max(scores)
        
        if max_score == min_score:
            return {id: 1.0 for id, _ in results}
        
        normalized = {}
        for id, score in results:
            norm_score = (score - min_score) / (max_score - min_score)
            if reverse:
                norm_score = 1.0 - norm_score
            normalized[id] = norm_score
        
        return normalized
    
    async def _get_restaurant_details(self, restaurant_ids: List[int]) -> List[Dict[str, Any]]:
        """
        Get full restaurant details from database.
        
        Args:
            restaurant_ids: List of restaurant IDs
            
        Returns:
            List of restaurant dictionaries
        """
        if not restaurant_ids:
            return []
        
        placeholders = ','.join('?' * len(restaurant_ids))
        query = f"SELECT * FROM restaurants WHERE id IN ({placeholders})"
        
        async with db_manager.get_connection() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, restaurant_ids) as cursor:
                rows = await cursor.fetchall()
                restaurants = []
                
                for row in rows:
                    restaurant = dict(row)
                    # Parse JSON fields
                    if restaurant.get('food_tags'):
                        try:
                            restaurant['food_tags'] = json.loads(restaurant['food_tags'])
                        except:
                            restaurant['food_tags'] = []
                    if restaurant.get('comments'):
                        try:
                            restaurant['comments'] = json.loads(restaurant['comments'])
                        except:
                            restaurant['comments'] = []
                    
                    restaurants.append(restaurant)
                
                return restaurants
    
    def _apply_filters(
        self,
        restaurants: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Apply filters to restaurant list.
        
        Args:
            restaurants: List of restaurants
            filters: Filter criteria
            
        Returns:
            Filtered restaurant list
        """
        filtered = restaurants
        
        # Price level filter
        if filters.get('price_level'):
            price_level = filters['price_level']
            filtered = [r for r in filtered if r.get('price_level') == price_level]
        
        # Budget filter (Google Maps $ price level system)
        if filters.get('max_budget'):
            max_budget = filters['max_budget']
            # Map price levels to approximate per-person costs (Google Maps style)
            # $ (INEXPENSIVE) = under 100k per person
            # $$ (MODERATE) = 100-300k per person
            # $$$ (EXPENSIVE) = 300-500k per person
            # $$$$ (VERY_EXPENSIVE) = over 500k per person
            
            # STRICT BUDGET MATCHING - No hallucination!
            # If user says 5k, don't show 100k+ restaurants
            if max_budget < 50000:
                # Very low budget (< 50k) -> ONLY show $ (INEXPENSIVE) restaurants
                # If no results, better to say "no restaurants" than suggest 100k+ places
                filtered = [
                    r for r in filtered
                    if r.get('price_level') == 'PRICE_LEVEL_INEXPENSIVE'
                ]
            elif max_budget <= 100000:
                # Low budget (50-100k) -> show $ restaurants
                # Can stretch to show $$ if they have budget-friendly dishes
                filtered = [
                    r for r in filtered
                    if r.get('price_level') in ['PRICE_LEVEL_INEXPENSIVE', 'PRICE_LEVEL_MODERATE']
                ]
            elif max_budget <= 300000:
                # Medium budget (100-300k) -> show $ and $$ restaurants
                filtered = [
                    r for r in filtered
                    if r.get('price_level') in ['PRICE_LEVEL_INEXPENSIVE', 'PRICE_LEVEL_MODERATE']
                ]
            else:
                # High budget (> 300k) -> show restaurants up to budget with 20% flex
                price_map = {
                    'PRICE_LEVEL_INEXPENSIVE': 100000,
                    'PRICE_LEVEL_MODERATE': 200000,
                    'PRICE_LEVEL_EXPENSIVE': 400000,
                    'PRICE_LEVEL_VERY_EXPENSIVE': 800000
                }
                filtered = [
                    r for r in filtered
                    if price_map.get(r.get('price_level', ''), 0) <= max_budget * 1.2
                ]
        
        # Rating filter
        if filters.get('min_rating'):
            min_rating = filters['min_rating']
            filtered = [r for r in filtered if r.get('rating', 0) >= min_rating]
        
        # Location filter by district/area name
        if filters.get('locations'):
            requested_locations = filters['locations']
            # Normalize for matching
            from utils.text_processing import normalize_text
            
            location_filtered = []
            for restaurant in filtered:
                address = restaurant.get('address', '')
                location_summary = restaurant.get('location_summary', '')
                name = restaurant.get('name', '')
                
                # Combine all text for matching
                combined_text = f"{name} {address} {location_summary}".lower()
                
                # Check if any requested location is in the combined text
                match_found = False
                for loc in requested_locations:
                    loc_normalized = normalize_text(loc, remove_accents=True).lower()
                    combined_normalized = normalize_text(combined_text, remove_accents=True)
                    
                    if loc_normalized in combined_normalized:
                        match_found = True
                        restaurant['_location_match_score'] = 1.0  # Mark as exact match
                        break
                
                if match_found:
                    location_filtered.append(restaurant)
            
            # Apply filter if we have at least 5 results (more lenient threshold)
            min_results = max(5, int(len(filtered) * 0.2))  # 20% threshold instead of 40%
            if len(location_filtered) >= min_results:
                filtered = location_filtered
                # Sort by location match (exact matches first) then by original score
                filtered.sort(key=lambda x: x.get('_location_match_score', 0), reverse=True)
        
        # Location filter (if user location provided)
        if filters.get('user_location'):
            # Calculate distances
            user_lat, user_lon = filters['user_location']
            for restaurant in filtered:
                if restaurant.get('coordinates_lat') and restaurant.get('coordinates_lon'):
                    distance = self._calculate_distance(
                        user_lat, user_lon,
                        restaurant['coordinates_lat'],
                        restaurant['coordinates_lon']
                    )
                    restaurant['distance'] = distance
        
        return filtered
    
    def _calculate_distance(
        self,
        lat1: float, lon1: float,
        lat2: float, lon2: float
    ) -> float:
        """
        Calculate distance between two coordinates (simplified).
        
        Args:
            lat1, lon1: First coordinate
            lat2, lon2: Second coordinate
            
        Returns:
            Distance in kilometers
        """
        import math
        
        # Haversine formula
        R = 6371  # Earth radius in km
        
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return round(distance, 2)
    
    def _rank_results(
        self,
        restaurants: List[Dict[str, Any]],
        filters: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Final ranking based on multiple factors.
        
        Args:
            restaurants: List of restaurants with relevance scores
            filters: User preferences
            
        Returns:
            Ranked restaurant list
        """
        if not restaurants:
            return []
        
        # Calculate ranking score
        for restaurant in restaurants:
            score = 0.0
            
            # Base relevance (40%)
            score += restaurant.get('relevance_score', 0) * 0.4
            
            # Rating (30%)
            rating = restaurant.get('rating', 0)
            if rating:
                score += (rating / 5.0) * 0.3
            
            # Popularity (rating count) (15%)
            rating_count = restaurant.get('rating_count', 0)
            if rating_count:
                # Normalize rating count (log scale)
                import math
                popularity_score = min(1.0, math.log10(rating_count + 1) / 4)
                score += popularity_score * 0.15
            
            # Distance (15%) - if available
            if restaurant.get('distance') is not None:
                distance = restaurant['distance']
                # Closer is better, normalize to max 10km
                distance_score = max(0, 1.0 - (distance / 10.0))
                score += distance_score * 0.15
            else:
                # If no distance, give neutral score
                score += 0.075
            
            restaurant['ranking_score'] = score
        
        # Sort by ranking score
        ranked = sorted(restaurants, key=lambda x: x['ranking_score'], reverse=True)
        
        return ranked


# Global instance
hybrid_search = HybridSearch()
