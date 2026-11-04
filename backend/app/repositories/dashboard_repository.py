"""Dashboard live aggregation repository."""

from decimal import Decimal
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session
from app.models.analyst_case import AnalystCase
from app.models.transaction import Transaction


class DashboardRepository:
    """Repository for live database-backed dashboard aggregations."""

    @staticmethod
    def get_summary(session: Session) -> dict:
        """Calculate live financial and fraud risk KPI aggregates."""
        tx_stats_stmt = select(
            func.coalesce(func.sum(Transaction.amount), Decimal("0.00")).label("total_volume"),
            func.coalesce(
                func.sum(case((Transaction.transaction_status == "APPROVED", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("approved_volume"),
            func.coalesce(
                func.sum(case((Transaction.transaction_status == "REVIEW", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("review_volume"),
            func.coalesce(
                func.sum(case((Transaction.transaction_status == "BLOCKED", Transaction.amount), else_=Decimal("0.00"))),
                Decimal("0.00"),
            ).label("blocked_volume"),
            func.count(Transaction.id).label("total_transactions"),
            func.count(case((Transaction.transaction_status == "APPROVED", 1))).label("approved_count"),
            func.count(case((Transaction.transaction_status == "REVIEW", 1))).label("review_count"),
            func.count(case((Transaction.transaction_status == "BLOCKED", 1))).label("blocked_count"),
            func.coalesce(func.avg(Transaction.risk_score), 0.0).label("avg_risk_score"),
            func.count(case((Transaction.risk_level == "HIGH", 1))).label("high_risk_count"),
        )
        row = session.execute(tx_stats_stmt).one()

        open_cases_stmt = select(func.count(AnalystCase.id)).where(
            AnalystCase.case_status.in_(["OPEN", "IN_REVIEW"])
        )
        open_cases_count = session.execute(open_cases_stmt).scalar_one()

        total_tx = row.total_transactions or 0
        high_risk_cnt = row.high_risk_count or 0
        high_risk_ratio = (high_risk_cnt / total_tx) if total_tx > 0 else 0.0

        rev_vol = f"{Decimal(row.review_volume):.2f}"
        rev_cnt = row.review_count or 0

        return {
            "total_volume": f"{Decimal(row.total_volume):.2f}",
            "approved_volume": f"{Decimal(row.approved_volume):.2f}",
            "review_volume": rev_vol,
            "flagged_volume": rev_vol,
            "blocked_volume": f"{Decimal(row.blocked_volume):.2f}",
            "total_transactions": total_tx,
            "approved_count": row.approved_count or 0,
            "review_count": rev_cnt,
            "flagged_count": rev_cnt,
            "blocked_count": row.blocked_count or 0,
            "open_cases_count": open_cases_count,
            "average_risk_score": round(float(row.avg_risk_score), 2),
            "high_risk_ratio": round(float(high_risk_ratio), 4),
        }

    @staticmethod
    def get_risk_distribution(session: Session) -> dict:
        """Count transactions across risk levels."""
        stmt = select(
            func.count(case((Transaction.risk_level == "LOW", 1))).label("low_count"),
            func.count(case((Transaction.risk_level == "MEDIUM", 1))).label("medium_count"),
            func.count(case((Transaction.risk_level == "HIGH", 1))).label("high_count"),
            func.count(Transaction.id).label("total_count"),
        )
        row = session.execute(stmt).one()
        return {
            "low_count": row.low_count or 0,
            "medium_count": row.medium_count or 0,
            "high_count": row.high_count or 0,
            "total_count": row.total_count or 0,
        }

    @staticmethod
    def get_recent_transactions(session: Session, limit: int = 10) -> list[Transaction]:
        """Fetch the most recent transactions."""
        stmt = select(Transaction).order_by(Transaction.created_at.desc(), Transaction.reference.desc()).limit(limit)
        return list(session.execute(stmt).scalars().all())
