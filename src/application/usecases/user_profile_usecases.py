# src/application/usecases/user_profile_usecases.py
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.application.interfaces.repositories.user_profile_repository_interface import UserProfileRepositoryInterface
from src.application.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.entities.user_profile import UserProfile, Currency, Theme


class UserProfileUseCases:
    """Casos de uso relacionados a perfis de usuário."""
    
    def __init__(
        self, 
        user_profile_repository: UserProfileRepositoryInterface,
        user_repository: UserRepositoryInterface
    ):
        """
        Inicializa os casos de uso de perfil de usuário.
        
        Args:
            user_profile_repository: Implementação do repositório de perfis de usuário
            user_repository: Implementação do repositório de usuários
        """
        self.user_profile_repository = user_profile_repository
        self.user_repository = user_repository
    
    async def get_or_create_profile(self, user_id: UUID) -> UserProfile:
        """
        Obtém o perfil de um usuário ou cria um novo se não existir.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O perfil do usuário
        """
        # Verifica se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            raise ValueError(f"Usuário com ID {user_id} não encontrado")
        
        # Tenta obter o perfil existente
        profile = await self.user_profile_repository.get_by_user_id(user_id)
        
        # Se não existir, cria um novo perfil com valores padrão
        if not profile:
            profile = UserProfile.create(user_id)
            await self.user_profile_repository.add(profile)
        
        return profile
    
    async def update_profile(self, user_id: UUID, profile_data: Dict[str, Any]) -> UserProfile:
        """
        Atualiza o perfil de um usuário.
        
        Args:
            user_id: ID do usuário
            profile_data: Dados do perfil a serem atualizados
            
        Returns:
            O perfil atualizado
            
        Raises:
            ValueError: Se o usuário não for encontrado ou o perfil não puder ser atualizado
        """
        # Obtém ou cria o perfil
        profile = await self.get_or_create_profile(user_id)
        
        # Validações específicas para cada campo
        if "currency" in profile_data:
            try:
                profile_data["currency"] = Currency(profile_data["currency"])
            except ValueError:
                raise ValueError(f"Moeda inválida: {profile_data['currency']}")
        
        if "theme" in profile_data:
            try:
                profile_data["theme"] = Theme(profile_data["theme"])
            except ValueError:
                raise ValueError(f"Tema inválido: {profile_data['theme']}")
        
        # Atualiza o perfil
        updated_profile = await self.user_profile_repository.update(profile.id, profile_data)
        
        if not updated_profile:
            raise ValueError("Não foi possível atualizar o perfil")
        
        return updated_profile
    
    async def get_shared_profiles(self, user_id: UUID) -> List[UserProfile]:
        """
        Obtém os perfis compartilhados com um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de perfis compartilhados com o usuário
        """
        return await self.user_profile_repository.get_shared_with(user_id)
    
    async def share_profile(self, owner_id: UUID, target_user_id: UUID) -> bool:
        """
        Compartilha o perfil de um usuário com outro.
        
        Args:
            owner_id: ID do usuário proprietário do perfil
            target_user_id: ID do usuário com quem compartilhar
            
        Returns:
            True se o perfil foi compartilhado com sucesso, False caso contrário
            
        Raises:
            ValueError: Se algum dos usuários não for encontrado
        """
        # Verifica se os usuários existem
        owner = await self.user_repository.get_by_id(owner_id)
        if not owner:
            raise ValueError(f"Usuário proprietário com ID {owner_id} não encontrado")
        
        target = await self.user_repository.get_by_id(target_user_id)
        if not target:
            raise ValueError(f"Usuário alvo com ID {target_user_id} não encontrado")
        
        # Obtém ou cria o perfil do proprietário
        profile = await self.get_or_create_profile(owner_id)
        
        # Compartilha o perfil
        return await self.user_profile_repository.share_with(profile.id, target_user_id)
    
    async def unshare_profile(self, owner_id: UUID, target_user_id: UUID) -> bool:
        """
        Remove o compartilhamento do perfil de um usuário com outro.
        
        Args:
            owner_id: ID do usuário proprietário do perfil
            target_user_id: ID do usuário com quem parar de compartilhar
            
        Returns:
            True se o compartilhamento foi removido com sucesso, False caso contrário
        """
        # Obtém o perfil do proprietário
        profile = await self.user_profile_repository.get_by_user_id(owner_id)
        if not profile:
            return False
        
        # Remove o compartilhamento
        return await self.user_profile_repository.unshare_with(profile.id, target_user_id)