# src/infrastructure/database/repositories/mongodb_user_repository.py
from typing import List, Optional
from uuid import UUID

from src.application.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.entities.user import User
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.infrastructure.database.mongodb.models.user_model import UserModel


class MongoDBUserRepository(UserRepositoryInterface):
    """Implementação do repositório de usuários usando MongoDB."""
    
    def __init__(self):
        """Inicializa o repositório com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.collection = self.connection.db.users
    
    async def add(self, user: User) -> User:
        """
        Adiciona um novo usuário.
        
        Args:
            user: O usuário a ser adicionado
            
        Returns:
            O usuário adicionado com ID atualizado
        """
        user_dict = UserModel.to_dict(user)
        await self.collection.insert_one(user_dict)
        return user
    
    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Recupera um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        data = await self.collection.find_one({"_id": str(user_id)})
        return UserModel.from_dict(data)
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Recupera um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        data = await self.collection.find_one({"email": email})
        return UserModel.from_dict(data)
    
    async def update(self, user_id: UUID, data: dict) -> Optional[User]:
        """
        Atualiza um usuário.
        
        Args:
            user_id: ID do usuário a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O usuário atualizado ou None se não encontrado
        """
        # Filtra apenas campos permitidos
        update_data = {}
        allowed_fields = ["name", "email"]
        
        for field in allowed_fields:
            if field in data:
                update_data[field] = data[field]
        
        if not update_data:
            return None
        
        result = await self.collection.update_one(
            {"_id": str(user_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_by_id(user_id)
    
    async def delete(self, user_id: UUID) -> bool:
        """
        Remove um usuário.
        
        Args:
            user_id: ID do usuário a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        result = await self.collection.delete_one({"_id": str(user_id)})
        return result.deleted_count > 0