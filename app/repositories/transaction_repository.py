from typing import Optional
from uuid import UUID

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.transaction import KindEnum, Transaction


class TransactionRepository:

    def __init__(self, session: Session):
        self.session = session

    def create(self, transaction: Transaction) -> Transaction:
        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)
        return transaction

    def get_by_id(self, transaction_id: int) -> Optional[Transaction]:
        return self.session.get(Transaction, transaction_id)

    def get_by_external_id(self, external_id: UUID) -> Optional[Transaction]:

        statement = select(Transaction).where(Transaction.external_id == external_id)

        return self.session.exec(statement).first()

    def update(self, transaction: Transaction) -> Transaction:

        self.session.add(transaction)
        self.session.commit()
        self.session.refresh(transaction)

        return transaction

    def get_balance(self, account_id: str) -> float:

        credit_sum = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.account_id == account_id)
            .where(Transaction.kind == KindEnum.CREDIT)
            .where(Transaction.status == "completed")
        ).one()

        debit_sum = self.session.exec(
            select(func.coalesce(func.sum(Transaction.amount), 0))
            .where(Transaction.account_id == account_id)
            .where(Transaction.kind == KindEnum.DEBIT)
            .where(Transaction.status == "completed")
        ).one()

        return credit_sum - debit_sum

    def account_exists(self, account_id: str) -> bool:
        statement = select(Transaction).where(Transaction.account_id == account_id)

        result = self.session.exec(statement).first()
        return result is not None
