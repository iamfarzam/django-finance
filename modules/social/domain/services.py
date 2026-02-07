"""Domain services for the social finance module.

These services contain business logic that operates on domain entities.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from modules.social.domain.entities import (
        ExpenseSplit,
        GroupExpense,
        PeerDebt,
        Settlement,
    )


@dataclass
class ContactBalance:
    """Balance summary for a single contact.

    Attributes:
        contact_id: The contact's ID.
        currency_code: Currency of the balance.
        total_lent: Total amount lent to this contact.
        total_borrowed: Total amount borrowed from this contact.
        total_settled_to_them: Total settlements paid to contact.
        total_settled_from_them: Total settlements received from contact.
        net_balance: Net amount (positive = they owe you).
    """

    contact_id: UUID
    currency_code: str
    total_lent: Decimal = Decimal("0")
    total_borrowed: Decimal = Decimal("0")
    total_settled_to_them: Decimal = Decimal("0")
    total_settled_from_them: Decimal = Decimal("0")

    @property
    def net_balance(self) -> Decimal:
        """Calculate net balance.

        Positive: Contact owes owner
        Negative: Owner owes contact
        """
        return (
            (self.total_lent - self.total_settled_from_them)
            - (self.total_borrowed - self.total_settled_to_them)
        )

    @property
    def they_owe_you(self) -> Decimal:
        """Amount contact owes to owner (positive balance)."""
        balance = self.net_balance
        return balance if balance > 0 else Decimal("0")

    @property
    def you_owe_them(self) -> Decimal:
        """Amount owner owes to contact (absolute of negative balance)."""
        balance = self.net_balance
        return abs(balance) if balance < 0 else Decimal("0")


class DebtCalculator:
    """Service for calculating debt balances."""

    @staticmethod
    def calculate_contact_balance(
        debts: list["PeerDebt"],
        settlements: list["Settlement"],
        contact_id: UUID,
        currency_code: str,
    ) -> ContactBalance:
        """Calculate the balance with a specific contact.

        Args:
            debts: All peer debts with this contact.
            settlements: All settlements with this contact.
            contact_id: The contact's ID.
            currency_code: Currency to calculate in.

        Returns:
            ContactBalance with the calculated totals.
        """
        from modules.social.domain.enums import DebtDirection, DebtStatus

        balance = ContactBalance(
            contact_id=contact_id,
            currency_code=currency_code,
        )

        # Sum up debts
        for debt in debts:
            if debt.currency_code != currency_code:
                continue
            if debt.status == DebtStatus.CANCELLED:
                continue

            if debt.direction == DebtDirection.LENT:
                balance.total_lent += debt.amount
            else:
                balance.total_borrowed += debt.amount

        # Sum up settlements
        for settlement in settlements:
            if settlement.currency_code != currency_code:
                continue

            if settlement.to_contact_id == contact_id:
                # Owner paid contact
                balance.total_settled_to_them += settlement.amount
            elif settlement.from_contact_id == contact_id:
                # Contact paid owner
                balance.total_settled_from_them += settlement.amount

        return balance

    @staticmethod
    def calculate_all_balances(
        debts: list["PeerDebt"],
        settlements: list["Settlement"],
        currency_code: str,
    ) -> dict[UUID, ContactBalance]:
        """Calculate balances for all contacts.

        Args:
            debts: All peer debts.
            settlements: All settlements.
            currency_code: Currency to calculate in.

        Returns:
            Dict mapping contact_id to ContactBalance.
        """
        # Group by contact
        contact_ids: set[UUID] = set()
        for debt in debts:
            contact_ids.add(debt.contact_id)
        for settlement in settlements:
            if settlement.to_contact_id:
                contact_ids.add(settlement.to_contact_id)
            if settlement.from_contact_id:
                contact_ids.add(settlement.from_contact_id)

        # Calculate balance for each contact
        balances = {}
        for contact_id in contact_ids:
            contact_debts = [d for d in debts if d.contact_id == contact_id]
            contact_settlements = [
                s for s in settlements
                if s.to_contact_id == contact_id or s.from_contact_id == contact_id
            ]
            balances[contact_id] = DebtCalculator.calculate_contact_balance(
                contact_debts,
                contact_settlements,
                contact_id,
                currency_code,
            )

        return balances


@dataclass
class GroupBalanceEntry:
    """A single balance entry in a group balance matrix.

    Attributes:
        from_contact_id: Who owes (None = owner).
        to_contact_id: Who is owed (None = owner).
        amount: Amount owed.
    """

    from_contact_id: UUID | None
    to_contact_id: UUID | None
    amount: Decimal


@dataclass
class GroupBalanceResult:
    """Result of group balance calculation.

    Attributes:
        group_id: The expense group ID.
        currency_code: Currency of the balances.
        entries: List of balance entries.
        total_expenses: Total of all expenses in the group.
    """

    group_id: UUID
    currency_code: str
    entries: list[GroupBalanceEntry]
    total_expenses: Decimal

    def get_balance_for(self, contact_id: UUID | None) -> Decimal:
        """Get net balance for a participant.

        Args:
            contact_id: Contact ID or None for owner.

        Returns:
            Positive = they are owed, Negative = they owe.
        """
        owed_to_them = sum(
            e.amount for e in self.entries if e.to_contact_id == contact_id
        )
        they_owe = sum(
            e.amount for e in self.entries if e.from_contact_id == contact_id
        )
        return owed_to_them - they_owe


class GroupBalanceCalculator:
    """Service for calculating group expense balances."""

    @staticmethod
    def calculate(
        expenses: list["GroupExpense"],
        currency_code: str,
    ) -> GroupBalanceResult:
        """Calculate who owes whom in a group.

        This calculates the raw balances before simplification.

        Args:
            expenses: All expenses in the group.
            currency_code: Currency to calculate in.

        Returns:
            GroupBalanceResult with all balance entries.
        """
        from modules.social.domain.enums import ExpenseStatus

        if not expenses:
            return GroupBalanceResult(
                group_id=expenses[0].group_id if expenses else UUID(int=0),
                currency_code=currency_code,
                entries=[],
                total_expenses=Decimal("0"),
            )

        group_id = expenses[0].group_id
        total = Decimal("0")

        # Track what each participant paid and what they owe
        # None represents the owner
        paid: dict[UUID | None, Decimal] = {}
        owes: dict[UUID | None, Decimal] = {}

        for expense in expenses:
            if expense.currency_code != currency_code:
                continue
            if expense.status == ExpenseStatus.CANCELLED:
                continue

            total += expense.total_amount

            # Record who paid
            payer_id = None if expense.paid_by_owner else expense.paid_by_contact_id
            paid[payer_id] = paid.get(payer_id, Decimal("0")) + expense.total_amount

            # Record what each person owes based on splits
            for split in expense.splits:
                participant_id = None if split.is_owner else split.contact_id
                owes[participant_id] = (
                    owes.get(participant_id, Decimal("0")) + split.share_amount
                )

        # Calculate net balance for each participant
        all_participants = set(paid.keys()) | set(owes.keys())
        net_balances: dict[UUID | None, Decimal] = {}

        for participant in all_participants:
            participant_paid = paid.get(participant, Decimal("0"))
            participant_owes = owes.get(participant, Decimal("0"))
            # Positive = owed money (paid more than fair share)
            # Negative = owes money (paid less than fair share)
            net_balances[participant] = participant_paid - participant_owes

        # Create balance entries for those who owe to those who are owed
        entries = []
        debtors = [(p, -b) for p, b in net_balances.items() if b < 0]
        creditors = [(p, b) for p, b in net_balances.items() if b > 0]

        for debtor_id, debt_amount in debtors:
            remaining_debt = debt_amount
            for creditor_id, credit_amount in creditors:
                if remaining_debt <= 0:
                    break
                if credit_amount <= 0:
                    continue

                transfer_amount = min(remaining_debt, credit_amount)
                if transfer_amount > 0:
                    entries.append(
                        GroupBalanceEntry(
                            from_contact_id=debtor_id,
                            to_contact_id=creditor_id,
                            amount=transfer_amount,
                        )
                    )
                    remaining_debt -= transfer_amount
                    # Update creditor's remaining credit
                    creditors = [
                        (cid, ca - transfer_amount if cid == creditor_id else ca)
                        for cid, ca in creditors
                    ]

        return GroupBalanceResult(
            group_id=group_id,
            currency_code=currency_code,
            entries=entries,
            total_expenses=total,
        )


@dataclass
class SimplifiedDebt:
    """A simplified debt after minimizing transactions.

    Attributes:
        from_contact_id: Who should pay (None = owner).
        to_contact_id: Who should receive (None = owner).
        amount: Amount to transfer.
    """

    from_contact_id: UUID | None
    to_contact_id: UUID | None
    amount: Decimal


class SimplifyDebtsService:
    """Service for simplifying debts to minimize transactions.

    Uses a greedy algorithm to minimize the number of transactions
    needed to settle all debts.
    """

    @staticmethod
    def simplify(
        balances: dict[UUID | None, Decimal],
    ) -> list[SimplifiedDebt]:
        """Simplify debts to minimize transactions.

        Args:
            balances: Net balance per participant.
                     Positive = owed money, Negative = owes money.

        Returns:
            List of simplified debts.
        """
        # Separate into debtors and creditors
        debtors: list[tuple[UUID | None, Decimal]] = [
            (pid, -balance) for pid, balance in balances.items() if balance < 0
        ]
        creditors: list[tuple[UUID | None, Decimal]] = [
            (pid, balance) for pid, balance in balances.items() if balance > 0
        ]

        # Sort by amount (largest first) for better simplification
        debtors.sort(key=lambda x: x[1], reverse=True)
        creditors.sort(key=lambda x: x[1], reverse=True)

        simplified: list[SimplifiedDebt] = []

        # Greedy matching
        d_idx = 0
        c_idx = 0
        debtor_remaining = list(debtors)
        creditor_remaining = list(creditors)

        while d_idx < len(debtor_remaining) and c_idx < len(creditor_remaining):
            debtor_id, debt_amount = debtor_remaining[d_idx]
            creditor_id, credit_amount = creditor_remaining[c_idx]

            if debt_amount <= 0:
                d_idx += 1
                continue
            if credit_amount <= 0:
                c_idx += 1
                continue

            transfer = min(debt_amount, credit_amount)
            if transfer > 0:
                simplified.append(
                    SimplifiedDebt(
                        from_contact_id=debtor_id,
                        to_contact_id=creditor_id,
                        amount=transfer,
                    )
                )

            # Update remaining amounts
            debtor_remaining[d_idx] = (debtor_id, debt_amount - transfer)
            creditor_remaining[c_idx] = (creditor_id, credit_amount - transfer)

            if debtor_remaining[d_idx][1] <= 0:
                d_idx += 1
            if creditor_remaining[c_idx][1] <= 0:
                c_idx += 1

        return simplified

    @staticmethod
    def simplify_from_group(
        group_balance: GroupBalanceResult,
    ) -> list[SimplifiedDebt]:
        """Simplify debts from a group balance result.

        Args:
            group_balance: The group balance calculation result.

        Returns:
            List of simplified debts.
        """
        # Calculate net balance for each participant
        balances: dict[UUID | None, Decimal] = {}

        for entry in group_balance.entries:
            # Debtor loses money
            balances[entry.from_contact_id] = (
                balances.get(entry.from_contact_id, Decimal("0")) - entry.amount
            )
            # Creditor gains money
            balances[entry.to_contact_id] = (
                balances.get(entry.to_contact_id, Decimal("0")) + entry.amount
            )

        return SimplifyDebtsService.simplify(balances)


class SettlementSuggestionService:
    """Service for suggesting settlements based on current balances."""

    @staticmethod
    def suggest_for_contact(
        contact_balance: ContactBalance,
    ) -> SimplifiedDebt | None:
        """Suggest a settlement for a contact balance.

        Args:
            contact_balance: The balance with a contact.

        Returns:
            Suggested settlement or None if balanced.
        """
        net = contact_balance.net_balance

        if net == 0:
            return None

        if net > 0:
            # Contact owes owner - contact should pay
            return SimplifiedDebt(
                from_contact_id=contact_balance.contact_id,
                to_contact_id=None,  # Owner
                amount=net,
            )
        else:
            # Owner owes contact - owner should pay
            return SimplifiedDebt(
                from_contact_id=None,  # Owner
                to_contact_id=contact_balance.contact_id,
                amount=abs(net),
            )

    @staticmethod
    def suggest_all(
        balances: dict[UUID, ContactBalance],
    ) -> list[SimplifiedDebt]:
        """Suggest settlements for all contact balances.

        Args:
            balances: Dict of contact_id to ContactBalance.

        Returns:
            List of suggested settlements.
        """
        suggestions = []
        for contact_balance in balances.values():
            suggestion = SettlementSuggestionService.suggest_for_contact(contact_balance)
            if suggestion:
                suggestions.append(suggestion)
        return suggestions
