"""
Initialization script for the chatbot backend.
Run this script once to initialize the database and build search indexes.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.db_manager import db_manager
from services.data_preprocessor import data_preprocessor
from services.vector_store import vector_store
from services.bm25_search import bm25_search


async def main():
    """Main initialization routine."""
    print("=" * 60)
    print("Food Chatbot Backend - Initialization")
    print("=" * 60)
    
    try:
        # Step 1: Initialize database
        print("\n[1/4] Initializing database schema...")
        await db_manager.init_db()
        print("✅ Database initialized")
        
        # Step 2: Load and preprocess restaurant data
        print("\n[2/4] Loading and preprocessing restaurant data...")
        await data_preprocessor.initialize_data()
        print("✅ Restaurant data loaded")
        
        # Step 3: Build FAISS vector index
        print("\n[3/4] Building FAISS vector index...")
        print("⚠️  This may take several minutes depending on data size...")
        await vector_store.build_index(force_rebuild=True)
        print("✅ FAISS index built")
        
        # Step 4: Build BM25 keyword index
        print("\n[4/4] Building BM25 keyword index...")
        await bm25_search.build_index(force_rebuild=True)
        print("✅ BM25 index built")
        
        print("\n" + "=" * 60)
        print("🎉 Initialization completed successfully!")
        print("=" * 60)
        print("\nYou can now start the server with:")
        print("  python main.py")
        print("\nOr with uvicorn:")
        print("  uvicorn main:app --reload")
        
    except Exception as e:
        print(f"\n❌ Error during initialization: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
