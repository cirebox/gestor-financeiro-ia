# src/domain/value_objects/money.py
from dataclasses import dataclass
from decimal import Decimal
from typing import Union


@dataclass(frozen=True)
class Money:
    """Value Object que representa um valor monetário."""
    
    amount: Decimal
    
    def __init__(self, amount: Union[Decimal, float, int, str]):
        """
        Inicializa um novo objeto Money.
        
        Args:
            amount: O valor monetário (Decimal, float, int ou str)
        """
        if isinstance(amount, str):
            # Remove R$ e outros caracteres não numéricos
            amount = amount.replace('R$', '').replace(' ', '')
            # Substitui vírgula por ponto
            amount = amount.replace(',', '.')
            
        # Frozen=True não permite atribuição direta, então usamos object.__setattr__
        object.__setattr__(self, 'amount', Decimal(str(amount)).quantize(Decimal('0.01')))
        
    def __add__(self, other: 'Money') -> 'Money':
        """Soma dois valores monetários."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return Money(self.amount + other.amount)
        
    def __sub__(self, other: 'Money') -> 'Money':
        """Subtrai dois valores monetários."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return Money(self.amount - other.amount)
        
    def __mul__(self, factor: Union[int, float, Decimal]) -> 'Money':
        """Multiplica o valor monetário por um fator."""
        return Money(self.amount * Decimal(str(factor)))
        
    def __truediv__(self, divisor: Union[int, float, Decimal]) -> 'Money':
        """Divide o valor monetário por um divisor."""
        if divisor == 0:
            raise ZeroDivisionError("Divisão por zero")
        return Money(self.amount / Decimal(str(divisor)))
        
    def __lt__(self, other: 'Money') -> bool:
        """Verifica se este valor é menor que outro."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return self.amount < other.amount
        
    def __le__(self, other: 'Money') -> bool:
        """Verifica se este valor é menor ou igual a outro."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return self.amount <= other.amount
        
    def __gt__(self, other: 'Money') -> bool:
        """Verifica se este valor é maior que outro."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return self.amount > other.amount
        
    def __ge__(self, other: 'Money') -> bool:
        """Verifica se este valor é maior ou igual a outro."""
        if not isinstance(other, Money):
            raise TypeError("Operando deve ser do tipo Money")
        return self.amount >= other.amount
    
    def __eq__(self, other: object) -> bool:
        """Verifica se este valor é igual a outro."""
        if not isinstance(other, Money):
            return False
        return self.amount == other.amount
    
    def __ne__(self, other: object) -> bool:
        """Verifica se este valor é diferente de outro."""
        return not self.__eq__(other)
    
    def __str__(self) -> str:
        """Retorna uma representação em string formatada como moeda."""
        return f"R$ {self.amount:.2f}"
    
    def __repr__(self) -> str:
        """Retorna uma representação para debugging."""
        return f"Money({self.amount})"
    
    def __hash__(self) -> int:
        """Retorna um hash para uso em dicionários e conjuntos."""
        return hash(self.amount)
    
    def is_positive(self) -> bool:
        """Verifica se o valor é positivo."""
        return self.amount > Decimal('0')
    
    def is_negative(self) -> bool:
        """Verifica se o valor é negativo."""
        return self.amount < Decimal('0')
    
    def is_zero(self) -> bool:
        """Verifica se o valor é zero."""
        return self.amount == Decimal('0')
    
    def absolute(self) -> 'Money':
        """Retorna o valor absoluto."""
        return Money(abs(self.amount))
    
    def negate(self) -> 'Money':
        """Retorna o valor negado."""
        return Money(-self.amount)
    
    def percentage_of(self, percent: float) -> 'Money':
        """Calcula uma porcentagem deste valor."""
        if percent < 0:
            raise ValueError("Porcentagem não pode ser negativa")
        return Money(self.amount * Decimal(str(percent)) / Decimal('100'))
    
    def allocate(self, ratios: list) -> list['Money']:
        """
        Aloca o valor total conforme uma lista de proporções.
        
        Args:
            ratios: Lista de proporções para alocação
            
        Returns:
            Lista de valores Money alocados conforme as proporções
        
        Exemplo:
            Money(10).allocate([1, 1, 1]) -> [Money(3.34), Money(3.33), Money(3.33)]
        """
        if not ratios:
            return []
        
        total = sum(ratios)
        if total <= 0:
            raise ValueError("A soma das proporções deve ser maior que zero")
        
        # Converte para inteiros para evitar erros de arredondamento
        precision = Decimal('0.01')
        cents = int(self.amount / precision)
        
        # Aloca centavos proporcionalmente
        result = []
        remaining_cents = cents
        
        for ratio in ratios[:-1]:  # Processa todos menos o último
            share = int(Decimal(ratio) / Decimal(total) * cents)
            result.append(Money(share * precision))
            remaining_cents -= share
        
        # O último recebe o restante para garantir que a soma é exata
        result.append(Money(remaining_cents * precision))
        
        return result