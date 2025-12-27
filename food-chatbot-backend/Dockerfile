# =============================================================================
# Food Chatbot Backend - Production Dockerfile
# =============================================================================
# Multi-stage build for optimized production image
#
# Build: docker build -t food-chatbot-backend .
# Run: docker run -p 8000:8000 --env-file .env.production food-chatbot-backend
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies and build the application
# -----------------------------------------------------------------------------
FROM python:3.13-slim as builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# -----------------------------------------------------------------------------
# Stage 2: Production - Minimal runtime image
# -----------------------------------------------------------------------------
FROM python:3.13-slim as production

# Labels for container metadata
LABEL maintainer="Restaurant Chatbot Team" \
    version="2.0.0" \
    description="AI-powered restaurant chatbot backend for Ho Chi Minh City"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    # Application settings
    HOST=0.0.0.0 \
    PORT=8000 \
    DEBUG=false

# Create non-root user for security
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    # For healthcheck
    curl \
    # Timezone data
    tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Create directories for data with correct permissions
RUN mkdir -p /app/data /app/database /app/logs && \
    chown -R appuser:appgroup /app

# Copy application code
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose the application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default command - use gunicorn for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]

# -----------------------------------------------------------------------------
# Stage 3: Development - Full development environment
# -----------------------------------------------------------------------------
FROM production as development

# Switch to root to install dev dependencies
USER root

# Install development tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install development Python packages
COPY requirements-dev.txt* ./
RUN if [ -f requirements-dev.txt ]; then pip install -r requirements-dev.txt; fi

# Switch back to non-root user
USER appuser

# Override command for development (with hot reload)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
