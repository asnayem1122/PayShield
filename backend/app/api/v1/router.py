"""API v1 root router."""

from fastapi import APIRouter
from app.api.v1.analyst_cases import router as cases_router
from app.api.v1.audit import router as audit_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.risk import router as risk_router
from app.api.v1.transactions import router as transactions_router

api_v1_router = APIRouter()
api_v1_router.include_router(dashboard_router)
api_v1_router.include_router(transactions_router)
api_v1_router.include_router(cases_router)
api_v1_router.include_router(risk_router)
api_v1_router.include_router(audit_router)
