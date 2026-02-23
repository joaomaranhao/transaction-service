import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import BankPartnerError, InvalidTransactionAmountError
from app.models.transaction import KindEnum, Transaction
from app.services.transaction_service import TransactionService


@pytest.fixture
def mock_repository():
    """Mock do TransactionRepository"""
    return MagicMock()


@pytest.fixture
def service(mock_repository):
    """Instância do TransactionService com repository mockado"""
    return TransactionService(mock_repository)


@pytest.fixture
def sample_transaction():
    """Transação de exemplo para testes"""
    return Transaction(
        external_id=uuid.uuid4(),
        amount=100.0,
        kind=KindEnum.CREDIT,
        account_id="123",
    )


@pytest.fixture
def pending_transaction():
    """Transação pendente para testes de process_transaction"""
    return Transaction(
        id=1,
        external_id=uuid.uuid4(),
        amount=100.0,
        kind=KindEnum.CREDIT,
        account_id="123",
        status="pending",
    )


class TestCreateTransaction:
    """Testes unitários para create_transaction"""

    @pytest.mark.asyncio
    async def test_returns_existing_transaction_if_duplicate(
        self, service, mock_repository, sample_transaction
    ):
        """Deve retornar transação existente se external_id já existe"""
        existing = Transaction(
            id=1,
            external_id=sample_transaction.external_id,
            amount=100.0,
            kind=KindEnum.CREDIT,
            account_id="123",
            status="completed",
        )
        mock_repository.get_by_external_id.return_value = existing

        result, created = await service.create_transaction(sample_transaction)

        assert result == existing
        assert created is False
        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_for_zero_amount(
        self, service, mock_repository, sample_transaction
    ):
        """Deve levantar InvalidTransactionAmountError para valor zero"""
        mock_repository.get_by_external_id.return_value = None
        sample_transaction.amount = 0

        with pytest.raises(InvalidTransactionAmountError):
            await service.create_transaction(sample_transaction)

        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_for_negative_amount(
        self, service, mock_repository, sample_transaction
    ):
        """Deve levantar InvalidTransactionAmountError para valor negativo"""
        mock_repository.get_by_external_id.return_value = None
        sample_transaction.amount = -50

        with pytest.raises(InvalidTransactionAmountError):
            await service.create_transaction(sample_transaction)

        mock_repository.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_creates_transaction_with_pending_status(
        self, service, mock_repository, sample_transaction
    ):
        """Deve criar transação com status pending"""
        mock_repository.get_by_external_id.return_value = None

        created_transaction = Transaction(
            id=1,
            external_id=sample_transaction.external_id,
            amount=sample_transaction.amount,
            kind=sample_transaction.kind,
            account_id=sample_transaction.account_id,
            status="pending",
        )
        mock_repository.create.return_value = created_transaction

        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ):
            result, created = await service.create_transaction(sample_transaction)

        assert result.status == "pending"
        assert created is True
        mock_repository.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_publishes_transaction_to_queue(
        self, service, mock_repository, sample_transaction
    ):
        """Deve publicar transação na fila após criar"""
        mock_repository.get_by_external_id.return_value = None

        created_transaction = Transaction(
            id=42,
            external_id=sample_transaction.external_id,
            amount=sample_transaction.amount,
            kind=sample_transaction.kind,
            account_id=sample_transaction.account_id,
            status="pending",
        )
        mock_repository.create.return_value = created_transaction

        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ) as mock_publish:
            await service.create_transaction(sample_transaction)

            mock_publish.assert_called_once_with(42)

    @pytest.mark.asyncio
    async def test_does_not_publish_for_duplicate(
        self, service, mock_repository, sample_transaction
    ):
        """Não deve publicar para transação duplicada"""
        existing = Transaction(
            id=1,
            external_id=sample_transaction.external_id,
            amount=100.0,
            kind=KindEnum.CREDIT,
            account_id="123",
            status="completed",
        )
        mock_repository.get_by_external_id.return_value = existing

        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ) as mock_publish:
            await service.create_transaction(sample_transaction)

            mock_publish.assert_not_called()


class TestProcessTransaction:
    """Testes unitários para process_transaction"""

    @pytest.mark.asyncio
    async def test_completes_transaction_on_success(
        self, service, mock_repository, pending_transaction
    ):
        """Deve completar transação quando banco parceiro retorna sucesso"""
        partner_id = str(uuid.uuid4())
        mock_repository.get_by_id.return_value = pending_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=partner_id,
        ):
            await service.process_transaction(pending_transaction.id)

        # Verifica chamadas de update
        assert mock_repository.update.call_count == 2  # processing + completed
        final_update = mock_repository.update.call_args_list[-1][0][0]
        assert final_update.status == "completed"
        assert final_update.partner_id == partner_id

    @pytest.mark.asyncio
    async def test_raises_exception_on_bank_partner_failure(
        self, service, mock_repository, pending_transaction
    ):
        """Deve lançar exceção quando banco parceiro falha"""
        mock_repository.get_by_id.return_value = pending_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            side_effect=BankPartnerError("Erro"),
        ):
            with pytest.raises(BankPartnerError):
                await service.process_transaction(
                    pending_transaction.id, is_last_attempt=False
                )

        # Status volta para pending para retry
        final_update = mock_repository.update.call_args_list[-1][0][0]
        assert final_update.status == "pending"

    @pytest.mark.asyncio
    async def test_marks_failed_on_last_attempt(
        self, service, mock_repository, pending_transaction
    ):
        """Deve marcar como failed na última tentativa"""
        mock_repository.get_by_id.return_value = pending_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            side_effect=BankPartnerError("Erro"),
        ):
            with pytest.raises(BankPartnerError):
                await service.process_transaction(
                    pending_transaction.id, is_last_attempt=True
                )

        final_update = mock_repository.update.call_args_list[-1][0][0]
        assert final_update.status == "failed"

    @pytest.mark.asyncio
    async def test_skips_already_processed_transaction(
        self, service, mock_repository, pending_transaction
    ):
        """Deve ignorar transação já processada"""
        pending_transaction.status = "completed"
        mock_repository.get_by_id.return_value = pending_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
        ) as mock_bank:
            await service.process_transaction(pending_transaction.id)

            mock_bank.assert_not_called()

    @pytest.mark.asyncio
    async def test_handles_not_found_transaction(self, service, mock_repository):
        """Deve tratar transação não encontrada"""
        mock_repository.get_by_id.return_value = None

        # Não deve lançar exceção
        await service.process_transaction(999)

        mock_repository.update.assert_not_called()

    @pytest.mark.asyncio
    async def test_calls_bank_partner_with_correct_params(
        self, service, mock_repository, pending_transaction
    ):
        """Deve chamar banco parceiro com parâmetros corretos"""
        mock_repository.get_by_id.return_value = pending_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ) as mock_bank:
            await service.process_transaction(pending_transaction.id)

            mock_bank.assert_called_once_with(
                external_id=pending_transaction.external_id,
                amount=pending_transaction.amount,
                kind=pending_transaction.kind,
            )


class TestTransactionServiceInit:
    """Testes de inicialização do service"""

    def test_initializes_with_repository(self, mock_repository):
        """Deve inicializar com repository"""
        service = TransactionService(mock_repository)

        assert service.repository == mock_repository
