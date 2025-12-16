"""
Food Chatbot Backend - FastAPI Application
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config import settings
from database import db_manager
from routes import chat_router, sessions_router, feedback_router
# Note: auth_router removed - authentication handled by parent module


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.
    """
    # Startup
    print("🚀 Starting Food Chatbot Backend...")
    
    # Initialize database
    print("📦 Initializing database...")
    await db_manager.init_db()
    
    # Clear expired cache
    await db_manager.clear_expired_cache()
    
    # Load indexes
    print("🔍 Loading search indexes...")
    from services.vector_store import vector_store
    from services.bm25_search import bm25_search
    
    faiss_loaded = False
    bm25_loaded = False
    
    try:
        vector_store.load_index()  # Not async
        print("  ✓ FAISS index loaded")
        faiss_loaded = True
    except Exception as e:
        print(f"  ⚠️  FAISS index not found: {e}")
    
    try:
        bm25_search.load_index()  # Not async
        print("  ✓ BM25 index loaded")
        bm25_loaded = True
    except Exception as e:
        print(f"  ⚠️  BM25 index not found: {e}")
    
    if not faiss_loaded or not bm25_loaded:
        print("  ℹ️  Run 'python init_system.py' to build missing indexes")
    
    print("✅ Application started successfully!")
    print(f"📍 Server running on http://{settings.HOST}:{settings.PORT}")
    print(f"📖 API docs available at http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # Shutdown
    print("👋 Shutting down Food Chatbot Backend...")
    
    # Suppress semaphore warnings from sentence-transformers
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")


# Create FastAPI app
app = FastAPI(
    title="Food Chatbot Backend API",
    description="""
    AI-powered food and restaurant recommendation chatbot for Ho Chi Minh City.
    """,
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware - Allow all origins for development
# TODO: Restrict origins in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers with /api prefix
# Note: auth_router not included - parent module handles authentication
app.include_router(chat_router, prefix="/api")
app.include_router(sessions_router, prefix="/api")
app.include_router(feedback_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint - API information."""
    return {
        "name": "Food Chatbot Backend API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/auth",
            "chat": "/api/chat",
            "sessions": "/api/sessions",
            "feedback": "/api/feedback"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from services import ollama_service
    
    # Check Ollama service
    ollama_healthy = await ollama_service.check_health()
    
    return {
        "status": "healthy" if ollama_healthy else "degraded",
        "database": "connected",
        "ollama": "connected" if ollama_healthy else "disconnected"
    }


@app.get("/stats")
async def get_stats():
    """Get system statistics."""
    import aiosqlite
    
    async with db_manager.get_connection() as db:
        # Count restaurants
        async with db.execute("SELECT COUNT(*) FROM restaurants") as cursor:
            restaurant_count = (await cursor.fetchone())[0]
        
        # Count sessions
        async with db.execute("SELECT COUNT(*) FROM sessions") as cursor:
            session_count = (await cursor.fetchone())[0]
        
        # Count messages
        async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
            message_count = (await cursor.fetchone())[0]
        
        # Count feedback
        async with db.execute("SELECT COUNT(*) FROM user_feedback") as cursor:
            feedback_count = (await cursor.fetchone())[0]
        
        # Cache stats
        async with db.execute("SELECT COUNT(*) FROM query_cache WHERE expires_at > datetime('now')") as cursor:
            cache_count = (await cursor.fetchone())[0]
    
    return {
        "restaurants": restaurant_count,
        "sessions": session_count,
        "messages": message_count,
        "feedback": feedback_count,
        "cached_queries": cache_count
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )
