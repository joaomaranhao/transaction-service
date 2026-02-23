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

        result = await service.create_transaction(sample_transaction)

        assert result == existing
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
        """Deve criar transação com status pending inicialmente"""
        mock_repository.get_by_external_id.return_value = None

        # Captura o status no momento da chamada de create
        captured_status = []

        def capture_create(transaction):
            captured_status.append(transaction.status)
            return transaction

        mock_repository.create.side_effect = capture_create
        mock_repository.update.return_value = sample_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            await service.create_transaction(sample_transaction)

        # Verifica que create foi chamado com status pending
        assert captured_status[0] == "pending"

    @pytest.mark.asyncio
    async def test_completes_transaction_on_bank_partner_success(
        self, service, mock_repository, sample_transaction
    ):
        """Deve completar transação quando banco parceiro retorna sucesso"""
        partner_id = str(uuid.uuid4())
        mock_repository.get_by_external_id.return_value = None
        mock_repository.create.return_value = sample_transaction
        mock_repository.update.return_value = sample_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=partner_id,
        ):
            await service.create_transaction(sample_transaction)

        # Verifica que update foi chamado com status completed e partner_id
        updated_transaction = mock_repository.update.call_args[0][0]
        assert updated_transaction.status == "completed"
        assert updated_transaction.partner_id == partner_id

    @pytest.mark.asyncio
    async def test_keeps_pending_on_bank_partner_failure(
        self, service, mock_repository, sample_transaction
    ):
        """Deve manter status pending quando banco parceiro falha"""
        mock_repository.get_by_external_id.return_value = None
        mock_repository.create.return_value = sample_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            side_effect=BankPartnerError("Erro"),
        ):
            result = await service.create_transaction(sample_transaction)

        # update não deve ser chamado quando banco parceiro falha
        mock_repository.update.assert_not_called()
        assert result.status == "pending"

    @pytest.mark.asyncio
    async def test_calls_bank_partner_with_correct_params(
        self, service, mock_repository, sample_transaction
    ):
        """Deve chamar banco parceiro com parâmetros corretos"""
        mock_repository.get_by_external_id.return_value = None
        mock_repository.create.return_value = sample_transaction
        mock_repository.update.return_value = sample_transaction

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ) as mock_bank:
            await service.create_transaction(sample_transaction)

            mock_bank.assert_called_once_with(
                external_id=sample_transaction.external_id,
                amount=sample_transaction.amount,
                kind=sample_transaction.kind,
            )

    @pytest.mark.asyncio
    async def test_does_not_call_bank_partner_for_duplicate(
        self, service, mock_repository, sample_transaction
    ):
        """Não deve chamar banco parceiro para transação duplicada"""
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
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
        ) as mock_bank:
            await service.create_transaction(sample_transaction)

            mock_bank.assert_not_called()

    @pytest.mark.asyncio
    async def test_does_not_call_bank_partner_for_invalid_amount(
        self, service, mock_repository, sample_transaction
    ):
        """Não deve chamar banco parceiro para valor inválido"""
        mock_repository.get_by_external_id.return_value = None
        sample_transaction.amount = -100

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
        ) as mock_bank:
            with pytest.raises(InvalidTransactionAmountError):
                await service.create_transaction(sample_transaction)

            mock_bank.assert_not_called()


class TestTransactionServiceInit:
    """Testes de inicialização do service"""

    def test_initializes_with_repository(self, mock_repository):
        """Deve inicializar com repository"""
        service = TransactionService(mock_repository)

        assert service.repository == mock_repository
