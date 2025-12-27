"""
Vector store service using FAISS for semantic search.
"""
import logging
import numpy as np
import faiss
import pickle
import os
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from config import settings
from services.data_preprocessor import data_preprocessor

logger = logging.getLogger(__name__)


class VectorStore:
    """FAISS-based vector store for semantic search."""
    
    # BUG #27 FIX: Allowed base directory for index storage
    ALLOWED_BASE_DIR = Path("./data").resolve()
    MAX_PATH_LENGTH = 255
    
    def __init__(self):
        self.index = None
        self.model = None
        self.restaurant_ids = []
        self.dimension = settings.VECTOR_DIMENSION
        
        # BUG #27 FIX: Validate and sanitize index path
        self.index_path = self._validate_index_path(settings.FAISS_INDEX_PATH)
    
    @staticmethod
    def _validate_index_path(path_str: str) -> Path:
        """
        BUG #27 FIX: Validate index path to prevent path traversal attacks.
        
        Security checks:
        - Path length validation
        - Null byte injection prevention
        - Path traversal prevention (../ or .\\)
        - Symbolic link resolution and validation
        - Absolute path requirement
        - Restricted to allowed base directory
        - No special device files
        
        Args:
            path_str: Path string from settings
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If path is invalid or unsafe
        """
        # Check 1: Basic validation
        if not path_str or not isinstance(path_str, str):
            raise ValueError("Index path must be a non-empty string")
        
        # Check 2: Length validation
        if len(path_str) > VectorStore.MAX_PATH_LENGTH:
            raise ValueError(f"Index path too long: {len(path_str)} chars (max {VectorStore.MAX_PATH_LENGTH})")
        
        # Check 3: Null byte injection prevention
        if '\x00' in path_str or '\0' in path_str:
            raise ValueError("Index path contains null bytes")
        
        # Check 4: Path traversal prevention
        dangerous_patterns = ['../', '..\\', '../', '..\\']
        if any(pattern in path_str for pattern in dangerous_patterns):
            raise ValueError("Index path contains path traversal sequences")
        
        # Check 5: Resolve to absolute path
        try:
            path = Path(path_str).resolve(strict=False)
        except (OSError, RuntimeError) as e:
            raise ValueError(f"Invalid path format: {e}")
        
        # Check 6: Ensure path is within allowed base directory
        try:
            # Create base dir if doesn't exist
            VectorStore.ALLOWED_BASE_DIR.mkdir(parents=True, exist_ok=True)
            
            # Check if path is relative to allowed base
            path.relative_to(VectorStore.ALLOWED_BASE_DIR)
        except ValueError:
            raise ValueError(
                f"Index path must be within {VectorStore.ALLOWED_BASE_DIR}, got {path}"
            )
        
        # Check 7: Prevent special device files on Unix
        path_str_lower = str(path).lower()
        dangerous_paths = ['/dev/', '/proc/', '/sys/', '\\\\', 'c:\\windows\\', 'c:\\system32\\']
        if any(dangerous in path_str_lower for dangerous in dangerous_paths):
            raise ValueError("Index path points to system/device files")
        
        # Check 8: If path exists, verify it's not a symlink to dangerous location
        if path.exists():
            # Resolve symlinks
            real_path = path.resolve(strict=True)
            
            # Verify resolved path is still within allowed base
            try:
                real_path.relative_to(VectorStore.ALLOWED_BASE_DIR)
            except ValueError:
                raise ValueError(
                    f"Symbolic link points outside allowed directory: {real_path}"
                )
        
        return path
        
    def load_model(self):
        """Load sentence transformer model."""
        if self.model is None:
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(f"Model loaded. Embedding dimension: {self.dimension}")
    
    def create_embeddings(self, texts: List[str]) -> np.ndarray:
        """
        Create embeddings for texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Numpy array of embeddings
        """
        if self.model is None:
            self.load_model()
        
        embeddings = self.model.encode(texts, show_progress_bar=True)
        return embeddings.astype('float32')
    
    async def build_index(self, force_rebuild: bool = False):
        """
        Build FAISS index from restaurant data.
        
        Args:
            force_rebuild: Force rebuild even if index exists
        """
        # Check if index already exists
        if not force_rebuild and self.index_exists():
            logger.info("Loading existing FAISS index...")
            self.load_index()
            return
        
        logger.info("Building new FAISS index...")
        
        # Load model
        self.load_model()
        
        # Load restaurant data
        restaurants = await data_preprocessor.load_from_database()
        
        if not restaurants:
            logger.warning("No restaurant data found. Please run data initialization first.")
            return
        
        # Create searchable texts
        texts = []
        self.restaurant_ids = []
        
        for restaurant in restaurants:
            searchable_text = data_preprocessor.create_searchable_text(restaurant)
            texts.append(searchable_text)
            self.restaurant_ids.append(restaurant['id'])
        
        logger.info(f"Creating embeddings for {len(texts)} restaurants...")
        embeddings = self.create_embeddings(texts)
        
        # Create FAISS index with IVF Flat
        logger.info("Creating FAISS IVF Flat index...")
        
        # Number of clusters for IVF
        nlist = min(100, len(texts) // 10)
        if nlist < 1:
            nlist = 1
        
        # Create quantizer
        quantizer = faiss.IndexFlatL2(self.dimension)
        
        # Create IVF index
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        # Train index
        logger.info("Training index...")
        self.index.train(embeddings)
        
        # Add vectors
        logger.info("Adding vectors to index...")
        self.index.add(embeddings)
        
        # Save index
        self.save_index()
        logger.info(f"FAISS index built successfully with {self.index.ntotal} vectors")
    
    def save_index(self):
        """Save FAISS index and metadata to disk."""
        self.index_path.mkdir(parents=True, exist_ok=True)
        
        # Save FAISS index
        index_file = self.index_path / "faiss.index"
        faiss.write_index(self.index, str(index_file))
        
        # Save metadata
        metadata = {
            'restaurant_ids': self.restaurant_ids,
            'dimension': self.dimension
        }
        metadata_file = self.index_path / "metadata.pkl"
        with open(metadata_file, 'wb') as f:
            pickle.dump(metadata, f)
        
        logger.info(f"Index saved to {self.index_path}")
    
    def load_index(self):
        """Load FAISS index and metadata from disk."""
        # BUG #27 FIX: Validate file paths before loading
        index_file = self.index_path / "faiss.index"
        metadata_file = self.index_path / "metadata.pkl"
        
        # Additional validation for file paths
        for file_path in [index_file, metadata_file]:
            if not file_path.exists():
                raise FileNotFoundError(f"Index file not found: {file_path}")
            
            # BUG #27 FIX: Verify file is within allowed directory
            try:
                file_path.resolve(strict=True).relative_to(self.ALLOWED_BASE_DIR)
            except ValueError:
                raise ValueError(f"Index file outside allowed directory: {file_path}")
            
            # BUG #27 FIX: Prevent loading from special devices
            if not file_path.is_file():
                raise ValueError(f"Index path is not a regular file: {file_path}")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        self.restaurant_ids = metadata['restaurant_ids']
        self.dimension = metadata['dimension']
        
        # Load model
        self.load_model()
        
        logger.info(f"Index loaded with {self.index.ntotal} vectors")
    
    def index_exists(self) -> bool:
        """Check if index files exist."""
        index_file = self.index_path / "faiss.index"
        metadata_file = self.index_path / "metadata.pkl"
        return index_file.exists() and metadata_file.exists()
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[int, float]]:
        """
        Search for similar restaurants using semantic search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of (restaurant_id, distance) tuples
        """
        if self.index is None:
            raise RuntimeError("Index not loaded. Please build or load index first.")
        
        if self.model is None:
            self.load_model()
        
        # Create query embedding
        query_embedding = self.model.encode([query]).astype('float32')
        
        # Search
        distances, indices = self.index.search(query_embedding, top_k)
        
        # Convert to restaurant IDs
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx >= 0 and idx < len(self.restaurant_ids):
                restaurant_id = self.restaurant_ids[idx]
                results.append((restaurant_id, float(distance)))
        
        return results


# Global instance
vector_store = VectorStore()
