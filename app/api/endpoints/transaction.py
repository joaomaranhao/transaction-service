from fastapi import APIRouter, Depends

from app.dependencies import get_transaction_repository
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository
from app.schemas.transaction import TransactionRequest, TransactionResponse

router = APIRouter()


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    tags=["Transactions"],
)
async def create_transaction(
    request: TransactionRequest,
    repository: TransactionRepository = Depends(get_transaction_repository),
):

    transaction = Transaction(
        external_id=request.external_id, amount=request.amount, kind=request.kind
    )

    transaction = repository.create(transaction)

    return TransactionResponse.model_validate(transaction)
