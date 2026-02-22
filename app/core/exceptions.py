class BankPartnerError(Exception):
    """Exceção para erros relacionados ao banco parceiro."""

    pass


class AccountNotFoundError(Exception):
    """Exceção para quando uma conta não é encontrada."""

    pass


class InvalidTransactionAmountError(Exception):
    """Exceção para quando um valor de transação é inválido."""

    pass
