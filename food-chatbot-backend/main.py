"""
Food Chatbot Backend - FastAPI Application

Version: 2.0
Author: Restaurant Chatbot Team
License: MIT

This is the main entry point for the Restaurant Chatbot Backend API.
Provides AI-powered restaurant recommendations for Ho Chi Minh City using:
- Groq Cloud LLM (llama-3.3-70b-versatile)
- Hybrid search (FAISS + BM25)
- Multi-key load balancing
- Redis caching
- SQLite database for sessions
"""
import logging
from dotenv import load_dotenv

# Load .env before importing anything else
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from config import settings
from config.logging_config import setup_logging
from database import db_manager
from routes import chat_router, sessions_router, feedback_router
from middleware.rate_limiter import rate_limiter
from middleware.csrf_protection import CSRFProtectionMiddleware
# Note: auth_router removed - authentication handled by parent module

# Setup structured logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager - handles startup and shutdown.
    """
    # Startup
    logger.info("🚀 Starting Food Chatbot Backend...")
    
    # Auto-decrypt API keys from encrypted Gist
    logger.info("🔓 Auto-decrypting API keys...")
    from utils.auto_decrypt import auto_load_api_keys
    api_keys = auto_load_api_keys()
    if api_keys:
        logger.info(f"✅ Loaded {len(api_keys)} API keys successfully")
    else:
        logger.warning("⚠️  Warning: No API keys loaded, backend may not work properly")
    
    # Initialize database
    logger.info("📦 Initializing database...")
    await db_manager.init_db()
    
    # Clear expired cache
    await db_manager.clear_expired_cache()
    
    # Load indexes
    logger.info("🔍 Loading search indexes...")
    from services.vector_store import vector_store
    from services.bm25_search import bm25_search
    
    faiss_loaded = False
    bm25_loaded = False
    
    try:
        vector_store.load_index()  # Not async
        logger.info("  ✓ FAISS index loaded")
        faiss_loaded = True
    except Exception as e:
        logger.warning(f"  ⚠️  FAISS index not found: {e}")
    
    try:
        bm25_search.load_index()  # Not async
        logger.info("  ✓ BM25 index loaded")
        bm25_loaded = True
    except Exception as e:
        logger.warning(f"  ⚠️  BM25 index not found: {e}")
    
    if not faiss_loaded or not bm25_loaded:
        logger.info("  ℹ️  Run 'python init_system.py' to build missing indexes")
    
    # BUG #16 FIX: Start cache version sync background task
    logger.info("🔄 Starting cache invalidation system...")
    from services.hybrid_search import hybrid_search
    await hybrid_search.start_version_sync()
    logger.info("  ✓ Cache version sync started")
    
    # Setup monitoring (Prometheus + Sentry)
    logger.info("📊 Setting up monitoring...")
    from config.monitoring import setup_monitoring
    setup_monitoring(app)
    
    logger.info("✅ Application started successfully!")
    logger.info(f"📍 Server running on http://{settings.HOST}:{settings.PORT}")
    logger.info(f"📖 API docs available at http://{settings.HOST}:{settings.PORT}/docs")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down Food Chatbot Backend...")
    
    # Suppress semaphore warnings from sentence-transformers
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning, module="multiprocessing.resource_tracker")


# Create FastAPI app
app = FastAPI(
    title="🍽️ Restaurant Chatbot API",
    description="""
## AI-Powered Restaurant Recommendation System for Ho Chi Minh City

### Overview
This API provides intelligent restaurant recommendations using advanced AI and vector search technology.

### Key Features
- 🤖 **AI Chat**: Natural language conversation about restaurants
- 🔍 **Smart Search**: Hybrid search combining vector similarity (FAISS) + keyword matching (BM25)
- 💬 **Session Management**: Persistent conversation history
- 👍 **User Feedback**: Rating and feedback system
- 🔒 **Security**: Rate limiting, CSRF protection, security headers
- ⚡ **Performance**: Redis caching, multi-key load balancing

### Technology Stack
- **AI Model**: Groq Cloud - llama-3.3-70b-versatile
- **Vector Search**: FAISS (Facebook AI Similarity Search)
- **Keyword Search**: BM25 (Best Match 25)
- **Framework**: FastAPI 0.115.6
- **Database**: SQLite (async)
- **Cache**: Redis (optional)
- **Embeddings**: Sentence-Transformers

### Quick Start
1. **Health Check**: `GET /health`
2. **Start Chat**: `POST /api/chat` with `{"message": "Tìm quán ăn Nhật"}`
3. **View Docs**: Visit `/docs` (this page) or `/redoc`

### Main Endpoints
- **POST /api/chat** - Send message and get AI response
- **GET /api/sessions/{id}** - Get conversation history
- **POST /api/feedback** - Submit rating and feedback

### Rate Limits
- 100 requests per minute per IP address
- 30 chat messages per minute per session

### CORS Policy
- Development: `http://localhost:3000`, `http://localhost:5173`
- Production: Configure in `.env`

### Support
- **Documentation**: See `API_DOCUMENTATION.md` for detailed integration guide
- **Setup Guide**: See `README.md` for installation instructions
- **Bug Reports**: Check `bug.md` for known issues (all fixed in v2.0)

### Version History
- **v2.0** (2025-01): Groq Cloud migration, multi-key support, all 30 bugs fixed
- **v1.0** (2024-12): Initial release with GPT-4 integration
    """,
    version="2.0.0",
    lifespan=lifespan,
    contact={
        "name": "Restaurant Chatbot Team",
        "url": "https://github.com/your-repo/food-chatbot-backend",
    },
    license_info={
        "name": "MIT",
    },
    openapi_tags=[
        {
            "name": "health",
            "description": "Health check and system status endpoints"
        },
        {
            "name": "chat",
            "description": "AI chatbot conversation endpoints"
        },
        {
            "name": "sessions",
            "description": "Conversation session management"
        },
        {
            "name": "feedback",
            "description": "User feedback and ratings"
        }
    ]
)

# BUG #11 FIX: CORS Bypass Protection - Strict origin validation
# Implements comprehensive security measures against CORS misconfiguration

import re
from urllib.parse import urlparse
from typing import List

def validate_origin(origin: str) -> bool:
    """
    BUG #11 FIX: Validate origin against security best practices.
    
    Prevents common CORS bypass attacks:
    - Wildcard origins (*)
    - Subdomain wildcards (*.example.com)
    - Case sensitivity bypasses
    - Trailing slash inconsistencies
    - Protocol confusion (http vs https)
    - Port mismatches
    - IPv4/IPv6 confusion
    """
    if not origin or not isinstance(origin, str):
        return False
    
    # BUG #11 FIX: Reject wildcard origins
    if origin == '*' or '*' in origin:
        return False
    
    # BUG #11 FIX: Validate URL structure
    try:
        parsed = urlparse(origin)
        
        # Must have scheme and netloc
        if not parsed.scheme or not parsed.netloc:
            return False
        
        # BUG #11 FIX: Only allow http/https schemes
        if parsed.scheme not in ['http', 'https']:
            return False
        
        # BUG #11 FIX: Reject suspicious patterns
        suspicious_patterns = [
            r'[\x00-\x1f]',  # Control characters
            r'\\',  # Backslashes (UNC paths)
            r'@',  # User info (http://evil.com@good.com)
            r'\s',  # Whitespace
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, origin):
                return False
        
        return True
        
    except Exception:
        return False

def normalize_origin(origin: str) -> str:
    """
    BUG #11 FIX: Normalize origin for consistent comparison.
    
    Handles:
    - Case sensitivity (Localhost vs localhost)
    - Trailing slashes
    - IPv4/IPv6 normalization
    """
    if not origin:
        return origin
    
    # Remove trailing slash
    if origin.endswith('/'):
        origin = origin[:-1]
    
    # Parse and rebuild to normalize
    parsed = urlparse(origin)
    
    # Lowercase scheme and host
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # IPv6 normalization (already in brackets from urlparse)
    # IPv4 stays as-is
    
    return f"{scheme}://{netloc}"

# BUG #11 FIX: Strictly defined allowed origins
# NO wildcards, NO regex patterns, explicit list only
ALLOWED_ORIGINS_RAW = [
    # Development origins
    "http://localhost:3000",
    "http://localhost:5173",  # Vite default
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    # IPv6 localhost
    "http://[::1]:3000",
    "http://[::1]:5173",
    # Production origins (add your domain here)
    # "https://yourdomain.com",
    # "https://www.yourdomain.com",
]

# BUG #11 FIX: Validate and normalize all origins at startup
ALLOWED_ORIGINS: List[str] = []
for origin in ALLOWED_ORIGINS_RAW:
    if validate_origin(origin):
        normalized = normalize_origin(origin)
        if normalized and normalized not in ALLOWED_ORIGINS:
            ALLOWED_ORIGINS.append(normalized)
    else:
        logger.warning(f"⚠️  WARNING: Invalid origin rejected: {origin}")

# BUG #11 FIX: Log final allowed origins for security audit
logger.info("🔒 CORS Configuration:")
for origin in ALLOWED_ORIGINS:
    logger.info(f"   ✓ {origin}")

if not ALLOWED_ORIGINS:
    logger.warning("   ⚠️  WARNING: No valid origins configured! API will reject all cross-origin requests.")

# BUG #11 FIX: Custom CORS validation middleware
# Note: We still use CORSMiddleware but with strict validation
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Only validated origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],  # Add X-CSRF-Token
    expose_headers=["X-Total-Count"],  # Safe headers only
    max_age=600,  # 10 minutes preflight cache
)

# BUG #23 FIX: CSRF Protection Middleware
# Must be added AFTER CORS middleware to work with CORS preflight
app.add_middleware(
    CSRFProtectionMiddleware,
    allowed_origins=set(ALLOWED_ORIGINS)
)


# CHATGPT-STYLE ERROR HANDLERS - Specific error messages
@app.exception_handler(ConnectionError)
async def connection_error_handler(request: Request, exc: ConnectionError):
    """Handle network connection errors."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "connection_error",
            "message": "Unable to connect to external service",
            "detail": str(exc),
            "suggestion": "Please check your network connection or try again later"
        }
    )


@app.exception_handler(TimeoutError)
async def timeout_error_handler(request: Request, exc: TimeoutError):
    """Handle timeout errors."""
    return JSONResponse(
        status_code=504,
        content={
            "error": "timeout_error",
            "message": "Request timeout",
            "detail": "The operation took too long to complete",
            "suggestion": "Try simplifying your query or try again in a few moments"
        }
    )


import aiosqlite
@app.exception_handler(aiosqlite.Error)
async def database_error_handler(request: Request, exc: aiosqlite.Error):
    """Handle database errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "database_error",
            "message": "Database operation failed",
            "detail": str(exc),
            "suggestion": "We're experiencing technical difficulties. Please try again later"
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with specific messages based on type."""
    error_type = type(exc).__name__
    
    # Model/LLM errors
    if "model" in str(exc).lower() or "gemini" in str(exc).lower() or "api" in str(exc).lower():
        return JSONResponse(
            status_code=503,
            content={
                "error": "model_error",
                "message": "AI service unavailable",
                "detail": str(exc),
                "suggestion": "Our AI service (Google Gemini) is temporarily unavailable. Please try again in a few minutes."
            }
        )
    
    # JSON parsing errors
    elif "json" in str(exc).lower() or isinstance(exc, ValueError):
        return JSONResponse(
            status_code=400,
            content={
                "error": "parsing_error",
                "message": "Invalid data format",
                "detail": str(exc),
                "suggestion": "Please check your input and try again"
            }
        )
    
    # Generic error
    return JSONResponse(
        status_code=500,
        content={
            "error": error_type.lower(),
            "message": "An unexpected error occurred",
            "detail": str(exc),
            "suggestion": "Please try again or contact support if the problem persists"
        }
    )


# BUG #27 FIX: Security Headers Middleware
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """
    BUG #27 & #28 FIX: Add security headers and remove verbose server info.
    
    Security headers added:
    - X-Frame-Options: Prevents clickjacking attacks
    - X-Content-Type-Options: Prevents MIME sniffing attacks
    - X-XSS-Protection: Enables browser XSS filter
    - Strict-Transport-Security: Enforces HTTPS
    - Content-Security-Policy: Restricts resource loading
    - Referrer-Policy: Controls referrer information
    - Permissions-Policy: Controls browser features
    
    Server header protection:
    - Removes FastAPI/Uvicorn version information
    - Prevents server fingerprinting
    """
    response = await call_next(request)
    
    # BUG #27 FIX: Add comprehensive security headers
    response.headers["X-Frame-Options"] = "DENY"  # Prevent clickjacking
    response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME sniffing
    response.headers["X-XSS-Protection"] = "1; mode=block"  # Enable XSS filter
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"  # Force HTTPS
    
    # Content Security Policy - restrictive but allows API functionality
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self'; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )
    
    # Referrer Policy - don't leak referrer info
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Permissions Policy - disable unnecessary browser features
    response.headers["Permissions-Policy"] = (
        "geolocation=(), "
        "microphone=(), "
        "camera=(), "
        "payment=(), "
        "usb=()"
    )
    
    # BUG #28 FIX: Remove verbose server information
    # Remove or replace Server header to prevent version fingerprinting
    if "Server" in response.headers:
        response.headers["Server"] = "API"  # Generic name without version
    
    # Remove X-Powered-By if present
    if "X-Powered-By" in response.headers:
        del response.headers["X-Powered-By"]
    
    return response


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    # Skip rate limiting for health checks and docs
    if request.url.path in ["/", "/health", "/docs", "/openapi.json"]:
        return await call_next(request)
    
    try:
        await rate_limiter.check_rate_limit(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail}
        )
    
    response = await call_next(request)
    return response

# ============================================================================
# API Versioning - v1 routes
# ============================================================================
from fastapi import APIRouter

# Create versioned router
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(chat_router)
api_v1_router.include_router(sessions_router)
api_v1_router.include_router(feedback_router)

# Include versioned routes
app.include_router(api_v1_router)

# Legacy routes (without version) - for backward compatibility
# These will be deprecated in v3.0
app.include_router(chat_router, prefix="/api", deprecated=True)
app.include_router(sessions_router, prefix="/api", deprecated=True)
app.include_router(feedback_router, prefix="/api", deprecated=True)


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


@app.get("/api/csrf-token")
async def get_csrf_token(request: Request):
    """
    Get CSRF token for subsequent requests.
    
    The token is automatically set in a cookie by the CSRF middleware.
    This endpoint just returns the token value so clients can include it in headers.
    """
    # Get the token from the cookie (set by middleware)
    csrf_cookie_name = "csrf_token"
    token = request.cookies.get(csrf_cookie_name)
    
    if not token:
        # If no token exists yet, the middleware will set one on the response
        # Return a message telling the client to check the cookie
        return {
            "message": "CSRF token will be set in cookie",
            "instructions": {
                "cookie": f"Token will be automatically set in '{csrf_cookie_name}' cookie",
                "header": "Include the cookie token value in 'X-CSRF-Token' header for protected requests",
                "protected_methods": ["POST", "PUT", "PATCH", "DELETE"],
                "note": "Call this endpoint again or check the Set-Cookie header to get the token value"
            }
        }
    
    # Return the existing token
    return {
        "csrf_token": token,
        "instructions": {
            "cookie": f"Token is set in '{csrf_cookie_name}' cookie",
            "header": f"Include this token in 'X-CSRF-Token' header for protected requests",
            "protected_methods": ["POST", "PUT", "PATCH", "DELETE"],
            "example": f"curl -X POST /api/chat -H 'X-CSRF-Token: {token}' -b 'csrf_token={token}'"
        }
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for load balancers and monitoring.
    
    Returns basic health status without checking external dependencies.
    Use /ready for comprehensive readiness checks.
    
    Returns:
        Basic health status
    """
    return {
        "status": "healthy",
        "version": "2.0.0",
        "service": "food-chatbot-backend"
    }


@app.get("/ready", tags=["health"])
async def readiness_check():
    """
    Readiness check endpoint - verifies all dependencies are ready.
    
    Checks:
    - Database connectivity
    - Groq API key availability
    - Search indexes loaded
    
    Returns:
        Detailed readiness status with component states
    """
    from services.groq_service import get_groq_service
    from services.vector_store import vector_store
    from services.bm25_search import bm25_search
    
    checks = {
        "database": "unknown",
        "groq_api": "unknown",
        "faiss_index": "unknown",
        "bm25_index": "unknown"
    }
    
    overall_status = "ready"
    
    # Check database
    try:
        async with db_manager.get_connection() as db:
            await db.execute("SELECT 1")
        checks["database"] = "connected"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        overall_status = "not_ready"
    
    # Check Groq API keys
    try:
        groq_service = get_groq_service()
        health_stats = groq_service.get_health_stats()
        keys_available = any(
            not stats['is_blocked'] 
            for stats in health_stats['key_stats'].values()
        )
        checks["groq_api"] = "available" if keys_available else "all_keys_blocked"
        if not keys_available:
            overall_status = "degraded"
    except Exception as e:
        checks["groq_api"] = f"error: {str(e)}"
        overall_status = "not_ready"
    
    # Check FAISS index
    try:
        if vector_store.index is not None:
            checks["faiss_index"] = "loaded"
        else:
            checks["faiss_index"] = "not_loaded"
            overall_status = "degraded"
    except Exception:
        checks["faiss_index"] = "not_loaded"
        overall_status = "degraded"
    
    # Check BM25 index
    try:
        if bm25_search.bm25 is not None:
            checks["bm25_index"] = "loaded"
        else:
            checks["bm25_index"] = "not_loaded"
            overall_status = "degraded"
    except Exception:
        checks["bm25_index"] = "not_loaded"
        overall_status = "degraded"
    
    status_code = 200 if overall_status in ["ready", "degraded"] else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            "status": overall_status,
            "checks": checks,
            "version": "2.0.0"
        }
    )


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
