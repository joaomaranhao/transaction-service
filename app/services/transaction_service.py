from app.core.logger import logger
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


class TransactionService:

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def create_transaction(self, transaction: Transaction) -> Transaction:
        existing_transaction = self.repository.get_by_external_id(
            transaction.external_id
        )
        if existing_transaction:
            logger.info(
                f"Transação com external_id {transaction.external_id} já existe, retornando transação existente"
            )
            return existing_transaction

        logger.info(f"Criando nova transação, external_id: {transaction.external_id}")
        transaction = self.repository.create(transaction)
        return transaction
