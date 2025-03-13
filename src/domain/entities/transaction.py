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
    due_date: Optional[datetime] = None  # Data de vencimento
    is_paid: bool = False  # Indica se foi quitada
    paid_date: Optional[datetime] = None  # Data em que foi quitada
    
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
               tags: Optional[List[str]] = None,
               due_date: Optional[datetime] = None,
               is_paid: bool = False,
               paid_date: Optional[datetime] = None) -> 'Transaction':
        """
        Cria uma nova instância de Transaction.
        
        Args:
            user_id: ID do usuário proprietário da transação
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação (Money ou float)
            category: Categoria da transação
            description: Descrição da transação
            date: Data da transação (opcional)
            priority: Prioridade da transação ('alta', 'média', 'baixa')
            recurrence: Informações de recorrência
            installment_info: Informações de parcelamento
            tags: Lista de tags para classificação adicional
            due_date: Data de vencimento da transação
            is_paid: Se a transação foi quitada
            paid_date: Data em que a transação foi quitada
            
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
            
        # Se for marcada como quitada, mas não tiver data de quitação, usar data atual
        if is_paid and paid_date is None:
            paid_date = datetime.now()
            
        # Se for receita (income), considerar como paga por padrão
        if type == 'income' and is_paid is None:
            is_paid = True
            if paid_date is None:
                paid_date = date
            
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
            tags=tags or [],
            due_date=due_date,
            is_paid=is_paid,
            paid_date=paid_date
        )
        
    def is_recurring(self) -> bool:
        """Verifica se a transação é recorrente."""
        return self.recurrence is not None
        
    def is_installment(self) -> bool:
        """Verifica se a transação é parcelada."""
        return self.installment_info is not None
        
    def is_overdue(self) -> bool:
        """Verifica se a transação está vencida (apenas para despesas não pagas)."""
        if self.type != 'expense' or self.is_paid:
            return False
            
        if self.due_date is None:
            return False
            
        return self.due_date < datetime.now()
        
    def days_to_due(self) -> Optional[int]:
        """Retorna o número de dias até o vencimento (ou desde o vencimento, se negativo)."""
        if self.due_date is None:
            return None
            
        delta = self.due_date - datetime.now()
        return delta.days
        
    def mark_as_paid(self, paid_date: Optional[datetime] = None) -> None:
        """
        Marca a transação como paga.
        
        Args:
            paid_date: Data em que foi paga (padrão é a data atual)
        """
        self.is_paid = True
        self.paid_date = paid_date or datetime.now()