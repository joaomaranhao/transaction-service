from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.transaction_repository import TransactionRepository


def get_transaction_repository(
    session: Session = Depends(get_session),
) -> TransactionRepository:
    return TransactionRepository(session)
