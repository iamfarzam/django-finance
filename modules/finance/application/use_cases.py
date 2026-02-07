"""Use cases for the finance module.

Use cases orchestrate domain entities and services to perform
specific business operations. They are the entry points for
application logic.
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING

from modules.finance.application.dto import (
    AccountDTO,
    AssetDTO,
    BalanceDTO,
    CategoryDTO,
    CreateAccountCommand,
    CreateAssetCommand,
    CreateCategoryCommand,
    CreateLiabilityCommand,
    CreateLoanCommand,
    CreateTransactionCommand,
    CreateTransferCommand,
    LiabilityDTO,
    LoanDTO,
    NetWorthDTO,
    RecordLiabilityPaymentCommand,
    RecordLoanPaymentCommand,
    TransactionDTO,
    TransferDTO,
    UpdateAssetValueCommand,
)
from modules.finance.domain.entities import (
    Account,
    Asset,
    Category,
    Liability,
    Loan,
    Transaction,
    Transfer,
)
from modules.finance.domain.enums import (
    AccountStatus,
    AccountType,
    AssetType,
    LiabilityType,
    LoanStatus,
    PaymentFrequency,
    TransactionType,
)
from modules.finance.domain.events import (
    AccountClosed,
    AccountCreated,
    AssetCreated,
    AssetValueUpdated,
    CategoryCreated,
    LiabilityCreated,
    LiabilityPaymentRecorded,
    LoanCreated,
    LoanPaidOff,
    LoanPaymentRecorded,
    TransactionCreated,
    TransactionPosted,
    TransferCompleted,
    TransferCreated,
)
from modules.finance.domain.exceptions import (
    AccountClosedError,
    AccountLimitExceededError,
    AccountNotFoundError,
    AssetNotFoundError,
    CategoryNotFoundError,
    IdempotencyKeyExistsError,
    LiabilityNotFoundError,
    LoanAlreadyPaidOffError,
    LoanNotFoundError,
    TransactionNotFoundError,
    TransferSameAccountError,
)
from modules.finance.domain.services import (
    AccountLimitChecker,
    BalanceCalculator,
    NetWorthCalculator,
)

if TYPE_CHECKING:
    from uuid import UUID

    from modules.finance.application.interfaces import (
        AccountRepository,
        AssetRepository,
        BalanceCache,
        CategoryRepository,
        EventPublisher,
        IdempotencyRepository,
        LiabilityRepository,
        LoanRepository,
        TransactionRepository,
        TransferRepository,
    )


def _utc_now() -> datetime:
    """Return current UTC datetime."""
    return datetime.now(timezone.utc)


# =============================================================================
# Account Use Cases
# =============================================================================


class CreateAccount:
    """Use case for creating a new account."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._event_publisher = event_publisher

    async def execute(
        self, command: CreateAccountCommand, user_role: str = "user"
    ) -> AccountDTO:
        """Create a new account.

        Args:
            command: Account creation command.
            user_role: Role of the user creating the account.

        Returns:
            Created account DTO.

        Raises:
            AccountLimitExceededError: If user exceeds account limit.
        """
        # Check account limit
        current_count = await self._account_repo.count(command.tenant_id)
        can_create, limit = AccountLimitChecker.check_limit(user_role, current_count)

        if not can_create:
            raise AccountLimitExceededError(limit, current_count)

        # Create account entity
        account = Account.create(
            tenant_id=command.tenant_id,
            name=command.name,
            account_type=AccountType(command.account_type),
            currency_code=command.currency_code,
            institution=command.institution,
            account_number_masked=command.account_number_masked,
            notes=command.notes,
        )

        # Save account
        saved_account = await self._account_repo.save(account)

        # Create initial balance transaction if provided
        if command.initial_balance and command.initial_balance != Decimal("0"):
            tx_type = (
                TransactionType.CREDIT
                if command.initial_balance > 0
                else TransactionType.DEBIT
            )
            initial_tx = Transaction(
                id=Transaction.create_credit(
                    tenant_id=command.tenant_id,
                    account_id=saved_account.id,
                    amount=abs(command.initial_balance),
                    currency_code=command.currency_code,
                    description="Initial balance",
                ).id,
                tenant_id=command.tenant_id,
                account_id=saved_account.id,
                transaction_type=tx_type,
                amount=abs(command.initial_balance),
                currency_code=command.currency_code,
                description="Initial balance",
            )
            initial_tx.post()
            await self._transaction_repo.save(initial_tx)

        # Publish event
        await self._event_publisher.publish(
            AccountCreated(
                tenant_id=saved_account.tenant_id,
                account_id=saved_account.id,
                name=saved_account.name,
                account_type=saved_account.account_type.value,
                currency_code=saved_account.currency_code,
            )
        )

        return self._to_dto(saved_account)

    def _to_dto(self, account: Account, balance: Decimal | None = None) -> AccountDTO:
        """Convert account entity to DTO."""
        return AccountDTO(
            id=account.id,
            tenant_id=account.tenant_id,
            name=account.name,
            account_type=account.account_type.value,
            currency_code=account.currency_code,
            status=account.status.value,
            institution=account.institution,
            account_number_masked=account.account_number_masked,
            notes=account.notes,
            is_included_in_net_worth=account.is_included_in_net_worth,
            display_order=account.display_order,
            created_at=account.created_at,
            updated_at=account.updated_at,
            balance=balance,
        )


class GetAccountBalance:
    """Use case for getting an account's balance."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        balance_cache: BalanceCache | None = None,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._balance_cache = balance_cache

    async def execute(self, account_id: UUID, tenant_id: UUID) -> BalanceDTO:
        """Get balance for an account.

        Args:
            account_id: The account ID.
            tenant_id: The tenant ID.

        Returns:
            Balance DTO.

        Raises:
            AccountNotFoundError: If account not found.
        """
        # Get account
        account = await self._account_repo.get_by_id(account_id, tenant_id)
        if not account:
            raise AccountNotFoundError(account_id)

        # Try cache first
        if self._balance_cache:
            cached = await self._balance_cache.get(account_id)
            if cached is not None:
                return BalanceDTO(
                    account_id=account_id,
                    balance=cached,
                    total_credits=Decimal("0"),
                    total_debits=Decimal("0"),
                    transaction_count=0,
                    currency_code=account.currency_code,
                )

        # Calculate from transactions
        transactions = await self._transaction_repo.get_by_account(
            account_id, tenant_id
        )
        result = BalanceCalculator.calculate(transactions, account.currency_code)

        # Cache result
        if self._balance_cache:
            await self._balance_cache.set(account_id, result.balance.amount)

        return BalanceDTO(
            account_id=account_id,
            balance=result.balance.amount,
            total_credits=result.total_credits.amount,
            total_debits=result.total_debits.amount,
            transaction_count=result.transaction_count,
            currency_code=account.currency_code,
            as_of_date=result.as_of_date,
        )


class CloseAccount:
    """Use case for closing an account."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._event_publisher = event_publisher

    async def execute(self, account_id: UUID, tenant_id: UUID) -> AccountDTO:
        """Close an account.

        Args:
            account_id: The account ID.
            tenant_id: The tenant ID.

        Returns:
            Updated account DTO.

        Raises:
            AccountNotFoundError: If account not found.
        """
        account = await self._account_repo.get_by_id(account_id, tenant_id)
        if not account:
            raise AccountNotFoundError(account_id)

        # Get final balance
        transactions = await self._transaction_repo.get_by_account(
            account_id, tenant_id
        )
        balance = BalanceCalculator.calculate(transactions, account.currency_code)

        # Close account
        account.close()
        saved = await self._account_repo.save(account)

        # Publish event
        await self._event_publisher.publish(
            AccountClosed(
                tenant_id=tenant_id,
                account_id=account_id,
                final_balance=str(balance.balance.amount),
            )
        )

        return AccountDTO(
            id=saved.id,
            tenant_id=saved.tenant_id,
            name=saved.name,
            account_type=saved.account_type.value,
            currency_code=saved.currency_code,
            status=saved.status.value,
            institution=saved.institution,
            account_number_masked=saved.account_number_masked,
            notes=saved.notes,
            is_included_in_net_worth=saved.is_included_in_net_worth,
            display_order=saved.display_order,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            balance=balance.balance.amount,
        )


# =============================================================================
# Transaction Use Cases
# =============================================================================


class CreateTransaction:
    """Use case for creating a new transaction."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        idempotency_repository: IdempotencyRepository,
        balance_cache: BalanceCache | None,
        event_publisher: EventPublisher,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._idempotency_repo = idempotency_repository
        self._balance_cache = balance_cache
        self._event_publisher = event_publisher

    async def execute(self, command: CreateTransactionCommand) -> TransactionDTO:
        """Create a new transaction.

        Args:
            command: Transaction creation command.

        Returns:
            Created transaction DTO.

        Raises:
            AccountNotFoundError: If account not found.
            AccountClosedError: If account is closed.
            IdempotencyKeyExistsError: If idempotency key already used.
        """
        # Check idempotency
        if command.idempotency_key:
            existing = await self._transaction_repo.get_by_idempotency_key(
                command.idempotency_key, command.tenant_id
            )
            if existing:
                return self._to_dto(existing)

        # Get and validate account
        account = await self._account_repo.get_by_id(
            command.account_id, command.tenant_id
        )
        if not account:
            raise AccountNotFoundError(command.account_id)
        if account.is_closed:
            raise AccountClosedError(command.account_id)

        # Create transaction
        tx_type = TransactionType(command.transaction_type)
        if tx_type == TransactionType.CREDIT:
            transaction = Transaction.create_credit(
                tenant_id=command.tenant_id,
                account_id=command.account_id,
                amount=command.amount,
                currency_code=command.currency_code,
                description=command.description,
                transaction_date=command.transaction_date,
                category_id=command.category_id,
                reference_number=command.reference_number,
                notes=command.notes,
                idempotency_key=command.idempotency_key,
            )
        else:
            transaction = Transaction.create_debit(
                tenant_id=command.tenant_id,
                account_id=command.account_id,
                amount=command.amount,
                currency_code=command.currency_code,
                description=command.description,
                transaction_date=command.transaction_date,
                category_id=command.category_id,
                reference_number=command.reference_number,
                notes=command.notes,
                idempotency_key=command.idempotency_key,
            )

        # Auto-post if requested
        if command.auto_post:
            transaction.post()

        # Save transaction
        saved = await self._transaction_repo.save(transaction)

        # Save idempotency key
        if command.idempotency_key:
            await self._idempotency_repo.save(
                command.idempotency_key,
                command.tenant_id,
                saved.id,
                "transaction",
            )

        # Invalidate balance cache
        if self._balance_cache:
            await self._balance_cache.invalidate(command.account_id)

        # Publish events
        await self._event_publisher.publish(
            TransactionCreated(
                tenant_id=saved.tenant_id,
                transaction_id=saved.id,
                account_id=saved.account_id,
                transaction_type=saved.transaction_type.value,
                amount=str(saved.amount),
                currency_code=saved.currency_code,
                description=saved.description,
                category_id=saved.category_id,
            )
        )

        if saved.is_posted:
            # Get new balance for event
            transactions = await self._transaction_repo.get_by_account(
                command.account_id, command.tenant_id
            )
            balance = BalanceCalculator.calculate(transactions, account.currency_code)

            await self._event_publisher.publish(
                TransactionPosted(
                    tenant_id=saved.tenant_id,
                    transaction_id=saved.id,
                    account_id=saved.account_id,
                    amount=str(saved.amount),
                    new_balance=str(balance.balance.amount),
                )
            )

        return self._to_dto(saved)

    def _to_dto(self, tx: Transaction) -> TransactionDTO:
        """Convert transaction entity to DTO."""
        return TransactionDTO(
            id=tx.id,
            tenant_id=tx.tenant_id,
            account_id=tx.account_id,
            transaction_type=tx.transaction_type.value,
            amount=tx.amount,
            currency_code=tx.currency_code,
            status=tx.status.value,
            transaction_date=tx.transaction_date,
            posted_at=tx.posted_at,
            description=tx.description,
            category_id=tx.category_id,
            category_name=None,
            reference_number=tx.reference_number,
            notes=tx.notes,
            is_adjustment=tx.is_adjustment,
            adjustment_for_id=tx.adjustment_for_id,
            created_at=tx.created_at,
            updated_at=tx.updated_at,
            signed_amount=tx.signed_amount,
        )


# =============================================================================
# Transfer Use Cases
# =============================================================================


class CreateTransfer:
    """Use case for creating a transfer between accounts."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        transfer_repository: TransferRepository,
        balance_cache: BalanceCache | None,
        event_publisher: EventPublisher,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._transfer_repo = transfer_repository
        self._balance_cache = balance_cache
        self._event_publisher = event_publisher

    async def execute(self, command: CreateTransferCommand) -> TransferDTO:
        """Create a transfer between accounts.

        Args:
            command: Transfer creation command.

        Returns:
            Created transfer DTO.

        Raises:
            AccountNotFoundError: If an account is not found.
            AccountClosedError: If an account is closed.
            TransferSameAccountError: If source and destination are the same.
        """
        if command.from_account_id == command.to_account_id:
            raise TransferSameAccountError(command.from_account_id)

        # Validate both accounts
        from_account = await self._account_repo.get_by_id(
            command.from_account_id, command.tenant_id
        )
        if not from_account:
            raise AccountNotFoundError(command.from_account_id)
        if from_account.is_closed:
            raise AccountClosedError(command.from_account_id)

        to_account = await self._account_repo.get_by_id(
            command.to_account_id, command.tenant_id
        )
        if not to_account:
            raise AccountNotFoundError(command.to_account_id)
        if to_account.is_closed:
            raise AccountClosedError(command.to_account_id)

        # Create transfer
        transfer = Transfer.create(
            tenant_id=command.tenant_id,
            from_account_id=command.from_account_id,
            to_account_id=command.to_account_id,
            amount=command.amount,
            currency_code=command.currency_code,
            transfer_date=command.transfer_date,
            description=command.description or "Transfer",
            notes=command.notes,
        )

        # Create linked transactions
        debit, credit = transfer.create_transactions()
        debit.post()
        credit.post()

        # Save all
        saved_debit = await self._transaction_repo.save(debit)
        saved_credit = await self._transaction_repo.save(credit)

        transfer.from_transaction_id = saved_debit.id
        transfer.to_transaction_id = saved_credit.id
        saved_transfer = await self._transfer_repo.save(transfer)

        # Invalidate caches
        if self._balance_cache:
            await self._balance_cache.invalidate(command.from_account_id)
            await self._balance_cache.invalidate(command.to_account_id)

        # Publish events
        await self._event_publisher.publish(
            TransferCreated(
                tenant_id=saved_transfer.tenant_id,
                transfer_id=saved_transfer.id,
                from_account_id=saved_transfer.from_account_id,
                to_account_id=saved_transfer.to_account_id,
                amount=str(saved_transfer.amount),
                currency_code=saved_transfer.currency_code,
            )
        )
        await self._event_publisher.publish(
            TransferCompleted(
                tenant_id=saved_transfer.tenant_id,
                transfer_id=saved_transfer.id,
                from_transaction_id=saved_debit.id,
                to_transaction_id=saved_credit.id,
            )
        )

        return TransferDTO(
            id=saved_transfer.id,
            tenant_id=saved_transfer.tenant_id,
            from_account_id=saved_transfer.from_account_id,
            to_account_id=saved_transfer.to_account_id,
            amount=saved_transfer.amount,
            currency_code=saved_transfer.currency_code,
            from_transaction_id=saved_transfer.from_transaction_id,
            to_transaction_id=saved_transfer.to_transaction_id,
            transfer_date=saved_transfer.transfer_date,
            description=saved_transfer.description,
            notes=saved_transfer.notes,
            created_at=saved_transfer.created_at,
        )


# =============================================================================
# Asset Use Cases
# =============================================================================


class CreateAsset:
    """Use case for creating a new asset."""

    def __init__(
        self,
        asset_repository: AssetRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._asset_repo = asset_repository
        self._event_publisher = event_publisher

    async def execute(self, command: CreateAssetCommand) -> AssetDTO:
        """Create a new asset."""
        asset = Asset.create(
            tenant_id=command.tenant_id,
            name=command.name,
            asset_type=AssetType(command.asset_type),
            current_value=command.current_value,
            currency_code=command.currency_code,
            purchase_date=command.purchase_date,
            purchase_price=command.purchase_price,
            description=command.description,
            notes=command.notes,
        )

        saved = await self._asset_repo.save(asset)

        await self._event_publisher.publish(
            AssetCreated(
                tenant_id=saved.tenant_id,
                asset_id=saved.id,
                name=saved.name,
                asset_type=saved.asset_type.value,
                current_value=str(saved.current_value),
                currency_code=saved.currency_code,
            )
        )

        return self._to_dto(saved)

    def _to_dto(self, asset: Asset) -> AssetDTO:
        """Convert asset entity to DTO."""
        gain_loss = asset.gain_loss
        return AssetDTO(
            id=asset.id,
            tenant_id=asset.tenant_id,
            name=asset.name,
            asset_type=asset.asset_type.value,
            current_value=asset.current_value,
            currency_code=asset.currency_code,
            purchase_date=asset.purchase_date,
            purchase_price=asset.purchase_price,
            description=asset.description,
            notes=asset.notes,
            is_included_in_net_worth=asset.is_included_in_net_worth,
            created_at=asset.created_at,
            updated_at=asset.updated_at,
            gain_loss=gain_loss.amount if gain_loss else None,
        )


class UpdateAssetValue:
    """Use case for updating an asset's value."""

    def __init__(
        self,
        asset_repository: AssetRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._asset_repo = asset_repository
        self._event_publisher = event_publisher

    async def execute(self, command: UpdateAssetValueCommand) -> AssetDTO:
        """Update an asset's current value."""
        asset = await self._asset_repo.get_by_id(command.asset_id, command.tenant_id)
        if not asset:
            raise AssetNotFoundError(command.asset_id)

        old_value = asset.current_value
        asset.update_value(command.new_value)
        saved = await self._asset_repo.save(asset)

        await self._event_publisher.publish(
            AssetValueUpdated(
                tenant_id=saved.tenant_id,
                asset_id=saved.id,
                old_value=str(old_value),
                new_value=str(saved.current_value),
                currency_code=saved.currency_code,
            )
        )

        gain_loss = saved.gain_loss
        return AssetDTO(
            id=saved.id,
            tenant_id=saved.tenant_id,
            name=saved.name,
            asset_type=saved.asset_type.value,
            current_value=saved.current_value,
            currency_code=saved.currency_code,
            purchase_date=saved.purchase_date,
            purchase_price=saved.purchase_price,
            description=saved.description,
            notes=saved.notes,
            is_included_in_net_worth=saved.is_included_in_net_worth,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            gain_loss=gain_loss.amount if gain_loss else None,
        )


# =============================================================================
# Liability Use Cases
# =============================================================================


class CreateLiability:
    """Use case for creating a new liability."""

    def __init__(
        self,
        liability_repository: LiabilityRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._liability_repo = liability_repository
        self._event_publisher = event_publisher

    async def execute(self, command: CreateLiabilityCommand) -> LiabilityDTO:
        """Create a new liability."""
        liability = Liability.create(
            tenant_id=command.tenant_id,
            name=command.name,
            liability_type=LiabilityType(command.liability_type),
            current_balance=command.current_balance,
            currency_code=command.currency_code,
            interest_rate=command.interest_rate,
            minimum_payment=command.minimum_payment,
            due_day=command.due_day,
            creditor=command.creditor,
            account_number_masked=command.account_number_masked,
            notes=command.notes,
        )

        saved = await self._liability_repo.save(liability)

        await self._event_publisher.publish(
            LiabilityCreated(
                tenant_id=saved.tenant_id,
                liability_id=saved.id,
                name=saved.name,
                liability_type=saved.liability_type.value,
                current_balance=str(saved.current_balance),
                currency_code=saved.currency_code,
            )
        )

        return self._to_dto(saved)

    def _to_dto(self, liability: Liability) -> LiabilityDTO:
        """Convert liability entity to DTO."""
        return LiabilityDTO(
            id=liability.id,
            tenant_id=liability.tenant_id,
            name=liability.name,
            liability_type=liability.liability_type.value,
            current_balance=liability.current_balance,
            currency_code=liability.currency_code,
            interest_rate=liability.interest_rate,
            minimum_payment=liability.minimum_payment,
            due_day=liability.due_day,
            creditor=liability.creditor,
            account_number_masked=liability.account_number_masked,
            notes=liability.notes,
            is_included_in_net_worth=liability.is_included_in_net_worth,
            created_at=liability.created_at,
            updated_at=liability.updated_at,
        )


# =============================================================================
# Loan Use Cases
# =============================================================================


class CreateLoan:
    """Use case for creating a new loan."""

    def __init__(
        self,
        loan_repository: LoanRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._loan_repo = loan_repository
        self._event_publisher = event_publisher

    async def execute(self, command: CreateLoanCommand) -> LoanDTO:
        """Create a new loan."""
        loan = Loan.create(
            tenant_id=command.tenant_id,
            name=command.name,
            liability_type=LiabilityType(command.liability_type),
            principal=command.principal,
            currency_code=command.currency_code,
            interest_rate=command.interest_rate,
            payment_amount=command.payment_amount,
            payment_frequency=PaymentFrequency(command.payment_frequency),
            start_date=command.start_date,
            expected_payoff_date=command.expected_payoff_date,
            next_payment_date=command.next_payment_date,
            lender=command.lender,
            account_number_masked=command.account_number_masked,
            notes=command.notes,
        )
        loan.linked_account_id = command.linked_account_id

        saved = await self._loan_repo.save(loan)

        await self._event_publisher.publish(
            LoanCreated(
                tenant_id=saved.tenant_id,
                loan_id=saved.id,
                name=saved.name,
                liability_type=saved.liability_type.value,
                original_principal=str(saved.original_principal),
                interest_rate=str(saved.interest_rate),
                currency_code=saved.currency_code,
            )
        )

        return self._to_dto(saved)

    def _to_dto(self, loan: Loan) -> LoanDTO:
        """Convert loan entity to DTO."""
        return LoanDTO(
            id=loan.id,
            tenant_id=loan.tenant_id,
            name=loan.name,
            liability_type=loan.liability_type.value,
            original_principal=loan.original_principal,
            current_balance=loan.current_balance,
            currency_code=loan.currency_code,
            interest_rate=loan.interest_rate,
            payment_amount=loan.payment_amount,
            payment_frequency=loan.payment_frequency.value,
            status=loan.status.value,
            start_date=loan.start_date,
            expected_payoff_date=loan.expected_payoff_date,
            next_payment_date=loan.next_payment_date,
            lender=loan.lender,
            account_number_masked=loan.account_number_masked,
            notes=loan.notes,
            linked_account_id=loan.linked_account_id,
            is_included_in_net_worth=loan.is_included_in_net_worth,
            created_at=loan.created_at,
            updated_at=loan.updated_at,
            principal_paid=loan.principal_paid,
            principal_paid_percentage=loan.principal_paid_percentage,
        )


class RecordLoanPayment:
    """Use case for recording a loan payment."""

    def __init__(
        self,
        loan_repository: LoanRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._loan_repo = loan_repository
        self._event_publisher = event_publisher

    async def execute(self, command: RecordLoanPaymentCommand) -> LoanDTO:
        """Record a loan payment."""
        loan = await self._loan_repo.get_by_id(command.loan_id, command.tenant_id)
        if not loan:
            raise LoanNotFoundError(command.loan_id)

        if loan.is_paid_off:
            raise LoanAlreadyPaidOffError(command.loan_id)

        loan.record_payment(command.principal_amount, command.interest_amount)
        saved = await self._loan_repo.save(loan)

        await self._event_publisher.publish(
            LoanPaymentRecorded(
                tenant_id=saved.tenant_id,
                loan_id=saved.id,
                principal_amount=str(command.principal_amount),
                interest_amount=str(command.interest_amount) if command.interest_amount else None,
                new_balance=str(saved.current_balance),
            )
        )

        if saved.is_paid_off:
            await self._event_publisher.publish(
                LoanPaidOff(
                    tenant_id=saved.tenant_id,
                    loan_id=saved.id,
                    total_paid=str(saved.original_principal),
                )
            )

        return LoanDTO(
            id=saved.id,
            tenant_id=saved.tenant_id,
            name=saved.name,
            liability_type=saved.liability_type.value,
            original_principal=saved.original_principal,
            current_balance=saved.current_balance,
            currency_code=saved.currency_code,
            interest_rate=saved.interest_rate,
            payment_amount=saved.payment_amount,
            payment_frequency=saved.payment_frequency.value,
            status=saved.status.value,
            start_date=saved.start_date,
            expected_payoff_date=saved.expected_payoff_date,
            next_payment_date=saved.next_payment_date,
            lender=saved.lender,
            account_number_masked=saved.account_number_masked,
            notes=saved.notes,
            linked_account_id=saved.linked_account_id,
            is_included_in_net_worth=saved.is_included_in_net_worth,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
            principal_paid=saved.principal_paid,
            principal_paid_percentage=saved.principal_paid_percentage,
        )


# =============================================================================
# Category Use Cases
# =============================================================================


class CreateCategory:
    """Use case for creating a new category."""

    def __init__(
        self,
        category_repository: CategoryRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._category_repo = category_repository
        self._event_publisher = event_publisher

    async def execute(self, command: CreateCategoryCommand) -> CategoryDTO:
        """Create a new category."""
        # Validate parent exists if provided
        if command.parent_id:
            parent = await self._category_repo.get_by_id(
                command.parent_id, command.tenant_id
            )
            if not parent:
                raise CategoryNotFoundError(command.parent_id)

        category = Category.create(
            tenant_id=command.tenant_id,
            name=command.name,
            parent_id=command.parent_id,
            icon=command.icon,
            color=command.color,
            is_income=command.is_income,
        )

        saved = await self._category_repo.save(category)

        await self._event_publisher.publish(
            CategoryCreated(
                tenant_id=saved.tenant_id,
                category_id=saved.id,
                name=saved.name,
                is_income=saved.is_income,
            )
        )

        return CategoryDTO(
            id=saved.id,
            tenant_id=saved.tenant_id,
            name=saved.name,
            parent_id=saved.parent_id,
            icon=saved.icon,
            color=saved.color,
            is_system=saved.is_system,
            is_income=saved.is_income,
            created_at=saved.created_at,
            updated_at=saved.updated_at,
        )


# =============================================================================
# Report Use Cases
# =============================================================================


class CalculateNetWorth:
    """Use case for calculating net worth."""

    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
        asset_repository: AssetRepository,
        liability_repository: LiabilityRepository,
        loan_repository: LoanRepository,
    ) -> None:
        self._account_repo = account_repository
        self._transaction_repo = transaction_repository
        self._asset_repo = asset_repository
        self._liability_repo = liability_repository
        self._loan_repo = loan_repository

    async def execute(self, tenant_id: UUID, base_currency: str) -> NetWorthDTO:
        """Calculate net worth for a tenant.

        Args:
            tenant_id: The tenant ID.
            base_currency: Currency for the result.

        Returns:
            Net worth DTO.
        """
        # Get all accounts with balances
        accounts = await self._account_repo.get_active(tenant_id)
        account_balances: list[tuple[Account, Money]] = []

        from modules.finance.domain.value_objects import Money

        for account in accounts:
            transactions = await self._transaction_repo.get_by_account(
                account.id, tenant_id
            )
            balance = BalanceCalculator.calculate(transactions, account.currency_code)
            account_balances.append((account, balance.balance))

        # Get assets, liabilities, loans
        assets = await self._asset_repo.get_all(tenant_id)
        liabilities = await self._liability_repo.get_all(tenant_id)
        loans = await self._loan_repo.get_active(tenant_id)

        # Calculate net worth
        result = NetWorthCalculator.calculate(
            accounts=account_balances,
            assets=assets,
            liabilities=liabilities,
            loans=loans,
            base_currency=base_currency,
        )

        return NetWorthDTO(
            total_assets=result.total_assets.amount,
            total_liabilities=result.total_liabilities.amount,
            net_worth=result.net_worth.amount,
            account_balances=result.account_balances.amount,
            asset_count=result.asset_count,
            liability_count=result.liability_count,
            account_count=result.account_count,
            currency_code=base_currency,
            calculated_at=_utc_now(),
        )
