import uuid
from unittest.mock import AsyncMock, patch

from app.core.exceptions import BankPartnerError


class TestGetBalance:
    """Testes para o endpoint GET /accounts/{account_id}/balance"""

    def test_get_balance_account_not_found(self, client):
        """Deve retornar 404 quando conta não existe"""
        response = client.get("/accounts/nonexistent/balance")

        assert response.status_code == 404
        assert response.json()["detail"] == "Account not found"

    def test_get_balance_with_no_transactions(self, client, session):
        """Deve retornar 404 quando conta não tem transações"""
        response = client.get("/accounts/123/balance")

        assert response.status_code == 404

    def test_get_balance_with_credit_transactions(self, client):
        """Deve retornar saldo correto com transações de crédito"""
        account_id = "test-account-1"

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            # Cria duas transações de crédito
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 100,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 50,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == account_id
        assert data["balance"] == 150

    def test_get_balance_with_debit_transactions(self, client):
        """Deve retornar saldo correto com transações de débito"""
        account_id = "test-account-2"

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            # Cria transação de crédito e débito
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 200,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 75,
                    "kind": "debit",
                    "account_id": account_id,
                },
            )

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        assert response.json()["balance"] == 125  # 200 - 75

    def test_get_balance_negative(self, client):
        """Deve retornar saldo negativo quando débitos excedem créditos"""
        account_id = "test-account-3"

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 50,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 100,
                    "kind": "debit",
                    "account_id": account_id,
                },
            )

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        assert response.json()["balance"] == -50

    def test_get_balance_ignores_pending_transactions(self, client):
        """Deve ignorar transações pendentes no cálculo do saldo"""
        account_id = "test-account-4"

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            # Transação completada
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 100,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            side_effect=BankPartnerError("Erro"),
        ):
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 500,
                    "kind": "credit",
                    "account_id": account_id,
                },
            )

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        # Saldo deve ser apenas da transação completada
        assert response.json()["balance"] == 100

    def test_get_balance_different_accounts_isolated(self, client):
        """Saldos de diferentes contas devem ser isolados"""
        account_1 = "account-a"
        account_2 = "account-b"

        with patch(
            "app.services.transaction_service.bank_partner_request",
            new_callable=AsyncMock,
            return_value=str(uuid.uuid4()),
        ):
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 100,
                    "kind": "credit",
                    "account_id": account_1,
                },
            )
            client.post(
                "/transaction",
                json={
                    "external_id": str(uuid.uuid4()),
                    "amount": 300,
                    "kind": "credit",
                    "account_id": account_2,
                },
            )

        response_1 = client.get(f"/accounts/{account_1}/balance")
        response_2 = client.get(f"/accounts/{account_2}/balance")

        assert response_1.json()["balance"] == 100
        assert response_2.json()["balance"] == 300
