"""
Monitoring Configuration - Prometheus & Sentry Integration

This module configures:
- Prometheus metrics collection
- Sentry error tracking
- OpenTelemetry distributed tracing
"""

import os
import logging
from functools import wraps
from typing import Callable, Optional

from fastapi import FastAPI, Request, Response
from config import settings

logger = logging.getLogger(__name__)

# ============================================================================
# Prometheus Metrics Configuration
# ============================================================================

def setup_prometheus(app: FastAPI) -> None:
    """
    Configure Prometheus metrics instrumentation for FastAPI.
    
    Metrics collected:
    - http_requests_total: Total HTTP requests by method, status, path
    - http_request_duration_seconds: Request duration histogram
    - http_requests_in_progress: Current requests being processed
    - Custom app metrics (chat messages, search queries, etc.)
    """
    try:
        from prometheus_fastapi_instrumentator import Instrumentator
        from prometheus_fastapi_instrumentator.metrics import Info
        from prometheus_client import Counter, Histogram, Gauge
        
        # Initialize instrumentator with custom configuration
        instrumentator = Instrumentator(
            should_group_status_codes=True,
            should_ignore_untemplated=True,
            should_respect_env_var=True,
            should_instrument_requests_inprogress=True,
            excluded_handlers=["/health", "/metrics"],
            env_var_name="ENABLE_METRICS",
            inprogress_name="http_requests_inprogress",
            inprogress_labels=True,
        )
        
        # Add default metrics
        instrumentator.add(
            Info(
                name="app_info",
                description="Application information",
                const_labels={
                    "app_name": "food-chatbot-backend",
                    "version": "2.0.0"
                }
            )
        )
        
        # Custom metrics
        # Chat message counter
        chat_messages = Counter(
            "chatbot_messages_total",
            "Total number of chat messages",
            ["language", "has_session"]
        )
        
        # Search query counter
        search_queries = Counter(
            "chatbot_search_queries_total",
            "Total number of search queries",
            ["search_type"]  # vector, bm25, hybrid
        )
        
        # AI response time histogram
        ai_response_time = Histogram(
            "chatbot_ai_response_seconds",
            "AI response generation time",
            ["model"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
        )
        
        # Active sessions gauge
        active_sessions = Gauge(
            "chatbot_active_sessions",
            "Number of active chat sessions"
        )
        
        # Cache hit ratio
        cache_hits = Counter(
            "chatbot_cache_hits_total",
            "Total cache hits",
            ["cache_type"]  # redis, local
        )
        
        cache_misses = Counter(
            "chatbot_cache_misses_total",
            "Total cache misses",
            ["cache_type"]
        )
        
        # Store custom metrics for access by other modules
        app.state.metrics = {
            "chat_messages": chat_messages,
            "search_queries": search_queries,
            "ai_response_time": ai_response_time,
            "active_sessions": active_sessions,
            "cache_hits": cache_hits,
            "cache_misses": cache_misses,
        }
        
        # Instrument the app and expose metrics endpoint
        instrumentator.instrument(app).expose(
            app,
            endpoint="/metrics",
            include_in_schema=True,
            tags=["monitoring"]
        )
        
        logger.info("✅ Prometheus metrics configured at /metrics")
        
    except ImportError:
        logger.warning("⚠️ prometheus-fastapi-instrumentator not installed, metrics disabled")
    except Exception as e:
        logger.error(f"❌ Failed to setup Prometheus: {e}")


# ============================================================================
# Sentry Error Tracking Configuration
# ============================================================================

def setup_sentry(app: FastAPI) -> None:
    """
    Configure Sentry for error tracking and performance monitoring.
    
    Features:
    - Automatic error capture
    - Performance tracing
    - User context
    - Release tracking
    """
    sentry_dsn = os.getenv("SENTRY_DSN", "")
    
    if not sentry_dsn:
        logger.info("ℹ️ Sentry DSN not configured, error tracking disabled")
        return
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        from sentry_sdk.integrations.aiohttp import AioHttpIntegration
        
        # Configure Sentry SDK
        sentry_sdk.init(
            dsn=sentry_dsn,
            integrations=[
                StarletteIntegration(transaction_style="endpoint"),
                FastApiIntegration(transaction_style="endpoint"),
                LoggingIntegration(
                    level=logging.INFO,
                    event_level=logging.ERROR
                ),
                AioHttpIntegration(),
            ],
            # Environment configuration
            environment=os.getenv("ENVIRONMENT", "development"),
            release=f"food-chatbot-backend@2.0.0",
            
            # Performance monitoring
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "0.1")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            
            # Error filtering
            before_send=_filter_sensitive_data,
            
            # Additional configuration
            attach_stacktrace=True,
            send_default_pii=False,  # GDPR compliance
            max_breadcrumbs=50,
        )
        
        logger.info("✅ Sentry error tracking configured")
        
    except ImportError:
        logger.warning("⚠️ sentry-sdk not installed, error tracking disabled")
    except Exception as e:
        logger.error(f"❌ Failed to setup Sentry: {e}")


def _filter_sensitive_data(event: dict, hint: dict) -> Optional[dict]:
    """
    Filter sensitive data before sending to Sentry.
    
    Removes:
    - API keys
    - Passwords
    - Session tokens
    - Personal user data
    """
    if event.get("request"):
        request = event["request"]
        
        # Filter headers
        if "headers" in request:
            sensitive_headers = ["authorization", "cookie", "x-api-key"]
            for header in sensitive_headers:
                if header in request["headers"]:
                    request["headers"][header] = "[FILTERED]"
        
        # Filter query strings
        if "query_string" in request:
            if "api_key" in request["query_string"]:
                request["query_string"] = "[FILTERED]"
        
        # Filter body data
        if "data" in request:
            data = request["data"]
            if isinstance(data, dict):
                sensitive_fields = ["password", "api_key", "token", "secret"]
                for field in sensitive_fields:
                    if field in data:
                        data[field] = "[FILTERED]"
    
    return event


# ============================================================================
# Custom Metrics Helpers
# ============================================================================

def record_chat_message(app: FastAPI, language: str = "vi", has_session: bool = True):
    """Record a chat message metric."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["chat_messages"].labels(
            language=language,
            has_session=str(has_session).lower()
        ).inc()


def record_search_query(app: FastAPI, search_type: str = "hybrid"):
    """Record a search query metric."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["search_queries"].labels(
            search_type=search_type
        ).inc()


def record_ai_response_time(app: FastAPI, model: str, duration: float):
    """Record AI response time."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["ai_response_time"].labels(
            model=model
        ).observe(duration)


def record_cache_hit(app: FastAPI, cache_type: str = "redis"):
    """Record a cache hit."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["cache_hits"].labels(
            cache_type=cache_type
        ).inc()


def record_cache_miss(app: FastAPI, cache_type: str = "redis"):
    """Record a cache miss."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["cache_misses"].labels(
            cache_type=cache_type
        ).inc()


def set_active_sessions(app: FastAPI, count: int):
    """Set the number of active sessions."""
    if hasattr(app.state, "metrics"):
        app.state.metrics["active_sessions"].set(count)


# ============================================================================
# Performance Tracking Decorator
# ============================================================================

def track_performance(operation_name: str):
    """
    Decorator to track operation performance in Sentry.
    
    Usage:
        @track_performance("search_restaurants")
        async def search(query: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                import sentry_sdk
                with sentry_sdk.start_span(op=operation_name) as span:
                    result = await func(*args, **kwargs)
                    return result
            except ImportError:
                return await func(*args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# Setup All Monitoring
# ============================================================================

def setup_monitoring(app: FastAPI) -> None:
    """
    Initialize all monitoring systems.
    
    Call this function during app startup.
    """
    logger.info("🔍 Setting up monitoring systems...")
    
    # Setup Prometheus
    setup_prometheus(app)
    
    # Setup Sentry
    setup_sentry(app)
    
    logger.info("✅ Monitoring systems initialized")
