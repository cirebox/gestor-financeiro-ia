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
    password_hash: str
    is_active: bool = True
    is_admin: bool = False
    last_login: Optional[datetime] = None
    
    @classmethod
    def create(cls, name: str, email: str, password_hash: str) -> 'User':
        """
        Cria uma nova instância de User.
        
        Args:
            name: Nome do usuário
            email: Email do usuário
            password_hash: Hash da senha do usuário
            
        Returns:
            Uma nova instância de User
        """
        return cls(
            id=uuid4(),
            name=name,
            email=email,
            password_hash=password_hash,
            created_at=datetime.now()
        )