# src/application/interfaces/repositories/user_profile_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.entities.user_profile import UserProfile


class UserProfileRepositoryInterface(ABC):
    """Interface para repositório de perfis de usuário."""
    
    @abstractmethod
    async def add(self, profile: UserProfile) -> UserProfile:
        """
        Adiciona um novo perfil de usuário.
        
        Args:
            profile: O perfil de usuário a ser adicionado
            
        Returns:
            O perfil de usuário adicionado com ID atualizado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, profile_id: UUID) -> Optional[UserProfile]:
        """
        Recupera um perfil de usuário pelo ID.
        
        Args:
            profile_id: ID do perfil de usuário
            
        Returns:
            O perfil de usuário encontrado ou None
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Recupera um perfil de usuário pelo ID do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O perfil de usuário encontrado ou None
        """
        pass
    
    @abstractmethod
    async def get_shared_with(self, user_id: UUID) -> List[UserProfile]:
        """
        Recupera todos os perfis compartilhados com o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de perfis de usuário compartilhados com o usuário
        """
        pass
    
    @abstractmethod
    async def update(self, profile_id: UUID, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Atualiza um perfil de usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O perfil de usuário atualizado ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def delete(self, profile_id: UUID) -> bool:
        """
        Remove um perfil de usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def share_with(self, profile_id: UUID, user_id: UUID) -> bool:
        """
        Compartilha um perfil de usuário com outro usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser compartilhado
            user_id: ID do usuário com quem compartilhar
            
        Returns:
            True se compartilhado com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def unshare_with(self, profile_id: UUID, user_id: UUID) -> bool:
        """
        Remove o compartilhamento de um perfil de usuário com outro usuário.
        
        Args:
            profile_id: ID do perfil de usuário
            user_id: ID do usuário com quem parar de compartilhar
            
        Returns:
            True se o compartilhamento foi removido com sucesso, False caso contrário
        """
        pass