"""
Improved Ranking System with Multi-Factor Scoring
Fixes normalization bugs and implements better ranking logic.

BUG #8 FIX: Floating Point Precision
- Use Decimal for critical calculations
- Epsilon comparison for near-equal scores
- Stable sorting with tie-breaking
- Validated weight sums
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
from scipy.stats import zscore
from collections import defaultdict
import math
from decimal import Decimal, ROUND_HALF_UP
import logging

logger = logging.getLogger(__name__)


class ImprovedRanker:
    """
    BUG #8 FIX: Improved ranker with automatic weight normalization.
    
    Multi-factor restaurant ranking with:
    - Relevance (40%): Search query match
    - Quality (25%): Rating + review count (Bayesian average)
    - Personalization (20%): User preferences
    - Distance (10%): Proximity to user
    - Popularity (5%): Review count
    
    Improvements:
    - Property-based weights with automatic normalization
    - Decimal precision for exact weight sum = 1.0
    - Validation: no negative weights, no overflow
    - Unused weight redistribution when features disabled
    - Robust handling of edge cases (all weights zero)
    """
    
    # Diversity settings
    MAX_PER_CUISINE = 3
    DIVERSITY_START_RANK = 5
    
    # BUG #8 FIX: Precision settings
    EPSILON = 1e-9  # For floating point comparison
    DECIMAL_PLACES = 6  # For score rounding
    
    def __init__(self):
        """Initialize with default weights and validate sum."""
        # BUG #8 FIX: Use private attributes with property access
        self._relevance_weight = 0.40
        self._quality_weight = 0.25
        self._personalization_weight = 0.20
        self._distance_weight = 0.10
        self._popularity_weight = 0.05
        
        # Flag to prevent recursive normalization
        self._normalizing = False
        
        # BUG #8 FIX: Validate weights on initialization
        self._normalize_weights()
    
    # BUG #8 FIX: Property-based weight management with automatic normalization
    
    @property
    def RELEVANCE_WEIGHT(self) -> float:
        """Relevance weight (read-only access to private attribute)."""
        return self._relevance_weight
    
    @RELEVANCE_WEIGHT.setter
    def RELEVANCE_WEIGHT(self, value: float) -> None:
        """Set relevance weight with validation and auto-normalization."""
        self._set_weight('_relevance_weight', value)
    
    @property
    def QUALITY_WEIGHT(self) -> float:
        """Quality weight (read-only access to private attribute)."""
        return self._quality_weight
    
    @QUALITY_WEIGHT.setter
    def QUALITY_WEIGHT(self, value: float) -> None:
        """Set quality weight with validation and auto-normalization."""
        self._set_weight('_quality_weight', value)
    
    @property
    def PERSONALIZATION_WEIGHT(self) -> float:
        """Personalization weight (read-only access to private attribute)."""
        return self._personalization_weight
    
    @PERSONALIZATION_WEIGHT.setter
    def PERSONALIZATION_WEIGHT(self, value: float) -> None:
        """Set personalization weight with validation and auto-normalization."""
        self._set_weight('_personalization_weight', value)
    
    @property
    def DISTANCE_WEIGHT(self) -> float:
        """Distance weight (read-only access to private attribute)."""
        return self._distance_weight
    
    @DISTANCE_WEIGHT.setter
    def DISTANCE_WEIGHT(self, value: float) -> None:
        """Set distance weight with validation and auto-normalization."""
        self._set_weight('_distance_weight', value)
    
    @property
    def POPULARITY_WEIGHT(self) -> float:
        """Popularity weight (read-only access to private attribute)."""
        return self._popularity_weight
    
    @POPULARITY_WEIGHT.setter
    def POPULARITY_WEIGHT(self, value: float) -> None:
        """Set popularity weight with validation and auto-normalization."""
        self._set_weight('_popularity_weight', value)
    
    def _set_weight(self, attr_name: str, value: float) -> None:
        """
        BUG #8 FIX: Set weight with validation and automatic normalization.
        
        Args:
            attr_name: Private attribute name (e.g., '_relevance_weight')
            value: New weight value
            
        Raises:
            ValueError: If weight is negative or causes overflow
        """
        # Validate: no negative weights
        if value < 0:
            raise ValueError(f"Weight cannot be negative: {value}")
        
        # Validate: no extreme overflow (prevent computational issues)
        if value > 1e6:
            raise ValueError(f"Weight overflow: {value} exceeds maximum (1e6)")
        
        # Set the private attribute
        setattr(self, attr_name, value)
        
        # Auto-normalize (avoid recursion)
        if not self._normalizing:
            self._normalize_weights()
    
    def set_weights(self, relevance: float = None, quality: float = None, 
                   personalization: float = None, distance: float = None, 
                   popularity: float = None) -> None:
        """
        BUG #8 FIX: Batch set multiple weights with single normalization.
        
        More efficient than setting weights individually when changing multiple values.
        
        Args:
            relevance: Relevance weight (None = keep current)
            quality: Quality weight (None = keep current)
            personalization: Personalization weight (None = keep current)
            distance: Distance weight (None = keep current)
            popularity: Popularity weight (None = keep current)
        """
        # Disable auto-normalization during batch update
        self._normalizing = True
        
        try:
            if relevance is not None:
                self.RELEVANCE_WEIGHT = relevance
            if quality is not None:
                self.QUALITY_WEIGHT = quality
            if personalization is not None:
                self.PERSONALIZATION_WEIGHT = personalization
            if distance is not None:
                self.DISTANCE_WEIGHT = distance
            if popularity is not None:
                self.POPULARITY_WEIGHT = popularity
        finally:
            # Re-enable normalization and normalize once
            self._normalizing = False
            self._normalize_weights()
    
    def _normalize_weights(self) -> None:
        """
        BUG #8 FIX: Normalize weights to sum to exactly 1.0.
        
        Uses Decimal for precise calculation to avoid floating point errors.
        If all weights are zero, reset to defaults.
        """
        if self._normalizing:
            return  # Prevent recursion
        
        self._normalizing = True
        
        try:
            # Convert to Decimal for precise calculation
            weights = {
                '_relevance_weight': Decimal(str(self._relevance_weight)),
                '_quality_weight': Decimal(str(self._quality_weight)),
                '_personalization_weight': Decimal(str(self._personalization_weight)),
                '_distance_weight': Decimal(str(self._distance_weight)),
                '_popularity_weight': Decimal(str(self._popularity_weight))
            }
            
            weight_sum = sum(weights.values())
            
            # If all weights are zero, reset to defaults
            if weight_sum == 0:
                self._relevance_weight = 0.40
                self._quality_weight = 0.25
                self._personalization_weight = 0.20
                self._distance_weight = 0.10
                self._popularity_weight = 0.05
                
                logger.error(
                    "❌ BUG #8 FIX: All weights were zero, reset to defaults"
                )
                return
            
            # Check if normalization needed (within epsilon tolerance)
            if abs(float(weight_sum) - 1.0) > Decimal(str(self.EPSILON)):
                logger.warning(
                    f"⚠️ BUG #8 FIX: Weights sum to {weight_sum:.10f}, normalizing to 1.0"
                )
                
                # Normalize proportionally
                for attr_name, weight_value in weights.items():
                    normalized_value = weight_value / weight_sum
                    # Convert back to float with controlled precision
                    setattr(self, attr_name, float(normalized_value))
        finally:
            self._normalizing = False
    
    def disable_feature(self, feature: str) -> None:
        """
        BUG #8 FIX: Disable a feature and redistribute its weight to others.
        
        When a feature is unavailable (e.g., no user location for distance,
        no user history for personalization), redistribute its weight
        proportionally to the remaining features.
        
        Args:
            feature: Feature to disable ('personalization', 'distance', etc.)
        """
        feature_map = {
            'personalization': '_personalization_weight',
            'distance': '_distance_weight',
            'popularity': '_popularity_weight',
            'quality': '_quality_weight',
            'relevance': '_relevance_weight'
        }
        
        if feature not in feature_map:
            raise ValueError(f"Unknown feature: {feature}")
        
        attr_name = feature_map[feature]
        
        # Get current weight before zeroing
        current_weight = getattr(self, attr_name)
        
        if current_weight == 0:
            return  # Already disabled
        
        # Zero out the weight
        self._normalizing = True
        setattr(self, attr_name, 0.0)
        self._normalizing = False
        
        # Normalize will redistribute proportionally
        self._normalize_weights()
        
        logger.info(
            f"🔧 BUG #8 FIX: Disabled '{feature}' feature, "
            f"redistributed {current_weight:.3f} weight to remaining features"
        )
    
    def rank_restaurants(
        self,
        restaurants: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None,
        personalization_scores: Optional[Dict[int, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank restaurants with multi-factor scoring.
        
        Args:
            restaurants: List of restaurant dictionaries
            context: Query context (user_location, budget, query, etc.)
            personalization_scores: Optional pre-computed personalization scores
            
        Returns:
            Ranked list of restaurants with scoring details
        """
        if not restaurants:
            return []
        
        context = context or {}
        
        # BUG #5 FIX: Validate and normalize weights before ranking
        self._normalize_weights()
        
        # Step 1: Calculate individual factor scores
        relevance_scores = self._extract_relevance_scores(restaurants)
        quality_scores = self._calculate_quality_scores(restaurants)
        distance_scores = self._calculate_distance_scores(restaurants, context)
        popularity_scores = self._calculate_popularity_scores(restaurants)
        personalization_scores_dict = personalization_scores or self._default_personalization(restaurants)
        
        # Step 2: Normalize all scores to [0, 1] with outlier handling
        relevance_scores = self._robust_normalize(relevance_scores)
        quality_scores = self._robust_normalize(quality_scores)
        distance_scores = self._robust_normalize(distance_scores)
        popularity_scores = self._robust_normalize(popularity_scores)
        # Convert personalization dict to list for normalization
        personalization_list = [personalization_scores_dict.get(r['id'], 0.5) for r in restaurants]
        personalization_list = self._robust_normalize(personalization_list)
        
        # Step 3: Calculate weighted composite scores with Decimal precision
        # BUG #8 FIX: Use Decimal for precise calculation, avoid floating point errors
        composite_scores = {}
        for i, restaurant in enumerate(restaurants):
            restaurant_id = restaurant['id']
            
            # Convert to Decimal for precise calculation
            rel_dec = Decimal(str(relevance_scores[i]))
            qual_dec = Decimal(str(quality_scores[i]))
            dist_dec = Decimal(str(distance_scores[i]))
            pop_dec = Decimal(str(popularity_scores[i]))
            pers_dec = Decimal(str(personalization_list[i]))
            
            composite_score_decimal = (
                rel_dec * Decimal(str(self.RELEVANCE_WEIGHT)) +
                qual_dec * Decimal(str(self.QUALITY_WEIGHT)) +
                dist_dec * Decimal(str(self.DISTANCE_WEIGHT)) +
                pop_dec * Decimal(str(self.POPULARITY_WEIGHT)) +
                pers_dec * Decimal(str(self.PERSONALIZATION_WEIGHT))
            )
            
            # Round to fixed precision to avoid float jitter
            composite_score_decimal = composite_score_decimal.quantize(
                Decimal(10) ** -self.DECIMAL_PLACES,
                rounding=ROUND_HALF_UP
            )
            
            # Convert back to float for storage
            composite_score = float(composite_score_decimal)
            composite_scores[restaurant_id] = composite_score
            
            # Add scoring breakdown for transparency
            restaurant['score_breakdown'] = {
                'relevance': round(relevance_scores[i], 3),
                'quality': round(quality_scores[i], 3),
                'distance': round(distance_scores[i], 3),
                'popularity': round(popularity_scores[i], 3),
                'personalization': round(personalization_list[i], 3),
                'composite': round(composite_score, 6)  # Higher precision for composite
            }
        
        # Step 4: Stable sort by composite score with tie-breaking
        # BUG #8 FIX: Use stable sort with ID as tie-breaker for consistent ordering
        restaurants.sort(
            key=lambda x: (
                -composite_scores[x['id']],  # Primary: score (descending)
                x['id']  # Secondary: ID (ascending) for stability
            )
        )
        
        # Step 5: Apply diversity (after top results)
        restaurants = self._apply_diversity(restaurants)
        
        # Step 6: Add final rank
        for rank, restaurant in enumerate(restaurants, 1):
            restaurant['rank'] = rank
            restaurant['final_score'] = composite_scores[restaurant['id']]
        
        return restaurants
    
    def _scores_equal(self, score1: float, score2: float) -> bool:
        """
        BUG #8 FIX: Compare two scores accounting for floating point precision.
        
        Args:
            score1: First score
            score2: Second score
            
        Returns:
            True if scores are equal within epsilon
        """
        return abs(score1 - score2) < self.EPSILON
    
    def _round_score(self, score: float) -> float:
        """
        BUG #8 FIX: Round score to fixed precision to avoid floating point jitter.
        
        Args:
            score: Raw score
            
        Returns:
            Rounded score
        """
        # Convert to Decimal, round, convert back
        dec_score = Decimal(str(score))
        rounded = dec_score.quantize(
            Decimal(10) ** -self.DECIMAL_PLACES,
            rounding=ROUND_HALF_UP
        )
        return float(rounded)
    
    def _robust_normalize(self, scores: List[float]) -> List[float]:
        """
        FIXED Bug #23: Robust normalization preserving top performers.
        FIXED Bug #1: Division by zero when all scores are equal.
        
        Uses modified z-score with MAD for extreme outlier detection,
        but uses percentile-based normalization to preserve score gaps.
        
        Key improvements:
        1. Cap at ±5 MAD (less aggressive than ±3)
        2. Use 95th percentile as max (not absolute max)
        3. Preserve top performers' advantage
        4. BUG #1 FIX: Handle empty arrays, NaN values, and zero range
        
        Args:
            scores: Raw scores
            
        Returns:
            Normalized scores in [0, 1] range with preserved gaps
        """
        # BUG #1 FIX: Handle empty list explicitly
        if not scores:
            return []
        
        # BUG #1 FIX: Handle single element
        if len(scores) == 1:
            return [1.0]
        
        scores_array = np.array(scores)
        
        # BUG #1 FIX: Check for NaN or Infinity values
        if np.any(np.isnan(scores_array)) or np.any(np.isinf(scores_array)):
            # Replace NaN/Inf with median of valid values
            valid_scores = scores_array[~(np.isnan(scores_array) | np.isinf(scores_array))]
            if len(valid_scores) > 0:
                replacement_value = np.median(valid_scores)
            else:
                replacement_value = 0.5
            scores_array = np.where(np.isnan(scores_array) | np.isinf(scores_array), 
                                   replacement_value, 
                                   scores_array)
        
        # FIXED: Remove ONLY extreme outliers (beyond 5 MAD, not 3)
        # This allows genuinely exceptional restaurants to stand out
        median = np.median(scores_array)
        mad = np.median(np.abs(scores_array - median))
        
        # BUG #1 FIX: Check if MAD is valid before division
        if mad > 1e-10:  # Use small threshold instead of 0
            modified_z_scores = 0.6745 * (scores_array - median) / mad
            # FIXED: Cap at ±5 MAD (less aggressive)
            scores_array = np.where(modified_z_scores > 5, 
                                   median + 5 * mad / 0.6745, 
                                   scores_array)
            scores_array = np.where(modified_z_scores < -5, 
                                   median - 5 * mad / 0.6745, 
                                   scores_array)
        
        # FIXED: Percentile-based normalization (not min-max)
        # Use 5th and 95th percentile to avoid single outlier compression
        min_score = np.percentile(scores_array, 5)
        max_score = np.percentile(scores_array, 95)
        
        # If range still too small, fall back to min-max
        if max_score - min_score < 0.01:
            min_score = scores_array.min()
            max_score = scores_array.max()
        
        # BUG #1 FIX: Check edge case - all restaurants at same score
        # This prevents division by zero
        if abs(max_score - min_score) < 1e-10:
            # All scores are equal (or very close)
            # Return equal normalized scores
            return [1.0] * len(scores)
        
        # Normalize with clipping to [0, 1] range
        normalized = (scores_array - min_score) / (max_score - min_score)
        normalized = np.clip(normalized, 0.0, 1.0)
        
        return normalized.tolist()
    
    def _extract_relevance_scores(self, restaurants: List[Dict[str, Any]]) -> List[float]:
        """Extract relevance scores from restaurants.
        
        BUG #3 FIX: Handle empty restaurant list explicitly.
        """
        # BUG #3 FIX: Handle empty list
        if not restaurants:
            return []
        
        scores = []
        for restaurant in restaurants:
            # Try multiple score fields
            score = (restaurant.get('relevance_score') or 
                    restaurant.get('score') or 
                    restaurant.get('similarity') or 
                    0.5)
            scores.append(float(score))
        return scores
    
    def _calculate_quality_scores(self, restaurants: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate quality score based on rating and review count.
        
        Uses Bayesian average to handle restaurants with few reviews.
        
        BUG #13 FIX: Add comprehensive validation to prevent:
        - Integer overflow (rating > 5)
        - Negative ratings
        - NaN/Infinity values
        - Type errors (string, list, dict)
        - Division by zero
        
        BUG #3 FIX: Handle empty restaurant list explicitly.
        """
        # BUG #3 FIX: Handle empty list
        if not restaurants:
            return []
        
        scores = []
        
        # BUG #13 FIX: Validate and sanitize all ratings before calculating global average
        valid_ratings = []
        for r in restaurants:
            raw_rating = r.get('rating')
            if raw_rating is not None:
                try:
                    # Convert to float and validate
                    rating_val = float(raw_rating)
                    
                    # Check for NaN/Infinity
                    if not (math.isnan(rating_val) or math.isinf(rating_val)):
                        # Clamp to valid range [0, 5]
                        rating_val = max(0.0, min(5.0, rating_val))
                        valid_ratings.append(rating_val)
                except (TypeError, ValueError):
                    # Skip invalid types (string, list, dict, etc.)
                    pass
        
        # Calculate global average rating from valid ratings only
        global_avg_rating = np.mean(valid_ratings) if valid_ratings else 4.0
        
        # Minimum reviews for full confidence
        confidence_threshold = 50
        
        for restaurant in restaurants:
            # BUG #13 FIX: Comprehensive validation of rating
            raw_rating = restaurant.get('rating')
            rating = global_avg_rating  # Default
            
            if raw_rating is not None:
                try:
                    rating = float(raw_rating)
                    
                    # Check for NaN/Infinity
                    if math.isnan(rating) or math.isinf(rating):
                        rating = global_avg_rating
                    else:
                        # Clamp to valid range [0, 5]
                        rating = max(0.0, min(5.0, rating))
                except (TypeError, ValueError):
                    # Invalid type (string, list, dict) - use default
                    rating = global_avg_rating
            
            # BUG #13 FIX: Validate rating_count
            raw_rating_count = restaurant.get('rating_count', 0)
            rating_count = 0  # Default
            
            try:
                rating_count = int(raw_rating_count)
                
                # Prevent negative counts
                if rating_count < 0:
                    rating_count = 0
                
                # Prevent extreme values that could cause overflow
                # Cap at 1 million reviews (reasonable maximum)
                if rating_count > 1000000:
                    rating_count = 1000000
            except (TypeError, ValueError):
                # Invalid type - use default 0
                rating_count = 0
            
            # Bayesian average: weighted between restaurant rating and global average
            # More reviews = more weight to restaurant's actual rating
            confidence = min(1.0, rating_count / confidence_threshold)
            bayesian_rating = (
                confidence * rating + 
                (1 - confidence) * global_avg_rating
            )
            
            # Normalize to 0-1 (assuming 5-star scale)
            quality_score = bayesian_rating / 5.0
            
            scores.append(quality_score)
        
        return scores
    
    def _calculate_distance_scores(
        self,
        restaurants: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[float]:
        """
        Calculate distance score (closer = better).
        
        Uses exponential decay for distance penalty.
        
        BUG #1 FIX: Division by Zero in Distance Normalization
        - Handle empty restaurant list
        - Handle all restaurants with None distance
        - Handle all restaurants at same distance
        - Handle invalid distance values (negative, NaN, Infinity)
        """
        # BUG #1 FIX: Handle empty list
        if not restaurants:
            return []
        
        user_location = context.get('user_location')
        
        if not user_location:
            # No location provided, neutral score
            return [0.5] * len(restaurants)
        
        scores = []
        valid_distances = []  # Track valid distances for edge case detection
        distance_validity = []  # Track which restaurants have valid distances
        
        for restaurant in restaurants:
            distance = restaurant.get('distance')
            
            # BUG #1 FIX: Validate distance value
            if distance is None:
                scores.append(0.5)
                distance_validity.append(False)
                continue
            
            # Check for invalid distance values
            try:
                distance = float(distance)
                
                # Check for NaN or Infinity
                if math.isnan(distance) or math.isinf(distance):
                    scores.append(0.5)
                    distance_validity.append(False)
                    continue
                
                # Check for negative distance (invalid)
                if distance < 0:
                    scores.append(0.5)
                    distance_validity.append(False)
                    continue
                    
            except (TypeError, ValueError):
                scores.append(0.5)
                distance_validity.append(False)
                continue
            
            # Exponential decay: 
            # - 0-1km: ~1.0
            # - 2km: ~0.8
            # - 5km: ~0.5
            # - 10km: ~0.25
            # - 20km+: ~0.1
            
            decay_factor = 0.3  # Controls how quickly score decreases
            distance_score = math.exp(-decay_factor * distance)
            
            scores.append(distance_score)
            valid_distances.append(distance)
            distance_validity.append(True)
        
        # BUG #1 FIX: Check if all restaurants at same distance
        # This prevents issues in normalization later
        if valid_distances:
            min_dist = min(valid_distances)
            max_dist = max(valid_distances)
            
            # All restaurants equidistant (or very close)
            if abs(max_dist - min_dist) < 1e-6:
                # Return equal scores: 1.0 for valid distances, 0.5 for invalid
                return [1.0 if valid else 0.5 for valid in distance_validity]
        
        return scores
    
    def _calculate_popularity_scores(self, restaurants: List[Dict[str, Any]]) -> List[float]:
        """
        Calculate popularity score based on review count and rating.
        
        Popular restaurants get a small boost.
        
        BUG #3 FIX: Handle empty restaurant list explicitly.
        """
        # BUG #3 FIX: Handle empty list
        if not restaurants:
            return []
        
        scores = []
        
        # Get max review count for normalization
        max_reviews = max(
            (r.get('rating_count', 0) for r in restaurants),
            default=1
        )
        
        for restaurant in restaurants:
            rating_count = restaurant.get('rating_count', 0)
            
            # Popularity score: log scale to avoid overwhelming other factors
            if rating_count > 0:
                popularity = math.log10(rating_count + 1) / math.log10(max_reviews + 1)
            else:
                popularity = 0.0
            
            scores.append(popularity)
        
        return scores
    
    def _default_personalization(self, restaurants: List[Dict[str, Any]]) -> Dict[int, float]:
        """Default personalization (neutral) when not available."""
        return {r['id']: 0.5 for r in restaurants}
    
    def _apply_diversity(self, restaurants: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply diversity to prevent cuisine clustering.
        
        Ensures variety in results by limiting same-cuisine restaurants
        in top positions.
        """
        if len(restaurants) <= self.DIVERSITY_START_RANK:
            return restaurants
        
        # Keep top results as-is
        top_results = restaurants[:self.DIVERSITY_START_RANK]
        remaining = restaurants[self.DIVERSITY_START_RANK:]
        
        # Track cuisine counts in top results
        cuisine_counts = defaultdict(int)
        for restaurant in top_results:
            cuisines = self._extract_cuisines(restaurant)
            for cuisine in cuisines:
                cuisine_counts[cuisine] += 1
        
        # FIXED: Use weighted sampling instead of greedy selection for better diversity
        diversified = []
        used_indices = set()
        
        # Create a pool of candidates
        candidates = list(enumerate(remaining))
        
        while candidates and len(diversified) < len(remaining):
            # Calculate weights for each candidate
            weights = []
            valid_candidates = []
            
            for i, restaurant in candidates:
                if i in used_indices:
                    continue
                
                cuisines = self._extract_cuisines(restaurant)
                
                # Calculate diversity score (lower cuisine count = higher weight)
                diversity_score = 1.0
                for cuisine in cuisines:
                    count = cuisine_counts[cuisine]
                    # Exponential penalty for over-represented cuisines
                    if count >= self.MAX_PER_CUISINE:
                        diversity_score *= 0.1  # Heavy penalty
                    else:
                        diversity_score *= (1.0 / (count + 1))
                
                # Combine with original score (from composite ranking)
                original_score = restaurant.get('final_score', restaurant.get('score_breakdown', {}).get('composite', 0.5))
                
                # Weighted score: 70% original quality + 30% diversity
                combined_weight = 0.7 * original_score + 0.3 * diversity_score
                
                weights.append(combined_weight)
                valid_candidates.append((i, restaurant))
            
            if not valid_candidates:
                break
            
            # Select candidate with highest weight (deterministic, not random)
            best_idx = np.argmax(weights)
            selected_i, selected_restaurant = valid_candidates[best_idx]
            
            diversified.append(selected_restaurant)
            used_indices.add(selected_i)
            
            # Update cuisine counts
            for cuisine in self._extract_cuisines(selected_restaurant):
                cuisine_counts[cuisine] += 1
            
            # Remove selected from candidates
            candidates = [(i, r) for i, r in candidates if i != selected_i]
        
        # Add any remaining (shouldn't happen, but safety)
        for i, restaurant in enumerate(remaining):
            if i not in used_indices:
                diversified.append(restaurant)
        
        return top_results + diversified
    
    def _extract_cuisines(self, restaurant: Dict[str, Any]) -> List[str]:
        """Extract cuisine types from restaurant."""
        cuisines = []
        
        # From food_tags
        food_tags = restaurant.get('food_tags', [])
        if isinstance(food_tags, str):
            import json
            try:
                food_tags = json.loads(food_tags)
            except:
                food_tags = [food_tags] if food_tags else []
        
        if isinstance(food_tags, list):
            cuisines.extend([c.lower().strip() for c in food_tags if c])
        
        # From category
        category = restaurant.get('category', '')
        if category:
            cuisines.append(category.lower().strip())
        
        return list(set(cuisines))  # Unique cuisines


# Global instance
improved_ranker = ImprovedRanker()
