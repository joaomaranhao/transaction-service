import uuid
from unittest.mock import AsyncMock, patch

import pytest


class TestCreateTransactionWithMessaging:
    """Testes de integração da criação de transação com mensageria"""

    def test_transaction_created_with_pending_status(self, client):
        """Transação deve ser criada com status pending"""
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
        assert response.json()["status"] == "pending"

    def test_publish_called_on_transaction_creation(self, client, session):
        """Deve publicar transação na fila após criar"""
        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ) as mock_publish:
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
            transaction_id = response.json()["id"]
            mock_publish.assert_called_once_with(transaction_id)

    def test_publish_not_called_for_duplicate(self, client):
        """Não deve publicar para transação duplicada"""
        external_id = str(uuid.uuid4())

        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ) as mock_publish:
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

            # Publish só deve ser chamado uma vez
            assert mock_publish.call_count == 1

    def test_publish_not_called_for_invalid_amount(self, client):
        """Não deve publicar para transação com valor inválido"""
        with patch(
            "app.services.transaction_service.publish_transaction",
            new_callable=AsyncMock,
        ) as mock_publish:
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": -100,
                    "kind": "credit",
                    "account_id": "1",
                },
            )

            mock_publish.assert_not_called()


class TestBankPartnerUnit:
    """Testes unitários da função bank_partner_request"""

    @pytest.mark.asyncio
    async def test_bank_partner_returns_uuid(self):
        """bank_partner_request deve retornar um UUID válido quando sucesso"""
        from app.integrations.bank_partner import bank_partner_request
        from app.models.transaction import KindEnum

        # Mocka random para garantir sucesso (> 0.3)
        with patch("app.integrations.bank_partner.random.random", return_value=0.5):
            result = await bank_partner_request(
                external_id=uuid.uuid4(),
                amount=100,
                kind=KindEnum.CREDIT,
            )

        # Resultado deve ser um UUID válido
        uuid.UUID(result)  # Levanta exceção se inválido

    @pytest.mark.asyncio
    async def test_bank_partner_raises_error(self):
        """bank_partner_request deve levantar BankPartnerError quando falha"""
        from app.core.exceptions import BankPartnerError
        from app.integrations.bank_partner import bank_partner_request
        from app.models.transaction import KindEnum

        # Mocka random para garantir falha (< 0.3)
        with patch("app.integrations.bank_partner.random.random", return_value=0.1):
            with pytest.raises(BankPartnerError):
                await bank_partner_request(
                    external_id=uuid.uuid4(),
                    amount=100,
                    kind=KindEnum.CREDIT,
                )
