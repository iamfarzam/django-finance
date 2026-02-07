"""Shared utilities and base classes for Django Finance.

This package contains:
- Base models (BaseModel, TenantModel, SoftDeleteModel)
- Custom middleware (Correlation ID, Tenant Context)
- Base exceptions and error handling
- Utility functions and helpers
"""

default_app_config = "shared.apps.SharedConfig"
