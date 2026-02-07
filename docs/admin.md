# Django Finance Admin Guide

This document describes the Django Admin interface for the Django Finance platform.

## Overview

The admin interface provides comprehensive management capabilities for:
- **User Management**: Create, update, and manage user accounts
- **Financial Entities**: Accounts, transactions, transfers, assets, liabilities, loans
- **Social Finance**: Contacts, peer debts, expense groups, settlements
- **Audit & Security**: Token management, audit log visibility

## Accessing the Admin

The admin interface is available at `/admin/`.

### Access Levels

| Role | Access Level |
|------|-------------|
| SuperAdmin | Full access to all tenants and features |
| Staff User | Limited access to their tenant only |
| Regular User | No admin access |

## Features

### Custom Branding

The admin includes custom branding with:
- Finance-themed color scheme
- Dashboard widgets with quick stats
- Quick action links

### Enhanced Dashboard

The admin dashboard (`/admin/`) provides:
- Total user count
- Active session count
- System health status
- Quick links to common actions

Access detailed statistics at `/admin/dashboard/stats/`.

### Tenant Scoping

All data is automatically scoped by tenant:
- SuperAdmins see all data across tenants
- Staff users only see their tenant's data
- Data is automatically assigned to the correct tenant on creation

## Module Admin Features

### Accounts Module

#### User Management

**List View:**
- Email, name, role, status, verification status
- Lock status with visual indicators
- Last login timestamp
- Date-based filtering and search

**Actions:**
- Activate/Suspend users
- Verify email addresses
- Unlock accounts
- Upgrade/Revoke Premium status
- Export as CSV

#### Token Management

- Email Verification Tokens: View and clean up expired tokens
- Password Reset Tokens: View and clean up expired tokens
- Refresh Token Blacklist: View blacklisted tokens and clean up expired

### Finance Module

#### Accounts

**List View:**
- Account name, type, currency, status
- Institution information
- Net worth inclusion toggle
- Inline display of recent transactions

**Actions:**
- Activate/Close accounts
- Include/Exclude from net worth
- Export as CSV

#### Transactions

**List View:**
- Date, account, type (credit/debit with visual indicators)
- Amount with color coding
- Status badges (pending/posted/voided)
- Category and description

**Actions:**
- Post transactions
- Void transactions
- Mark as pending
- Export as CSV

#### Assets & Liabilities

- Visual gain/loss display for assets
- Interest rate display for liabilities
- Progress bars for loan repayment

**Actions:**
- Include/Exclude from net worth
- Mark loans as paid off
- Export as CSV

### Social Module

#### Contacts

**List View:**
- Name, email, phone, status
- Share status with linked user
- Debt balance summary (inline calculation)
- Inline view of recent debts

**Actions:**
- Activate/Deactivate contacts
- Export as CSV

#### Peer Debts

**List View:**
- Contact with link
- Direction (lent/borrowed) with visual indicators
- Amount, settled amount, remaining amount
- Status badges and due date warnings (overdue)

**Actions:**
- Mark as fully settled
- Mark as partially paid (50%)
- Reset to pending
- Export as CSV

#### Expense Groups & Group Expenses

**List View:**
- Group name, member count
- Total expenses and amounts
- Split method and status

**Actions:**
- Mark all splits as settled
- Inline split editing
- Export as CSV

#### Settlements

**List View:**
- From → To visual display
- Amount with currency
- Payment method badges
- Linked items count

## Bulk Actions

All models support bulk actions:
- **Export as CSV**: Download selected items as CSV file
- **Model-specific actions**: See individual module sections above

## Audit Logging

Admin actions are automatically logged to the audit system.

### Logged Events
- Object creation
- Object updates (with before/after values)
- Object deletion
- Data exports

### Viewing Audit Logs

Access the audit log information at `/admin/audit-logs/`.

Audit logs are stored using structured logging (structlog). To view:

```bash
# From log files
grep "audit_event" /var/log/django-finance/app.log | jq .

# From centralized logging
event: "audit_event" AND category: "admin"
```

### Retention Policies
- Financial operations: 7 years
- Security operations: 2 years
- Admin operations: 7 years

## Security Best Practices

1. **Use Strong Passwords**: All admin users should use strong, unique passwords
2. **Limit Staff Access**: Only grant staff access when necessary
3. **Review Permissions**: Regularly audit user permissions
4. **Monitor Audit Logs**: Review audit logs for unusual activity
5. **Clean Up Tokens**: Regularly clean up expired tokens

## Customization

### Adding Custom Actions

```python
@admin.action(description="My custom action")
def my_action(modeladmin, request, queryset):
    # Your action logic
    count = queryset.update(status="active")
    modeladmin.message_user(request, f"Updated {count} items.")
```

### Adding Inline Editors

```python
class RelatedInline(admin.TabularInline):
    model = RelatedModel
    extra = 0
    readonly_fields = ["field1", "field2"]
```

### Custom Display Methods

```python
@admin.display(description="Status")
def status_badge(self, obj):
    color = "#10b981" if obj.is_active else "#ef4444"
    return format_html(
        '<span style="color: {};">{}</span>',
        color,
        obj.status,
    )
```

## Troubleshooting

### Cannot See Data
- Verify you have staff or superuser status
- Check tenant assignment for non-superusers
- Ensure model has proper `tenant_id` field

### Actions Not Appearing
- Verify action is registered in admin class
- Check user permissions for the action
- Ensure action is not filtered by list_filter

### Export Issues
- Large exports may timeout; use filters to reduce selection
- Check CSV encoding for special characters

## API Reference

### Base Classes

| Class | Description |
|-------|-------------|
| `TenantScopedAdmin` | Base class with tenant filtering |
| `AuditLogMixin` | Mixin for audit logging |
| `ExportMixin` | Mixin for CSV export action |
| `ReadOnlyAdminMixin` | Mixin for read-only views |
| `SoftDeleteMixin` | Mixin for soft delete/restore |

### Usage

```python
from shared.admin import TenantScopedAdmin, AuditLogMixin, ExportMixin

@admin.register(MyModel)
class MyModelAdmin(TenantScopedAdmin, AuditLogMixin, ExportMixin):
    list_display = ["field1", "field2"]
    # ...
```
