"""Analyst case management API endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import require_role
from app.models.user import User
from app.schemas.analyst_case import (
    AnalystCaseListResponse,
    AnalystCaseResponse,
    AnalystCaseUpdate,
)
from app.services.analyst_case_service import AnalystCaseService

router = APIRouter(prefix="/cases", tags=["Analyst Cases"])


@router.get("", response_model=AnalystCaseListResponse)
def list_cases(
    status: str | None = Query(
        None, description="Filter by status (OPEN, IN_REVIEW, RESOLVED)"
    ),
    priority: str | None = Query(
        None, description="Filter by priority (LOW, MEDIUM, HIGH)"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_role("ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Retrieve paginated fraud investigation cases (restricted to Analysts and Admins)."""
    return AnalystCaseService.list_cases(
        session=db,
        status=status,
        priority=priority,
        limit=limit,
        offset=offset,
    )


@router.get("/{case_id}", response_model=AnalystCaseResponse)
def get_case(
    case_id: uuid.UUID,
    current_user: User = Depends(require_role("ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific analyst case (restricted to Analysts and Admins)."""
    c = AnalystCaseService.get_case(db, case_id)
    if not c:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analyst case '{case_id}' not found",
        )
    return c


@router.patch("/{case_id}", response_model=AnalystCaseResponse)
def update_case(
    case_id: uuid.UUID,
    payload: AnalystCaseUpdate,
    current_user: User = Depends(require_role("ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Update case status or notes and record audit log (restricted to Analysts and Admins)."""
    try:
        return AnalystCaseService.update_case(
            db, case_id, payload, current_user=current_user
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
