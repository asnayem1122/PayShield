"""Audit log API endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.audit_log_repository import AuditLogRepository
from app.schemas.audit_log import AuditLogListResponse, AuditLogResponse

router = APIRouter(prefix="/audit", tags=["Audit Log"])


@router.get("/logs", response_model=AuditLogListResponse)
def list_audit_logs(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve immutable audit trail entries."""
    logs, total = AuditLogRepository.list_logs(db, limit, offset)
    return AuditLogListResponse(
        items=[AuditLogResponse.model_validate(l) for l in logs],
        total=total,
    )
