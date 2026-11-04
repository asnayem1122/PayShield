"""Risk assessment repository."""

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.risk_assessment import RiskAssessment


class RiskAssessmentRepository:
    """Repository managing risk assessments."""

    @staticmethod
    def create(session: Session, assessment: RiskAssessment) -> RiskAssessment:
        session.add(assessment)
        session.flush()
        return assessment

    @staticmethod
    def get_by_transaction_id(session: Session, transaction_id: uuid.UUID) -> RiskAssessment | None:
        stmt = select(RiskAssessment).where(RiskAssessment.transaction_id == transaction_id)
        return session.execute(stmt).scalar_one_or_none()
