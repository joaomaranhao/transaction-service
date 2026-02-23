import uuid
from unittest.mock import AsyncMock, patch

import pytest
from sqlmodel import select

from app.models.transaction import Transaction


class TestTransactionWithBankPartner:
    """Testes de integração da transação com o banco parceiro"""

    def test_transaction_completed_when_bank_partner_succeeds(self, client):
        """Transação deve ser completada quando banco parceiro responde com sucesso"""
        partner_id = str(uuid.uuid4())

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=partner_id,
        ):
            response = client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

        assert response.status_code == 201
        assert response.json()["status"] == "completed"

    def test_transaction_pending_when_bank_partner_fails(self, client, session):
        """Transação deve ficar pendente quando banco parceiro falha"""
        from app.core.exceptions import BankPartnerError

        external_id = str(uuid.uuid4())

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            side_effect=BankPartnerError("Erro no banco parceiro"),
        ):
            response = client.post(
                "/transaction",
                json={
                    "external_id": external_id,
                    "amount": 100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

        # Transação é criada mas não completada
        assert response.status_code == 201

        transaction = session.exec(select(Transaction)).first()
        assert transaction is not None
        assert transaction.status == "pending"
        assert transaction.partner_id is None

    def test_bank_partner_receives_correct_parameters(self, client):
        """Banco parceiro deve receber os parâmetros corretos"""
        external_id = uuid.uuid4()

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ) as mock_bank_partner:
            client.post(
                "/transaction",
                json={
                    "external_id": str(external_id),
                    "amount": 150.50,
                    "kind": "debit",
                    "account_id": "123",
                },
            )

            mock_bank_partner.assert_called_once()
            call_kwargs = mock_bank_partner.call_args.kwargs

            assert call_kwargs["amount"] == 150.50
            assert call_kwargs["kind"] == "debit"

    def test_bank_partner_not_called_for_duplicate_transaction(self, client):
        """Banco parceiro não deve ser chamado para transação duplicada"""
        external_id = str(uuid.uuid4())

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ) as mock_bank_partner:
            # Primeira requisição
            client.post(
                "/transaction",
                json={
                    "external_id": external_id,
                    "amount": 100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

            # Segunda requisição com mesmo external_id
            client.post(
                "/transaction",
                json={
                    "external_id": external_id,
                    "amount": 100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

            # Banco parceiro só deve ser chamado uma vez
            assert mock_bank_partner.call_count == 1

    def test_bank_partner_not_called_for_invalid_amount(self, client):
        """Banco parceiro não deve ser chamado para transação com valor inválido"""
        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
        ) as mock_bank_partner:
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": -100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

            # Banco parceiro não deve ser chamado
            mock_bank_partner.assert_not_called()


class TestBankPartnerUnit:
    """Testes unitários da função bank_partner_request"""

    @pytest.mark.asyncio
    async def test_bank_partner_returns_uuid(self):
        """bank_partner_request deve retornar um UUID válido quando sucesso"""
        from app.integrations.bank_partner import bank_partner_request

        # Mocka random para garantir sucesso (> 0.3)
        with patch("app.integrations.bank_partner.random.random", return_value=0.5):
            result = await bank_partner_request(
                external_id=uuid.uuid4(),
                amount=100,
                kind="credit",
            )

        # Resultado deve ser um UUID válido
        uuid.UUID(result)  # Levanta exceção se inválido

    @pytest.mark.asyncio
    async def test_bank_partner_raises_error(self):
        """bank_partner_request deve levantar BankPartnerError quando falha"""
        from app.core.exceptions import BankPartnerError
        from app.integrations.bank_partner import bank_partner_request

        # Mocka random para garantir falha (< 0.3)
        with patch("app.integrations.bank_partner.random.random", return_value=0.1):
            with pytest.raises(BankPartnerError):
                await bank_partner_request(
                    external_id=uuid.uuid4(),
                    amount=100,
                    kind="credit",
                )
