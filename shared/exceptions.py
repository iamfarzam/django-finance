"""Custom exception handling for Django Finance.

This module provides:
- Base exception classes for domain and application errors
- DRF custom exception handler with standardized error format
- Error response formatting utilities
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.response import Response
from rest_framework.views import exception_handler

if TYPE_CHECKING:
    from rest_framework.views import Request


# =============================================================================
# Domain Exceptions
# =============================================================================


class DomainError(Exception):
    """Base class for domain layer errors.

    Domain errors represent business rule violations or invalid states
    within the domain model.
    """

    def __init__(self, message: str, code: str = "DOMAIN_ERROR") -> None:
        """Initialize domain error.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
        """
        self.message = message
        self.code = code
        super().__init__(message)


class EntityNotFoundError(DomainError):
    """Requested entity was not found."""

    def __init__(
        self, entity_type: str, entity_id: str, message: str | None = None
    ) -> None:
        """Initialize entity not found error.

        Args:
            entity_type: Type of entity that was not found.
            entity_id: ID of the entity that was not found.
            message: Optional custom message.
        """
        self.entity_type = entity_type
        self.entity_id = entity_id
        super().__init__(
            message or f"{entity_type} with id '{entity_id}' not found",
            code="NOT_FOUND",
        )


class DomainValidationError(DomainError):
    """Domain validation failed."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize validation error.

        Args:
            message: Human-readable error message.
            field: Field that failed validation (if applicable).
            details: List of field-level error details.
        """
        self.field = field
        self.details = details or []
        super().__init__(message, code="VALIDATION_ERROR")


class ConflictError(DomainError):
    """Operation conflicts with current state."""

    def __init__(self, message: str) -> None:
        """Initialize conflict error.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, code="CONFLICT")


class AuthorizationError(DomainError):
    """User is not authorized for this action."""

    def __init__(self, message: str = "Not authorized for this action") -> None:
        """Initialize authorization error.

        Args:
            message: Human-readable error message.
        """
        super().__init__(message, code="FORBIDDEN")


# =============================================================================
# Application Exceptions
# =============================================================================


class ApplicationError(Exception):
    """Base class for application layer errors.

    Application errors represent failures in use case execution,
    external service failures, or infrastructure problems.
    """

    def __init__(self, message: str, code: str = "APPLICATION_ERROR") -> None:
        """Initialize application error.

        Args:
            message: Human-readable error message.
            code: Machine-readable error code.
        """
        self.message = message
        self.code = code
        super().__init__(message)


class ExternalServiceError(ApplicationError):
    """External service call failed."""

    def __init__(
        self, service: str, message: str, original_error: Exception | None = None
    ) -> None:
        """Initialize external service error.

        Args:
            service: Name of the external service.
            message: Human-readable error message.
            original_error: Original exception if any.
        """
        self.service = service
        self.original_error = original_error
        super().__init__(f"{service}: {message}", code="EXTERNAL_SERVICE_ERROR")


# =============================================================================
# API Exceptions
# =============================================================================


class APIValidationError(APIException):
    """API validation error with standardized format."""

    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "VALIDATION_ERROR"
    default_detail = "Validation failed"

    def __init__(
        self,
        detail: str | None = None,
        field_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        """Initialize API validation error.

        Args:
            detail: Human-readable error message.
            field_errors: List of field-level error details.
        """
        self.field_errors = field_errors or []
        super().__init__(detail=detail or self.default_detail)


class TenantAccessError(APIException):
    """Tenant access violation."""

    status_code = status.HTTP_403_FORBIDDEN
    default_code = "TENANT_ACCESS_DENIED"
    default_detail = "Access denied for this tenant"


# =============================================================================
# Exception Handler
# =============================================================================


def format_error_response(
    code: str,
    message: str,
    details: list[dict[str, Any]] | None = None,
    correlation_id: str | None = None,
) -> dict[str, Any]:
    """Format error response in standardized format.

    Args:
        code: Machine-readable error code.
        message: Human-readable error message.
        details: List of field-level error details.
        correlation_id: Request correlation ID for support.

    Returns:
        Standardized error response dictionary.
    """
    error: dict[str, Any] = {
        "code": code,
        "message": message,
    }
    if details:
        error["details"] = details
    if correlation_id:
        error["correlation_id"] = correlation_id

    return {"error": error}


def custom_exception_handler(
    exc: Exception, context: dict[str, Any]
) -> Response | None:
    """Custom exception handler for DRF.

    Converts exceptions to standardized error response format.

    Args:
        exc: The exception that was raised.
        context: Context dictionary with view information.

    Returns:
        Response with standardized error format, or None to use default handler.
    """
    from shared.middleware import get_correlation_id

    correlation_id = get_correlation_id()

    # Handle domain exceptions
    if isinstance(exc, EntityNotFoundError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, DomainValidationError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                details=exc.details,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ConflictError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, AuthorizationError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, DomainError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Handle application exceptions
    if isinstance(exc, ExternalServiceError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    if isinstance(exc, ApplicationError):
        return Response(
            format_error_response(
                code=exc.code,
                message=exc.message,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Handle Django exceptions
    if isinstance(exc, Http404):
        return Response(
            format_error_response(
                code="NOT_FOUND",
                message=str(exc) or "Resource not found",
                correlation_id=correlation_id,
            ),
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, PermissionDenied):
        return Response(
            format_error_response(
                code="FORBIDDEN",
                message=str(exc) or "Permission denied",
                correlation_id=correlation_id,
            ),
            status=status.HTTP_403_FORBIDDEN,
        )

    if isinstance(exc, ValidationError):
        details = []
        if hasattr(exc, "message_dict"):
            for field, messages in exc.message_dict.items():
                for msg in messages:
                    details.append({"field": field, "message": msg})
        return Response(
            format_error_response(
                code="VALIDATION_ERROR",
                message="Validation failed",
                details=details,
                correlation_id=correlation_id,
            ),
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Handle API exceptions with custom format
    if isinstance(exc, APIValidationError):
        return Response(
            format_error_response(
                code=exc.default_code,
                message=str(exc.detail),
                details=exc.field_errors,
                correlation_id=correlation_id,
            ),
            status=exc.status_code,
        )

    # Call default handler for other DRF exceptions
    response = exception_handler(exc, context)

    if response is not None:
        # Convert DRF error format to our standardized format
        code = getattr(exc, "default_code", "API_ERROR")
        if isinstance(code, str):
            code = code.upper()
        else:
            code = "API_ERROR"

        message = str(exc.detail) if hasattr(exc, "detail") else str(exc)

        response.data = format_error_response(
            code=code,
            message=message,
            correlation_id=correlation_id,
        )

    return response
