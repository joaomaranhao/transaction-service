from typing import Optional
from uuid import UUID

from sqlmodel import Session, select

from app.models.transaction import Transaction


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
