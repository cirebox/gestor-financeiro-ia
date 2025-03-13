# src/domain/entities/category.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class Category:
    """Entidade que representa uma categoria de transação."""
    
    id: UUID
    name: str
    type: str  # 'income' ou 'expense'
    created_at: datetime
    
    @classmethod
    def create(cls, name: str, type: str) -> 'Category':
        """
        Cria uma nova instância de Category.
        
        Args:
            name: Nome da categoria
            type: Tipo da categoria ('income' ou 'expense')
            
        Returns:
            Uma nova instância de Category
        """
        if type not in ('income', 'expense'):
            raise ValueError("O tipo deve ser 'income' ou 'expense'")
            
        return cls(
            id=uuid4(),
            name=name,
            type=type,
            created_at=datetime.now()
        )