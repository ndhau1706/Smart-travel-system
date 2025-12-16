"""
BM25 keyword search service.
"""
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from config import settings
from services.data_preprocessor import data_preprocessor
from utils import tokenize_vietnamese, expand_synonyms


class BM25Search:
    """BM25-based keyword search."""
    
    def __init__(self):
        self.bm25 = None
        self.restaurant_ids = []
        self.corpus = []
        self.index_path = Path(settings.BM25_INDEX_PATH)
    
    async def build_index(self, force_rebuild: bool = False):
        """
        Build BM25 index from restaurant data.
        
        Args:
            force_rebuild: Force rebuild even if index exists
        """
        # Check if index already exists
        if not force_rebuild and self.index_exists():
            print("Loading existing BM25 index...")
            self.load_index()
            return
        
        print("Building new BM25 index...")
        
        # Load restaurant data
        restaurants = await data_preprocessor.load_from_database()
        
        if not restaurants:
            print("No restaurant data found. Please run data initialization first.")
            return
        
        # Create corpus
        self.corpus = []
        self.restaurant_ids = []
        
        for restaurant in restaurants:
            searchable_text = data_preprocessor.create_searchable_text(restaurant)
            tokens = tokenize_vietnamese(searchable_text)
            self.corpus.append(tokens)
            self.restaurant_ids.append(restaurant['id'])
        
        # Create BM25 index
        print(f"Creating BM25 index for {len(self.corpus)} restaurants...")
        self.bm25 = BM25Okapi(self.corpus)
        
        # Save index
        self.save_index()
        print("BM25 index built successfully")
    
    def save_index(self):
        """Save BM25 index to disk."""
        self.index_path.parent.mkdir(parents=True, exist_ok=True)
        
        data = {
            'bm25': self.bm25,
            'restaurant_ids': self.restaurant_ids,
            'corpus': self.corpus
        }
        
        with open(self.index_path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"BM25 index saved to {self.index_path}")
    
    def load_index(self):
        """Load BM25 index from disk."""
        if not self.index_path.exists():
            raise FileNotFoundError(f"BM25 index not found: {self.index_path}")
        
        with open(self.index_path, 'rb') as f:
            data = pickle.load(f)
        
        self.bm25 = data['bm25']
        self.restaurant_ids = data['restaurant_ids']
        self.corpus = data['corpus']
        
        print(f"BM25 index loaded with {len(self.restaurant_ids)} documents")
    
    def index_exists(self) -> bool:
        """Check if index file exists."""
        return self.index_path.exists()
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for restaurants using BM25.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (restaurant_id, score) tuples
        """
        if self.bm25 is None:
            raise RuntimeError("BM25 index not loaded. Please build or load index first.")
        
        # Expand query with synonyms (coffee → cà phê, bun → bún)
        query_variants = expand_synonyms(query)
        
        # Combine scores from all variants
        combined_scores = {}
        for variant in query_variants:
            query_tokens = tokenize_vietnamese(variant)
            variant_scores = self.bm25.get_scores(query_tokens)
            
            # Merge scores (take max for each restaurant)
            for idx, score in enumerate(variant_scores):
                if idx not in combined_scores or score > combined_scores[idx]:
                    combined_scores[idx] = score
        
        # Convert to array
        import numpy as np
        scores = np.zeros(len(self.restaurant_ids))
        for idx, score in combined_scores.items():
            scores[idx] = score
        
        # Get top-k results
        top_indices = scores.argsort()[-top_k:][::-1]
        
        results = []
        for idx in top_indices:
            if idx < len(self.restaurant_ids):
                restaurant_id = self.restaurant_ids[idx]
                score = float(scores[idx])
                if score > 0:  # Only include results with positive scores
                    results.append((restaurant_id, score))
        
        return results


# Global instance
bm25_search = BM25Search()
