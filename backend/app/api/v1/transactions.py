"""Transaction API endpoints."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.dependencies import (
    get_current_user,
    require_merchant_ownership,
    require_role,
)
from app.models.user import User
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionUpdateStatus,
)
from app.services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    status: str | None = Query(
        None, description="Filter by status (APPROVED, FLAGGED, BLOCKED)"
    ),
    risk_level: str | None = Query(
        None, description="Filter by risk level (LOW, MEDIUM, HIGH)"
    ),
    query: str | None = Query(
        None, description="Search by counterparty, reference, or location"
    ),
    merchant_id: uuid.UUID | None = Query(
        None, description="Filter by merchant ID (Analyst/Admin only)"
    ),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve paginated transactions with optional filters and tenant data isolation."""
    scoped_merchant_id = (
        current_user.merchant_id
        if current_user.role == "MERCHANT"
        else merchant_id
    )

    items, total = TransactionRepository.list_transactions(
        session=db,
        status=status,
        risk_level=risk_level,
        query=query,
        merchant_id=scoped_merchant_id,
        limit=limit,
        offset=offset,
    )
    return TransactionListResponse(
        items=[TransactionResponse.from_orm_model(tx) for tx in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{reference}", response_model=TransactionResponse)
def get_transaction(
    reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get transaction details by unique reference with strict merchant ownership check."""
    tx = TransactionRepository.get_by_reference(db, reference)
    if not tx:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Transaction '{reference}' not found",
        )

    # Merchant tenant isolation: prevent IDOR enumeration across merchants
    if current_user.role == "MERCHANT":
        require_merchant_ownership(tx.merchant_id, current_user)

    return TransactionResponse.from_orm_model(tx)


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a payment transaction for real-time risk assessment and ingestion."""
    try:
        tx, _, _ = TransactionService.create_transaction(
            db, payload, current_user=current_user
        )
        return TransactionResponse.from_orm_model(tx)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.patch("/{reference}/status", response_model=TransactionResponse)
def update_transaction_status(
    reference: str,
    payload: TransactionUpdateStatus,
    current_user: User = Depends(require_role("ANALYST", "ADMIN")),
    db: Session = Depends(get_db),
):
    """Update transaction status (APPROVED, FLAGGED, BLOCKED) and append audit log."""
    try:
        tx = TransactionService.update_transaction_status(
            db, reference, payload, current_user=current_user
        )
        return TransactionResponse.from_orm_model(tx)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
