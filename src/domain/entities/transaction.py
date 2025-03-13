# src/domain/entities/transaction.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union
from uuid import UUID, uuid4

from src.domain.value_objects.money import Money


@dataclass
class Transaction:
    """Entidade que representa uma transação financeira."""
    
    id: UUID
    user_id: UUID
    type: str  # 'income' ou 'expense'
    amount: Money
    category: str
    description: str
    date: datetime
    created_at: datetime
    
    @classmethod
    def create(cls, 
               user_id: UUID, 
               type: str, 
               amount: Union[Money, float], 
               category: str, 
               description: str, 
               date: Optional[datetime] = None) -> 'Transaction':
        """
        Cria uma nova instância de Transaction.
        
        Args:
            user_id: ID do usuário proprietário da transação
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação (Money ou float)
            category: Categoria da transação
            description: Descrição da transação
            date: Data da transação (opcional, padrão é agora)
            
        Returns:
            Uma nova instância de Transaction
        """
        if not isinstance(amount, Money):
            amount = Money(amount)
            
        if date is None:
            date = datetime.now()
            
        if type not in ('income', 'expense'):
            raise ValueError("O tipo deve ser 'income' ou 'expense'")
            
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=date,
            created_at=datetime.now()
        )