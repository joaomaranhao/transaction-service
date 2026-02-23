from app.core.exceptions import InvalidTransactionAmountError
from app.core.logger import logger
from app.integrations.bank_partner import bank_partner_request
from app.messaging.publisher import publish_transaction
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


class TransactionService:

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    async def create_transaction(
        self, transaction: Transaction
    ) -> tuple[Transaction, bool]:
        """
        Cria uma nova transação ou retorna existente.

        Returns:
            tuple[Transaction, bool]: (transação, foi_criada)
        """
        # Verifica se já existe uma transação com o mesmo external_id
        existing_transaction = self.repository.get_by_external_id(
            transaction.external_id
        )
        if existing_transaction:
            logger.info(
                f"Transação com external_id={transaction.external_id} já existe, retornando transação existente"
            )
            return existing_transaction, False

        # Valida valor da transação
        if transaction.amount <= 0:
            logger.error(
                f"Valor de transação inválido, external_id={transaction.external_id}, amount={transaction.amount}"
            )
            raise InvalidTransactionAmountError()

        # Cria nova transação
        logger.info(f"Criando nova transação, external_id={transaction.external_id}")
        transaction.status = "pending"
        transaction = self.repository.create(transaction)

        # Publica transação para processamento assíncrono
        if transaction.id is not None:
            await publish_transaction(transaction.id)
            logger.info(f"Transação publicada para processamento, id={transaction.id}")

        return transaction, True

    async def process_transaction(
        self, transaction_id: int, is_last_attempt: bool = False
    ) -> None:
        transaction = self.repository.get_by_id(transaction_id)

        if not transaction:
            logger.error(f"Transação não encontrada, id={transaction_id}")
            return

        if transaction.status not in ("pending", "processing"):
            logger.info(
                f"Transação id={transaction_id} já processada, status={transaction.status}"
            )
            return

        try:
            logger.info(f"Processando transação id={transaction_id}")

            # Mudar status para processing para evitar processamento concorrente
            transaction.status = "processing"
            self.repository.update(transaction)

            partner_id = await bank_partner_request(
                external_id=transaction.external_id,
                amount=transaction.amount,
                kind=transaction.kind,
            )
            transaction.status = "completed"
            transaction.partner_id = partner_id
            self.repository.update(transaction)
            logger.info(
                f"Transação id={transaction_id} processada com sucesso, status={transaction.status}"
            )
        except Exception as e:
            logger.error(f"Erro ao processar transação id={transaction_id}: {e}")

            if is_last_attempt:
                transaction.status = "failed"
                self.repository.update(transaction)
                logger.info(
                    f"Transação id={transaction_id} falhou definitivamente, status={transaction.status}"
                )
            else:
                # Volta para pending para permitir retry
                transaction.status = "pending"
                self.repository.update(transaction)

            raise
