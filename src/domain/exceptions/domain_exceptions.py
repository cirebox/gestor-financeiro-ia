# src/domain/exceptions/domain_exceptions.py
class DomainException(Exception):
    """Exceção base para erros de domínio."""
    pass


class CategoryNotFoundException(DomainException):
    """Exceção lançada quando uma categoria não é encontrada."""
    pass


class InvalidTransactionTypeException(DomainException):
    """Exceção lançada quando um tipo de transação é inválido."""
    pass


class InvalidAmountException(DomainException):
    """Exceção lançada quando um valor de transação é inválido."""
    pass