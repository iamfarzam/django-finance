"""Shared views for Django Finance.

This module provides:
- Health check endpoints
- Common utility views
"""

from __future__ import annotations

from typing import Any

from django.http import JsonResponse


def health_check(request: Any) -> JsonResponse:
    """Basic health check endpoint.

    Returns 200 OK if the application is running.
    This endpoint is used for liveness probes.

    Args:
        request: The HTTP request (unused but required by Django).

    Returns:
        JSON response with status "healthy".
    """
    return JsonResponse({"status": "healthy"})


def health_ready(request: Any) -> JsonResponse:
    """Readiness check endpoint.

    Checks connectivity to critical services:
    - Database (PostgreSQL)
    - Cache (Redis)
    - Celery broker (Redis)

    Returns 200 if all services are reachable, 503 otherwise.
    This endpoint is used for readiness probes.

    Args:
        request: The HTTP request (unused but required by Django).

    Returns:
        JSON response with status and service details.
    """
    checks: dict[str, dict[str, Any]] = {}
    all_healthy = True

    # Check database
    try:
        from django.db import connection

        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = {"status": "healthy"}
    except Exception as e:
        checks["database"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check cache/Redis
    try:
        from django.core.cache import cache

        cache.set("health_check", "ok", timeout=1)
        value = cache.get("health_check")
        if value == "ok":
            checks["cache"] = {"status": "healthy"}
        else:
            checks["cache"] = {"status": "unhealthy", "error": "Cache read/write failed"}
            all_healthy = False
    except Exception as e:
        checks["cache"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    # Check Celery broker
    try:
        from config.celery import app as celery_app

        conn = celery_app.connection()
        conn.ensure_connection(max_retries=1, timeout=3)
        conn.release()
        checks["celery_broker"] = {"status": "healthy"}
    except Exception as e:
        checks["celery_broker"] = {"status": "unhealthy", "error": str(e)}
        all_healthy = False

    status_code = 200 if all_healthy else 503
    return JsonResponse(
        {
            "status": "healthy" if all_healthy else "unhealthy",
            "checks": checks,
        },
        status=status_code,
    )
