"""
Vector store service using FAISS for semantic search.
"""
import numpy as np
import faiss
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from config import settings
from services.data_preprocessor import data_preprocessor


class VectorStore:
    """FAISS-based vector store for semantic search."""
    
    def __init__(self):
        self.index = None
        self.model = None
        self.restaurant_ids = []
        self.dimension = settings.VECTOR_DIMENSION
        self.index_path = Path(settings.FAISS_INDEX_PATH)
        
    def load_model(self):
        """Load sentence transformer model."""
        if self.model is None:
            print(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
            self.dimension = self.model.get_sentence_embedding_dimension()
            print(f"Model loaded. Embedding dimension: {self.dimension}")
    
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
            print("Loading existing FAISS index...")
            self.load_index()
            return
        
        print("Building new FAISS index...")
        
        # Load model
        self.load_model()
        
        # Load restaurant data
        restaurants = await data_preprocessor.load_from_database()
        
        if not restaurants:
            print("No restaurant data found. Please run data initialization first.")
            return
        
        # Create searchable texts
        texts = []
        self.restaurant_ids = []
        
        for restaurant in restaurants:
            searchable_text = data_preprocessor.create_searchable_text(restaurant)
            texts.append(searchable_text)
            self.restaurant_ids.append(restaurant['id'])
        
        print(f"Creating embeddings for {len(texts)} restaurants...")
        embeddings = self.create_embeddings(texts)
        
        # Create FAISS index with IVF Flat
        print("Creating FAISS IVF Flat index...")
        
        # Number of clusters for IVF
        nlist = min(100, len(texts) // 10)
        if nlist < 1:
            nlist = 1
        
        # Create quantizer
        quantizer = faiss.IndexFlatL2(self.dimension)
        
        # Create IVF index
        self.index = faiss.IndexIVFFlat(quantizer, self.dimension, nlist)
        
        # Train index
        print("Training index...")
        self.index.train(embeddings)
        
        # Add vectors
        print("Adding vectors to index...")
        self.index.add(embeddings)
        
        # Save index
        self.save_index()
        print(f"FAISS index built successfully with {self.index.ntotal} vectors")
    
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
        
        print(f"Index saved to {self.index_path}")
    
    def load_index(self):
        """Load FAISS index and metadata from disk."""
        index_file = self.index_path / "faiss.index"
        metadata_file = self.index_path / "metadata.pkl"
        
        if not index_file.exists() or not metadata_file.exists():
            raise FileNotFoundError("Index files not found")
        
        # Load FAISS index
        self.index = faiss.read_index(str(index_file))
        
        # Load metadata
        with open(metadata_file, 'rb') as f:
            metadata = pickle.load(f)
        
        self.restaurant_ids = metadata['restaurant_ids']
        self.dimension = metadata['dimension']
        
        # Load model
        self.load_model()
        
        print(f"Index loaded with {self.index.ntotal} vectors")
    
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
