from app.core.exceptions import AccountNotFoundError
from app.repositories.transaction_repository import TransactionRepository


class AccountService:

    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def get_balance(self, account_id: str) -> float:

        exists = self.repository.account_exists(account_id)

        if not exists:
            raise AccountNotFoundError()

        return self.repository.get_balance(account_id)
