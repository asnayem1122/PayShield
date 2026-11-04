"""Transaction data access repository."""

from datetime import datetime, timezone
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from app.models.transaction import Transaction


class TransactionRepository:
    """Repository managing transactions."""

    @staticmethod
    def list_transactions(
        session: Session,
        status: str | None = None,
        risk_level: str | None = None,
        query: str | None = None,
        merchant_id: uuid.UUID | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[list[Transaction], int]:
        """List transactions with optional filtering and pagination."""
        stmt = select(Transaction)

        if merchant_id is not None:
            stmt = stmt.where(Transaction.merchant_id == merchant_id)
        if status:
            stmt = stmt.where(Transaction.transaction_status == status.upper())
        if risk_level:
            stmt = stmt.where(Transaction.risk_level == risk_level.upper())
        if query:
            q = f"%{query}%"
            stmt = stmt.where(
                or_(
                    Transaction.reference.ilike(q),
                    Transaction.counterparty_name.ilike(q),
                    Transaction.location_city.ilike(q),
                )
            )

        # Count total matching
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = session.execute(count_stmt).scalar_one()

        # Fetch page ordered by created_at DESC
        stmt = (
            stmt.order_by(
                Transaction.created_at.desc(), Transaction.reference.desc()
            )
            .limit(limit)
            .offset(offset)
        )
        items = list(session.execute(stmt).scalars().all())

        return items, total

    @staticmethod
    def get_by_reference(session: Session, reference: str) -> Transaction | None:
        stmt = select(Transaction).where(Transaction.reference == reference)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(session: Session, transaction_id: uuid.UUID) -> Transaction | None:
        return session.get(Transaction, transaction_id)

    @staticmethod
    def create(session: Session, transaction: Transaction) -> Transaction:
        session.add(transaction)
        session.flush()
        return transaction

    @staticmethod
    def update_status(
        session: Session,
        transaction: Transaction,
        new_status: str,
    ) -> Transaction:
        transaction.transaction_status = new_status
        transaction.updated_at = datetime.now(timezone.utc)
        session.flush()
        return transaction
