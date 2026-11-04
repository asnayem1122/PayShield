"""Merchant repository for read-only access."""

import uuid
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.merchant import Merchant


class MerchantRepository:
    """Repository for merchant entity lookup."""

    @staticmethod
    def get_default_merchant(session: Session) -> Merchant | None:
        """Fetch the default merchant (e.g. PayShield Demo Merchant or first active merchant)."""
        stmt = select(Merchant).where(Merchant.status == "ACTIVE").order_by(Merchant.created_at.asc()).limit(1)
        return session.execute(stmt).scalar_one_or_none()

    @staticmethod
    def get_by_id(session: Session, merchant_id: uuid.UUID) -> Merchant | None:
        return session.get(Merchant, merchant_id)
