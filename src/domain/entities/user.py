# src/domain/entities/user.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class User:
    """Entidade que representa um usuário do sistema."""
    
    id: UUID
    name: str
    email: str
    created_at: datetime
    
    @classmethod
    def create(cls, name: str, email: str) -> 'User':
        """
        Cria uma nova instância de User.
        
        Args:
            name: Nome do usuário
            email: Email do usuário
            
        Returns:
            Uma nova instância de User
        """
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            created_at=datetime.now()
        )
