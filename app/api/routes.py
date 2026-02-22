from fastapi import APIRouter

from app.api.endpoints import health
from app.api.endpoints.account import router as account_router
from app.api.endpoints.transaction import router as transaction_router

router = APIRouter()

router.include_router(transaction_router)
router.include_router(account_router)
router.include_router(health.router)
