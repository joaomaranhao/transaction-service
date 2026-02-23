import uuid

from app.models.transaction import KindEnum, Transaction


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

    def test_get_balance_with_credit_transactions(self, client, session):
        """Deve retornar saldo correto com transações de crédito"""
        account_id = "test-account-1"

        # Cria transações diretamente no banco com status completed
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=100,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=50,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.commit()

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        data = response.json()
        assert data["account_id"] == account_id
        assert data["balance"] == 150

    def test_get_balance_with_debit_transactions(self, client, session):
        """Deve retornar saldo correto com transações de débito"""
        account_id = "test-account-2"

        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=200,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=75,
                kind=KindEnum.DEBIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.commit()

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        assert response.json()["balance"] == 125  # 200 - 75

    def test_get_balance_negative(self, client, session):
        """Deve retornar saldo negativo quando débitos excedem créditos"""
        account_id = "test-account-3"

        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=50,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=100,
                kind=KindEnum.DEBIT,
                account_id=account_id,
                status="completed",
            )
        )
        session.commit()

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        assert response.json()["balance"] == -50

    def test_get_balance_ignores_pending_transactions(self, client, session):
        """Deve ignorar transações pendentes no cálculo do saldo"""
        account_id = "test-account-4"

        # Transação completada
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=100,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="completed",
            )
        )
        # Transação pendente - não deve contar
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=500,
                kind=KindEnum.CREDIT,
                account_id=account_id,
                status="pending",
            )
        )
        session.commit()

        response = client.get(f"/accounts/{account_id}/balance")

        assert response.status_code == 200
        # Saldo deve ser apenas da transação completada
        assert response.json()["balance"] == 100

    def test_get_balance_different_accounts_isolated(self, client, session):
        """Saldos de diferentes contas devem ser isolados"""
        account_1 = "account-a"
        account_2 = "account-b"

        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=100,
                kind=KindEnum.CREDIT,
                account_id=account_1,
                status="completed",
            )
        )
        session.add(
            Transaction(
                external_id=uuid.uuid4(),
                amount=300,
                kind=KindEnum.CREDIT,
                account_id=account_2,
                status="completed",
            )
        )
        session.commit()

        response_1 = client.get(f"/accounts/{account_1}/balance")
        response_2 = client.get(f"/accounts/{account_2}/balance")

        assert response_1.json()["balance"] == 100
        assert response_2.json()["balance"] == 300
