from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.models.transaction import Transaction
from app.schemas.transaction import TransactionRequest, TransactionResponse

router = APIRouter()


@router.post(
    "/transaction",
    response_model=TransactionResponse,
    tags=["Transactions"],
)
async def create_transaction(
    request: TransactionRequest, session: Session = Depends(get_session)
):

    transaction = Transaction(
        external_id=request.external_id, amount=request.amount, kind=request.kind
    )

    session.add(transaction)
    session.commit()
    session.refresh(transaction)

    return {"id": transaction.id, "status": transaction.status}
