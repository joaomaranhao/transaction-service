from fastapi import Depends
from sqlmodel import Session

from app.core.database import get_session
from app.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService


def get_transaction_repository(
    session: Session = Depends(get_session),
) -> TransactionRepository:
    return TransactionRepository(session)


def get_transaction_service(
    repository: TransactionRepository = Depends(get_transaction_repository),
):
    return TransactionService(repository)


def get_account_service(
    repository: TransactionRepository = Depends(get_transaction_repository),
):
    from app.services.account_services import AccountService

    return AccountService(repository)
