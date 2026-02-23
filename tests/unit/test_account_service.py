from unittest.mock import MagicMock

import pytest

from app.core.exceptions import AccountNotFoundError
from app.services.account_services import AccountService


@pytest.fixture
def mock_repository():
    """Mock do TransactionRepository"""
    return MagicMock()


@pytest.fixture
def service(mock_repository):
    """Instância do AccountService com repository mockado"""
    return AccountService(mock_repository)


class TestGetBalance:
    """Testes unitários para get_balance"""

    def test_returns_balance_when_account_exists(self, service, mock_repository):
        """Deve retornar o saldo quando a conta existe"""
        mock_repository.account_exists.return_value = True
        mock_repository.get_balance.return_value = 150.50

        balance = service.get_balance("123")

        assert balance == 150.50
        mock_repository.account_exists.assert_called_once_with("123")
        mock_repository.get_balance.assert_called_once_with("123")

    def test_raises_error_when_account_not_found(self, service, mock_repository):
        """Deve levantar AccountNotFoundError quando conta não existe"""
        mock_repository.account_exists.return_value = False

        with pytest.raises(AccountNotFoundError):
            service.get_balance("nonexistent")

        mock_repository.account_exists.assert_called_once_with("nonexistent")
        mock_repository.get_balance.assert_not_called()

    def test_returns_zero_balance(self, service, mock_repository):
        """Deve retornar saldo zero quando conta existe sem transações"""
        mock_repository.account_exists.return_value = True
        mock_repository.get_balance.return_value = 0.0

        balance = service.get_balance("empty-account")

        assert balance == 0.0

    def test_returns_negative_balance(self, service, mock_repository):
        """Deve retornar saldo negativo quando débitos excedem créditos"""
        mock_repository.account_exists.return_value = True
        mock_repository.get_balance.return_value = -100.0

        balance = service.get_balance("negative-account")

        assert balance == -100.0

    def test_calls_repository_with_correct_account_id(self, service, mock_repository):
        """Deve chamar repository com account_id correto"""
        mock_repository.account_exists.return_value = True
        mock_repository.get_balance.return_value = 50.0

        service.get_balance("my-account-id")

        mock_repository.account_exists.assert_called_once_with("my-account-id")
        mock_repository.get_balance.assert_called_once_with("my-account-id")


class TestAccountServiceInit:
    """Testes de inicialização do service"""

    def test_initializes_with_repository(self, mock_repository):
        """Deve inicializar com repository"""
        service = AccountService(mock_repository)

        assert service.repository == mock_repository
