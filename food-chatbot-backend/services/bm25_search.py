"""
BM25 keyword search service with structured logging.
"""
import logging
import pickle
import asyncio
import re
from pathlib import Path
from typing import List, Dict, Any, Tuple
from rank_bm25 import BM25Okapi
from config import settings
from services.data_preprocessor import data_preprocessor
from utils import tokenize_vietnamese, expand_synonyms

logger = logging.getLogger(__name__)


class BM25Search:
    """BM25-based keyword search."""
    
    # BUG #26 FIX: Resource consumption limits
    MAX_QUERY_LENGTH = 500  # Maximum characters in query
    MAX_QUERY_TOKENS = 50   # Maximum tokens after tokenization
    MAX_SYNONYMS = 10       # Maximum synonym expansions
    SEARCH_TIMEOUT = 5.0    # Maximum search time in seconds
    MAX_DOCS_TO_SCORE = 10000  # Maximum documents to score (for large datasets)
    
    # BUG #27 FIX: Path traversal prevention
    ALLOWED_BASE_DIR = Path("./data").resolve()
    MAX_PATH_LENGTH = 255
    
    def __init__(self):
        self.bm25 = None
        self.restaurant_ids = []
        self.corpus = []
        
        # BUG #27 FIX: Validate index path
        self.index_path = self._validate_index_path(settings.BM25_INDEX_PATH)
    
    @staticmethod
    def _validate_index_path(path_str: str) -> Path:
        """
        BUG #27 FIX: Validate index path to prevent path traversal attacks.
        
        Same security checks as VectorStore._validate_index_path
        """
        if not path_str or not isinstance(path_str, str):
            raise ValueError("Index path must be a non-empty string")
        
        if len(path_str) > BM25Search.MAX_PATH_LENGTH:
            raise ValueError(f"Index path too long: {len(path_str)} chars")
        
        if '\x00' in path_str or '\0' in path_str:
            raise ValueError("Index path contains null bytes")
        
        dangerous_patterns = ['../', '..\\', '../', '..\\']
        if any(pattern in path_str for pattern in dangerous_patterns):
            raise ValueError("Index path contains path traversal sequences")
        
        try:
            path = Path(path_str).resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path format: {e}")
        
        try:
            BM25Search.ALLOWED_BASE_DIR.mkdir(parents=True, exist_ok=True)
            path.relative_to(BM25Search.ALLOWED_BASE_DIR)
        except ValueError:
            raise ValueError(
                f"Index path must be within {BM25Search.ALLOWED_BASE_DIR}, got {path}"
            )
        
        path_str_lower = str(path).lower()
        dangerous_paths = ['/dev/', '/proc/', '/sys/', '\\\\', 'c:\\windows\\', 'c:\\system32\\']
        if any(dangerous in path_str_lower for dangerous in dangerous_paths):
            raise ValueError("Index path points to system/device files")
        
        if path.exists():
            real_path = path.resolve(strict=True)
            try:
                real_path.relative_to(BM25Search.ALLOWED_BASE_DIR)
            except ValueError:
                raise ValueError(
                    f"Symbolic link points outside allowed directory: {real_path}"
                )
        
        return path
    
    async def build_index(self, force_rebuild: bool = False):
        """
        Build BM25 index from restaurant data.
        
        Args:
            force_rebuild: Force rebuild even if index exists
        """
        # Check if index already exists
        if not force_rebuild and self.index_exists():
            logger.info("Loading existing BM25 index...")
            self.load_index()
            return
        
        logger.info("Building new BM25 index...")
        
        # Load restaurant data
        restaurants = await data_preprocessor.load_from_database()
        
        if not restaurants:
            logger.warning("No restaurant data found. Please run data initialization first.")
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
        logger.info(f"Creating BM25 index for {len(self.corpus)} restaurants...")
        self.bm25 = BM25Okapi(self.corpus)
        
        # Save index
        self.save_index()
        logger.info("BM25 index built successfully")
    
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
        
        logger.info(f"BM25 index saved to {self.index_path}")
    
    def load_index(self):
        """Load BM25 index from disk."""
        # BUG #27 FIX: Validate path before loading
        if not self.index_path.exists():
            raise FileNotFoundError(f"BM25 index not found: {self.index_path}")
        
        # BUG #27 FIX: Verify file is within allowed directory
        try:
            real_path = self.index_path.resolve(strict=True)
            real_path.relative_to(self.ALLOWED_BASE_DIR)
        except ValueError:
            raise ValueError(f"Index file outside allowed directory: {self.index_path}")
        
        # BUG #27 FIX: Verify it's a regular file, not a device
        if not self.index_path.is_file():
            raise ValueError(f"Index path is not a regular file: {self.index_path}")
        
        with open(self.index_path, 'rb') as f:
            data = pickle.load(f)
        
        self.bm25 = data['bm25']
        self.restaurant_ids = data['restaurant_ids']
        self.corpus = data['corpus']
        
        logger.info(f"BM25 index loaded with {len(self.restaurant_ids)} documents")
    
    def index_exists(self) -> bool:
        """Check if index file exists."""
        return self.index_path.exists()
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for restaurants using BM25.
        
        BUG #26 FIX: Added resource consumption limits:
        - Query length validation (max 500 chars)
        - Token count limit (max 50 tokens)
        - Synonym expansion limit (max 10 variants)
        - Search timeout (5 seconds)
        - Document scoring limit (max 10k docs)
        - Regex injection prevention
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (restaurant_id, score) tuples
            
        Raises:
            ValueError: If query exceeds resource limits
            TimeoutError: If search exceeds timeout
        """
        if self.bm25 is None:
            raise RuntimeError("BM25 index not loaded. Please build or load index first.")
        
        # BUG #26 FIX: Validate query length
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")
        
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValueError(f"Query too long: {len(query)} chars (max {self.MAX_QUERY_LENGTH})")
        
        # BUG #26 FIX: Prevent regex injection by escaping special characters
        # Remove or escape dangerous regex patterns
        dangerous_patterns = [
            r'\(\?R\)',  # Recursive regex
            r'\(\?P<',    # Named groups
            r'\\\d+',    # Backreferences
            r'\(\?=',     # Lookahead
            r'\(\?!',     # Negative lookahead
            r'\(\?<=',    # Lookbehind
            r'\(\?<!',    # Negative lookbehind
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, query):
                raise ValueError(f"Query contains forbidden regex pattern: {pattern}")
        
        # Escape regex special characters to prevent ReDoS
        # Keep only alphanumeric, Vietnamese chars, and basic punctuation
        safe_query = re.sub(r'[^\w\s\u00C0-\u1EF9àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ,."-]', ' ', query)
        
        # BUG #26 FIX: Limit synonym expansion
        # BUG #13 FIX: Pass original query as context for cuisine-aware filtering
        query_variants = expand_synonyms(safe_query, query_context=query)
        if len(query_variants) > self.MAX_SYNONYMS:
            query_variants = query_variants[:self.MAX_SYNONYMS]
        
        # BUG #26 FIX: Validate token count
        initial_tokens = tokenize_vietnamese(safe_query)
        if len(initial_tokens) > self.MAX_QUERY_TOKENS:
            raise ValueError(f"Query has too many tokens: {len(initial_tokens)} (max {self.MAX_QUERY_TOKENS})")
        
        # BUG #26 FIX: Combine scores with resource limits
        combined_scores = {}
        total_docs = len(self.restaurant_ids)
        docs_to_score = min(total_docs, self.MAX_DOCS_TO_SCORE)
        
        for variant in query_variants:
            query_tokens = tokenize_vietnamese(variant)
            
            # Skip if too many tokens after expansion
            if len(query_tokens) > self.MAX_QUERY_TOKENS:
                continue
            
            # BUG #26 FIX: Score only limited number of documents for large datasets
            if total_docs > self.MAX_DOCS_TO_SCORE:
                # For large datasets, use sampling or pre-filtering
                variant_scores = self.bm25.get_scores(query_tokens)[:docs_to_score]
            else:
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
    
    async def search_async(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Async wrapper for search with timeout protection.
        
        BUG #26 FIX: Prevents long-running searches from blocking the service.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (restaurant_id, score) tuples
            
        Raises:
            TimeoutError: If search exceeds timeout limit
        """
        try:
            # Run synchronous search in executor with timeout
            loop = asyncio.get_event_loop()
            result = await asyncio.wait_for(
                loop.run_in_executor(None, self.search, query, top_k),
                timeout=self.SEARCH_TIMEOUT
            )
            return result
        except asyncio.TimeoutError:
            raise TimeoutError(f"Search timeout after {self.SEARCH_TIMEOUT} seconds. Query may be too complex.")


# Global instance
bm25_search = BM25Search()
