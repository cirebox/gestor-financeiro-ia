# src/application/interfaces/repositories/user_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.user import User


class UserRepositoryInterface(ABC):
    """Interface para repositório de usuários."""
    
    @abstractmethod
    async def add(self, user: User) -> User:
        """
        Adiciona um novo usuário.
        
        Args:
            user: O usuário a ser adicionado
            
        Returns:
            O usuário adicionado com ID atualizado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Recupera um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        pass
    
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Recupera um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        pass
    
    @abstractmethod
    async def update(self, user_id: UUID, data: dict) -> Optional[User]:
        """
        Atualiza um usuário.
        
        Args:
            user_id: ID do usuário a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O usuário atualizado ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: UUID) -> bool:
        """
        Remove um usuário.
        
        Args:
            user_id: ID do usuário a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        pass