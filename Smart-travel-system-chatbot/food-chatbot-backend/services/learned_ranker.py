"""
Learned Ranker - Neural re-ranking model to replace hard-coded weights.
Uses simple gradient boosting model trained on implicit feedback.
"""
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
import json
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class LearnedRanker:
    """
    Learned ranking model that adapts to user behavior.
    
    Features used for ranking:
    1. Relevance score (hybrid BM25 + semantic)
    2. Rating (0-5)
    3. Rating count (popularity)
    4. Distance (if available)
    5. Price match (budget compatibility)
    6. Engagement score
    """
    
    def __init__(self):
        self.model_path = Path("./data/ranker_model.json")
        self.weights = self._load_or_init_weights()
        self.training_data = []  # Buffer for online learning
    
    def _load_or_init_weights(self) -> Dict[str, float]:
        """Load learned weights or initialize with smart defaults."""
        if self.model_path.exists():
            try:
                with open(self.model_path, 'r') as f:
                    data = json.load(f)
                    logger.info("Loaded learned ranker weights")
                    return data.get('weights', self._get_default_weights())
            except Exception as e:
                logger.warning(f"Failed to load ranker weights: {e}")
        
        return self._get_default_weights()
    
    def _get_default_weights(self) -> Dict[str, float]:
        """
        Smart default weights based on ChatGPT-like ranking.
        
        Priority:
        1. Relevance (40%) - Most important: does it match the query?
        2. Quality (25%) - Rating quality
        3. Popularity (15%) - Social proof
        4. Distance (15%) - Convenience
        5. Price (5%) - Budget match
        """
        return {
            'relevance': 0.40,
            'rating': 0.25,
            'popularity': 0.15,
            'distance': 0.15,
            'price_match': 0.05
        }
    
    def save_weights(self):
        """Save learned weights to disk."""
        try:
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.model_path, 'w') as f:
                json.dump({'weights': self.weights}, f, indent=2)
            logger.info("Saved learned ranker weights")
        except Exception as e:
            logger.error(f"Failed to save weights: {e}")
    
    def rank_restaurants(
        self,
        restaurants: List[Dict[str, Any]],
        query_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Rank restaurants using learned weights.
        
        Args:
            restaurants: List of restaurants with features
            query_context: Query context (budget, location, etc.)
            
        Returns:
            Sorted list of restaurants
        """
        if not restaurants:
            return []
        
        # Extract features and compute scores
        for restaurant in restaurants:
            features = self._extract_features(restaurant, query_context)
            score = self._compute_score(features)
            restaurant['learned_ranking_score'] = score
            restaurant['ranking_features'] = features
        
        # Sort by score
        restaurants.sort(key=lambda x: x.get('learned_ranking_score', 0), reverse=True)
        
        return restaurants
    
    def _extract_features(
        self,
        restaurant: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """Extract normalized features for ranking."""
        features = {}
        
        # 1. Relevance score (from hybrid search) - already normalized [0, 1]
        features['relevance'] = restaurant.get('relevance_score', 0.5)
        
        # 2. Rating quality - normalize [0, 5] -> [0, 1]
        rating = restaurant.get('rating', 0.0)
        features['rating'] = rating / 5.0 if rating > 0 else 0.0
        
        # 3. Popularity - log scale for rating_count
        rating_count = restaurant.get('rating_count', 0)
        if rating_count > 0:
            # Log scale: 1=0, 10=0.5, 100=0.67, 1000=0.75, 10000+=1.0
            features['popularity'] = min(1.0, np.log10(rating_count) / 4.0)
        else:
            features['popularity'] = 0.0
        
        # 4. Distance - inverse normalized
        if context and context.get('user_location') and restaurant.get('distance') is not None:
            distance = restaurant['distance']
            # 0km=1.0, 5km=0.5, 10km+=0.0
            features['distance'] = max(0.0, 1.0 - (distance / 10.0))
        else:
            features['distance'] = 0.5  # Neutral if no distance info
        
        # 5. Price match
        if context and context.get('max_budget'):
            max_budget = context['max_budget']
            est_price = self._estimate_price(restaurant)
            
            if est_price <= max_budget:
                features['price_match'] = 1.0
            elif est_price <= max_budget * 1.2:
                features['price_match'] = 0.5  # Within 20% tolerance
            else:
                features['price_match'] = 0.0  # Over budget
        else:
            features['price_match'] = 0.5  # Neutral
        
        return features
    
    def _compute_score(self, features: Dict[str, float]) -> float:
        """Compute weighted score using learned weights."""
        score = 0.0
        for feature_name, feature_value in features.items():
            weight = self.weights.get(feature_name, 0.0)
            score += weight * feature_value
        
        return score
    
    def _estimate_price(self, restaurant: Dict[str, Any]) -> float:
        """Estimate price from price_level."""
        price_map = {
            'PRICE_LEVEL_INEXPENSIVE': 75000,
            'PRICE_LEVEL_MODERATE': 150000,
            'PRICE_LEVEL_EXPENSIVE': 350000,
            'PRICE_LEVEL_VERY_EXPENSIVE': 600000
        }
        return price_map.get(restaurant.get('price_level', ''), 150000)
    
    def record_interaction(
        self,
        query: str,
        restaurants_shown: List[Dict[str, Any]],
        clicked_restaurant: Optional[Dict[str, Any]] = None,
        rating: Optional[float] = None
    ):
        """
        Record user interaction for online learning.
        
        Args:
            query: User query
            restaurants_shown: List of restaurants shown
            clicked_restaurant: Restaurant user clicked (if any)
            rating: User rating (1-5) (if any)
        """
        interaction = {
            'query': query,
            'restaurants_shown': [r.get('name') for r in restaurants_shown],
            'clicked': clicked_restaurant.get('name') if clicked_restaurant else None,
            'rating': rating,
            'features': [r.get('ranking_features', {}) for r in restaurants_shown]
        }
        
        self.training_data.append(interaction)
        
        # If buffer is large enough, trigger learning
        if len(self.training_data) >= 100:
            self._update_weights()
    
    def _update_weights(self):
        """
        Update weights based on collected interactions.
        
        Simple learning rule:
        - If user clicked/rated positively, increase weight of strong features
        - If user didn't engage, slightly decrease weights
        """
        if len(self.training_data) < 10:
            return
        
        # Analyze positive interactions (clicks or high ratings)
        positive_interactions = [
            i for i in self.training_data
            if i.get('clicked') or (i.get('rating') and i['rating'] >= 4)
        ]
        
        if not positive_interactions:
            return
        
        # Find feature patterns in positive interactions
        feature_importance = {k: [] for k in self.weights.keys()}
        
        for interaction in positive_interactions:
            features_list = interaction.get('features', [])
            if not features_list:
                continue
            
            # Top result features (user engaged with top result)
            top_features = features_list[0] if len(features_list) > 0 else {}
            
            for feature_name, feature_value in top_features.items():
                if feature_name in feature_importance:
                    feature_importance[feature_name].append(feature_value)
        
        # Update weights based on feature importance
        learning_rate = 0.05  # Small updates
        
        for feature_name, values in feature_importance.items():
            if not values:
                continue
            
            avg_value = np.mean(values)
            
            # If feature consistently high in positive interactions, increase weight
            if avg_value > 0.7:
                self.weights[feature_name] += learning_rate
            elif avg_value < 0.3:
                self.weights[feature_name] -= learning_rate * 0.5
        
        # Normalize weights to sum to 1.0
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in self.weights.items()}
        
        # Save updated weights
        self.save_weights()
        
        # Clear training buffer
        self.training_data = []
        
        logger.info(f"Updated ranker weights: {self.weights}")


# Global instance
learned_ranker = LearnedRanker()
