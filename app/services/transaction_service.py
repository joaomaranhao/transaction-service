from app.core.exceptions import BankPartnerError, InvalidTransactionAmountError
from app.core.logger import logger
from app.integrations.bank_partner import bank_partner_request
from app.models.transaction import Transaction
from app.repositories.transaction_repository import TransactionRepository


class TransactionService:

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    async def create_transaction(self, transaction: Transaction) -> Transaction:
        # Verifica se já existe uma transação com o mesmo external_id
        existing_transaction = self.repository.get_by_external_id(
            transaction.external_id
        )
        if existing_transaction:
            logger.info(
                f"Transação com external_id={transaction.external_id} já existe, retornando transação existente"
            )
            return existing_transaction

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

        try:
            # Envia transação para banco parceiro
            logger.info(
                f"Enviando transação para banco parceiro, external_id={transaction.external_id}"
            )
            partner_id = await bank_partner_request(
                external_id=transaction.external_id,
                amount=transaction.amount,
                kind=transaction.kind,
            )
            logger.info(
                f"Resposta do banco parceiro recebida, partner_id={partner_id}, external_id={transaction.external_id}"
            )
            transaction.partner_id = partner_id
            transaction.status = "completed"
            transaction = self.repository.update(transaction)
            logger.info(
                f"Transação completada, external_id={transaction.external_id}, partner_id={transaction.partner_id}"
            )
        except BankPartnerError:
            logger.error(
                f"Erro ao processar transação no banco parceiro, external_id={transaction.external_id}"
            )

        return transaction
