# src/domain/entities/transaction.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Union, List
from uuid import UUID, uuid4

from src.domain.value_objects.money import Money
from src.domain.value_objects.recurrence import Recurrence


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
    priority: Optional[str] = None  # 'alta', 'média', 'baixa'
    recurrence: Optional[Recurrence] = None
    installment_info: Optional[dict] = None  # Para parcelamentos: {'total': 12, 'current': 1, 'reference_id': UUID}
    tags: List[str] = None  # Tags para classificação adicional
    
    @classmethod
    def create(cls, 
               user_id: UUID, 
               type: str, 
               amount: Union[Money, float], 
               category: str, 
               description: str, 
               date: Optional[datetime] = None,
               priority: Optional[str] = None,
               recurrence: Optional[Recurrence] = None,
               installment_info: Optional[dict] = None,
               tags: Optional[List[str]] = None) -> 'Transaction':
        """
        Cria uma nova instância de Transaction.
        
        Args:
            user_id: ID do usuário proprietário da transação
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação (Money ou float)
            category: Categoria da transação
            description: Descrição da transação
            date: Data da transação (opcional, padrão é agora)
            priority: Prioridade da transação ('alta', 'média', 'baixa')
            recurrence: Informações de recorrência
            installment_info: Informações de parcelamento
            tags: Lista de tags para classificação adicional
            
        Returns:
            Uma nova instância de Transaction
        """
        if not isinstance(amount, Money):
            amount = Money(amount)
            
        if date is None:
            date = datetime.now()
            
        if type not in ('income', 'expense'):
            raise ValueError("O tipo deve ser 'income' ou 'expense'")
            
        if priority is not None and priority not in ('alta', 'média', 'baixa'):
            raise ValueError("A prioridade deve ser 'alta', 'média' ou 'baixa'")
            
        return cls(
            id=uuid4(),
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=date,
            created_at=datetime.now(),
            priority=priority,
            recurrence=recurrence,
            installment_info=installment_info,
            tags=tags or []
        )
        
    def is_recurring(self) -> bool:
        """Verifica se a transação é recorrente."""
        return self.recurrence is not None
        
    def is_installment(self) -> bool:
        """Verifica se a transação é parcelada."""
        return self.installment_info is not None