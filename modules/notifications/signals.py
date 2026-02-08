"""Django signals for triggering notifications.

Listens to model events from finance and social modules
and creates appropriate notifications.
"""

from __future__ import annotations

from decimal import Decimal

from django.db.models.signals import post_save
from django.dispatch import receiver

import structlog

logger = structlog.get_logger()


# =============================================================================
# Finance Module Signals
# =============================================================================

@receiver(post_save, sender="finance.Transaction")
def notify_transaction_created(sender, instance, created, **kwargs):
    """Notify user when a transaction is created."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    # Get account name
    account_name = instance.account.name if instance.account else "Unknown Account"

    # Format amount
    amount = f"{instance.currency_code} {instance.amount:,.2f}"

    # Determine transaction type display
    tx_type = "credit" if instance.transaction_type == "credit" else "debit"

    create_notification.delay(
        user_id=str(instance.tenant_id),  # tenant_id is the user_id
        tenant_id=str(instance.tenant_id),
        notification_type="finance.transaction_created",
        title="Transaction Recorded",
        message=f"A {tx_type} of {amount} was recorded in {account_name}.",
        data={
            "transaction_id": str(instance.id),
            "transaction_type": tx_type,
            "amount": str(instance.amount),
            "currency_code": instance.currency_code,
            "account_name": account_name,
            "account_id": str(instance.account_id) if instance.account_id else None,
        },
        action_url=f"/transactions/{instance.id}/",
        send_email=False,  # Don't email for every transaction
    )

    logger.debug(
        "transaction_notification_triggered",
        transaction_id=str(instance.id),
        tenant_id=str(instance.tenant_id),
    )


@receiver(post_save, sender="finance.Transfer")
def notify_transfer_completed(sender, instance, created, **kwargs):
    """Notify user when a transfer is completed."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    # Get account names
    from_name = instance.from_account.name if instance.from_account else "Unknown"
    to_name = instance.to_account.name if instance.to_account else "Unknown"
    amount = f"{instance.currency_code} {instance.amount:,.2f}"

    create_notification.delay(
        user_id=str(instance.tenant_id),
        tenant_id=str(instance.tenant_id),
        notification_type="finance.transfer_completed",
        title="Transfer Completed",
        message=f"Transfer of {amount} from {from_name} to {to_name} completed.",
        data={
            "transfer_id": str(instance.id),
            "from_account": from_name,
            "to_account": to_name,
            "amount": str(instance.amount),
            "currency_code": instance.currency_code,
        },
        send_email=False,
    )


@receiver(post_save, sender="finance.Account")
def notify_account_created(sender, instance, created, **kwargs):
    """Notify user when an account is created."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    create_notification.delay(
        user_id=str(instance.tenant_id),
        tenant_id=str(instance.tenant_id),
        notification_type="finance.account_created",
        title="Account Created",
        message=f"Your new account '{instance.name}' has been created.",
        data={
            "account_id": str(instance.id),
            "account_name": instance.name,
            "account_type": instance.account_type,
            "currency_code": instance.currency_code,
        },
        action_url=f"/accounts/{instance.id}/",
        send_email=False,
    )


# =============================================================================
# Social Module Signals
# =============================================================================

@receiver(post_save, sender="social.PeerDebt")
def notify_debt_created(sender, instance, created, **kwargs):
    """Notify user when a debt is created."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    # Get contact name
    contact_name = instance.contact.name if instance.contact else "Someone"
    amount = f"{instance.currency_code} {instance.amount:,.2f}"

    # Determine direction text
    if instance.direction == "lent":
        direction_text = "owes"
        message = f"{contact_name} {direction_text} you {amount}."
    else:
        direction_text = "lent"
        message = f"You owe {contact_name} {amount}."

    create_notification.delay(
        user_id=str(instance.tenant_id),
        tenant_id=str(instance.tenant_id),
        notification_type="social.debt_created",
        title="New Debt Recorded",
        message=message,
        data={
            "debt_id": str(instance.id),
            "contact_name": contact_name,
            "contact_id": str(instance.contact_id) if instance.contact_id else None,
            "direction": instance.direction,
            "amount": str(instance.amount),
            "currency_code": instance.currency_code,
        },
        action_url=f"/debts/{instance.id}/",
        send_email=True,  # Email for debts
    )


@receiver(post_save, sender="social.Settlement")
def notify_settlement_created(sender, instance, created, **kwargs):
    """Notify user when a settlement is recorded."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    # Get contact names
    from_name = instance.from_contact.name if instance.from_contact else "Someone"
    to_name = instance.to_contact.name if instance.to_contact else "Someone"
    amount = f"{instance.currency_code} {instance.amount:,.2f}"

    # Determine if user is receiving or paying
    # This is simplified - in reality you'd check against the owner
    message = f"Settlement of {amount} recorded between {from_name} and {to_name}."

    create_notification.delay(
        user_id=str(instance.tenant_id),
        tenant_id=str(instance.tenant_id),
        notification_type="social.settlement_received",
        title="Settlement Recorded",
        message=message,
        data={
            "settlement_id": str(instance.id),
            "from_contact": from_name,
            "to_contact": to_name,
            "amount": str(instance.amount),
            "currency_code": instance.currency_code,
        },
        action_url=f"/settlements/",
        send_email=True,
    )


@receiver(post_save, sender="social.GroupExpense")
def notify_expense_added(sender, instance, created, **kwargs):
    """Notify user when a group expense is added."""
    if not created:
        return

    from modules.notifications.tasks import create_notification

    # Get group and payer names
    group_name = instance.group.name if instance.group else "Unknown Group"
    payer_name = instance.paid_by.name if instance.paid_by else "Someone"
    amount = f"{instance.currency_code} {instance.total_amount:,.2f}"

    create_notification.delay(
        user_id=str(instance.tenant_id),
        tenant_id=str(instance.tenant_id),
        notification_type="social.expense_added",
        title="New Group Expense",
        message=f"{payer_name} added '{instance.description}' ({amount}) to {group_name}.",
        data={
            "expense_id": str(instance.id),
            "group_id": str(instance.group_id) if instance.group_id else None,
            "group_name": group_name,
            "payer_name": payer_name,
            "description": instance.description,
            "amount": str(instance.total_amount),
            "currency_code": instance.currency_code,
        },
        action_url=f"/groups/{instance.group_id}/" if instance.group_id else "/groups/",
        send_email=True,
    )


@receiver(post_save, sender="social.Contact")
def notify_contact_created(sender, instance, created, **kwargs):
    """Log contact creation (no notification needed)."""
    if created:
        logger.debug(
            "contact_created",
            contact_id=str(instance.id),
            tenant_id=str(instance.tenant_id),
        )


# =============================================================================
# Subscription Module Signals
# =============================================================================

@receiver(post_save, sender="subscriptions.Subscription")
def notify_subscription_changed(sender, instance, created, **kwargs):
    """Notify user when subscription changes."""
    from modules.notifications.tasks import create_notification

    if created:
        title = "Welcome to Django Finance!"
        message = f"Your {instance.tier.name} subscription is now active."
    else:
        title = "Subscription Updated"
        message = f"Your subscription has been updated to {instance.tier.name}."

    create_notification.delay(
        user_id=str(instance.user_id),
        tenant_id=str(instance.tenant_id),
        notification_type="account.subscription_changed",
        title=title,
        message=message,
        data={
            "subscription_id": str(instance.id),
            "tier_name": instance.tier.name if instance.tier else "Unknown",
            "status": instance.status,
        },
        send_email=True,
    )
