# syntax=docker/dockerfile:1
# Django Finance Dockerfile
# Multi-stage build for optimized production images

# =============================================================================
# Base Stage - Common dependencies
# =============================================================================
FROM python:3.12-slim-bookworm AS base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONFAULTHANDLER=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client libraries
    libpq5 \
    # For healthchecks
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

WORKDIR /app

# =============================================================================
# Builder Stage - Install dependencies
# =============================================================================
FROM base AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # PostgreSQL client for psycopg build
    libpq-dev \
    # C compiler for native extensions
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install uv for fast dependency management
RUN pip install uv

# Copy dependency files
COPY pyproject.toml ./

# Create virtual environment and install dependencies
RUN uv venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Install production dependencies
RUN uv pip install -e .

# Install production extras
RUN uv pip install -e ".[production]"

# =============================================================================
# Development Stage
# =============================================================================
FROM builder AS development

# Install development dependencies
RUN uv pip install -e ".[dev]"

# Copy application code
COPY . .

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# =============================================================================
# Production Stage
# =============================================================================
FROM base AS production

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY --chown=appuser:appgroup . .

# Create necessary directories
RUN mkdir -p staticfiles media \
    && chown -R appuser:appgroup staticfiles media

USER appuser

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Production server using Daphne (ASGI)
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "config.asgi:application"]

# =============================================================================
# Celery Worker Stage
# =============================================================================
FROM production AS celery-worker

# Override CMD for Celery worker
CMD ["celery", "-A", "config", "worker", "-l", "INFO", "--concurrency=2"]

# =============================================================================
# Celery Beat Stage
# =============================================================================
FROM production AS celery-beat

# Override CMD for Celery beat
CMD ["celery", "-A", "config", "beat", "-l", "INFO"]
