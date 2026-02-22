from core.logger import logger
from fastapi import APIRouter, Depends

from app.dependencies import get_transaction_service
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionRequest, TransactionResponse
from app.services.transaction_service import TransactionService

router = APIRouter()


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    tags=["Transactions"],
)
async def create_transaction(
    request: TransactionRequest,
    service: TransactionService = Depends(get_transaction_service),
):
    logger.info(f"Requisição de transação recebida, external_id: {request.external_id}")

    transaction = Transaction(
        external_id=request.external_id, amount=request.amount, kind=request.kind
    )

    transaction = service.create_transaction(transaction)

    return TransactionResponse.model_validate(transaction)
