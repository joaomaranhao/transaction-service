import uuid

import pytest


class TestCreateTransaction:
    """Testes para criação de transações"""

    def test_create_credit_transaction(self, client):
        """Deve criar uma transação de crédito com sucesso"""
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

        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_create_debit_transaction(self, client):
        """Deve criar uma transação de débito com sucesso"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 50.5,
                "kind": "debit",
                "account_id": "123",
            },
        )

        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert data["status"] == "pending"

    def test_create_transaction_with_zero_amount(self, client):
        """Deve retornar 400 para transação com valor zero"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 0,
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Valor de transação deve ser maior que zero"

    def test_create_transaction_with_negative_amount(self, client):
        """Deve retornar 400 para transação com valor negativo"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": -100,
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 400
        assert response.json()["detail"] == "Valor de transação deve ser maior que zero"

    def test_create_transaction_idempotency(self, client):
        """Deve retornar a mesma transação quando external_id já existe"""
        external_id = str(uuid.uuid4())

        # Primeira requisição
        response1 = client.post(
            "/transaction",
            json={
                "external_id": external_id,
                "amount": 100,
                "kind": "credit",
                "account_id": "1",
            },
        )
        assert response1.status_code == 201
        data1 = response1.json()

        # Segunda requisição com mesmo external_id
        response2 = client.post(
            "/transaction",
            json={
                "external_id": external_id,
                "amount": 200,  # valor diferente
                "kind": "debit",  # tipo diferente
                "account_id": "2",  # conta diferente
            },
        )
        assert response2.status_code == 200  # 200 para existente, não 201
        data2 = response2.json()

        # Deve retornar a mesma transação (idempotência)
        assert data1["id"] == data2["id"]


class TestTransactionValidation:
    """Testes de validação do payload da transação"""

    def test_missing_external_id(self, client):
        """Deve retornar 422 quando external_id não é informado"""
        response = client.post(
            "/transaction",
            json={
                "amount": 100,
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    def test_missing_amount(self, client):
        """Deve retornar 422 quando amount não é informado"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    def test_missing_kind(self, client):
        """Deve retornar 422 quando kind não é informado"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 100,
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    def test_missing_account_id(self, client):
        """Deve retornar 422 quando account_id não é informado"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 100,
                "kind": "credit",
            },
        )

        assert response.status_code == 422

    def test_invalid_kind(self, client):
        """Deve retornar 422 quando kind é inválido"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 100,
                "kind": "invalid_kind",
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    def test_invalid_external_id_format(self, client):
        """Deve retornar 422 quando external_id não é um UUID válido"""
        response = client.post(
            "/transaction",
            json={
                "external_id": "not-a-valid-uuid",
                "amount": 100,
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    def test_invalid_amount_type(self, client):
        """Deve retornar 422 quando amount não é numérico"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": "cem",
                "kind": "credit",
                "account_id": "1",
            },
        )

        assert response.status_code == 422

    @pytest.mark.parametrize(
        "kind",
        ["credit", "debit"],
    )
    def test_valid_kind_values(self, client, kind):
        """Deve aceitar os valores válidos de kind"""
        response = client.post(
            "/transaction",
            json={
                "external_id": str(uuid.uuid4()),
                "amount": 100,
                "kind": kind,
                "account_id": "1",
            },
        )

        assert response.status_code == 201
