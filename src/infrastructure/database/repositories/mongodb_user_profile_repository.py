# src/infrastructure/database/repositories/mongodb_user_profile_repository.py
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.application.interfaces.repositories.user_profile_repository_interface import UserProfileRepositoryInterface
from src.domain.entities.user_profile import UserProfile
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.infrastructure.database.mongodb.models.user_profile_model import UserProfileModel


class MongoDBUserProfileRepository(UserProfileRepositoryInterface):
    """Implementação do repositório de perfis de usuário usando MongoDB."""
    
    def __init__(self):
        """Inicializa o repositório com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.collection = self.connection.db.user_profiles
    
    async def add(self, profile: UserProfile) -> UserProfile:
        """
        Adiciona um novo perfil de usuário.
        
        Args:
            profile: O perfil de usuário a ser adicionado
            
        Returns:
            O perfil de usuário adicionado com ID atualizado
        """
        profile_dict = UserProfileModel.to_dict(profile)
        await self.collection.insert_one(profile_dict)
        return profile
    
    async def get_by_id(self, profile_id: UUID) -> Optional[UserProfile]:
        """
        Recupera um perfil de usuário pelo ID.
        
        Args:
            profile_id: ID do perfil de usuário
            
        Returns:
            O perfil de usuário encontrado ou None
        """
        data = await self.collection.find_one({"_id": str(profile_id)})
        return UserProfileModel.from_dict(data)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[UserProfile]:
        """
        Recupera um perfil de usuário pelo ID do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O perfil de usuário encontrado ou None
        """
        data = await self.collection.find_one({"userId": str(user_id)})
        return UserProfileModel.from_dict(data)
    
    async def get_shared_with(self, user_id: UUID) -> List[UserProfile]:
        """
        Recupera todos os perfis compartilhados com o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de perfis de usuário compartilhados com o usuário
        """
        cursor = self.collection.find({"sharedWithUsers": str(user_id)})
        profiles = []
        
        async for document in cursor:
            profile = UserProfileModel.from_dict(document)
            if profile:
                profiles.append(profile)
                
        return profiles
    
    async def update(self, profile_id: UUID, data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Atualiza um perfil de usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O perfil de usuário atualizado ou None se não encontrado
        """
        # Converte as chaves para o formato do MongoDB
        update_data = {}
        key_map = {
            "currency": "currency",
            "language": "language",
            "theme": "theme",
            "notification_email": "notificationEmail",
            "notification_push": "notificationPush",
            "monthly_budget": "monthlyBudget",
            "dashboard_widgets": "dashboardWidgets",
            "extra_settings": "extraSettings",
            "shared_with_users": "sharedWithUsers"
        }
        
        for key, value in data.items():
            if key in key_map:
                mongodb_key = key_map[key]
                
                # Tratamento especial para shared_with_users (converte UUIDs para strings)
                if key == "shared_with_users" and isinstance(value, list):
                    value = [str(user_id) for user_id in value]
                
                update_data[mongodb_key] = value
                
        # Sempre atualiza a data de atualização
        from datetime import datetime
        update_data["updatedAt"] = datetime.now()
        
        result = await self.collection.update_one(
            {"_id": str(profile_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
            
        return await self.get_by_id(profile_id)
    
    async def delete(self, profile_id: UUID) -> bool:
        """
        Remove um perfil de usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        result = await self.collection.delete_one({"_id": str(profile_id)})
        return result.deleted_count > 0
    
    async def share_with(self, profile_id: UUID, user_id: UUID) -> bool:
        """
        Compartilha um perfil de usuário com outro usuário.
        
        Args:
            profile_id: ID do perfil de usuário a ser compartilhado
            user_id: ID do usuário com quem compartilhar
            
        Returns:
            True se compartilhado com sucesso, False caso contrário
        """
        result = await self.collection.update_one(
            {"_id": str(profile_id)},
            {"$addToSet": {"sharedWithUsers": str(user_id)}}
        )
        
        return result.modified_count > 0
    
    async def unshare_with(self, profile_id: UUID, user_id: UUID) -> bool:
        """
        Remove o compartilhamento de um perfil de usuário com outro usuário.
        
        Args:
            profile_id: ID do perfil de usuário
            user_id: ID do usuário com quem parar de compartilhar
            
        Returns:
            True se o compartilhamento foi removido com sucesso, False caso contrário
        """
        result = await self.collection.update_one(
            {"_id": str(profile_id)},
            {"$pull": {"sharedWithUsers": str(user_id)}}
        )
        
        return result.modified_count > 0