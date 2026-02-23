class BankPartnerError(Exception):
    """Exceção para erros relacionados ao banco parceiro."""

    def __init__(self, message: str = "Erro na comunicação com banco parceiro"):
        self.message = message
        super().__init__(self.message)


class AccountNotFoundError(Exception):
    """Exceção para quando uma conta não é encontrada."""

    pass


class InvalidTransactionAmountError(Exception):
    """Exceção para quando um valor de transação é inválido."""

    pass
