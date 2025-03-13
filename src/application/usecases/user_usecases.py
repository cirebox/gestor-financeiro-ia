# src/application/usecases/user_usecases.py
from typing import Optional
from uuid import UUID

from src.application.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.domain.entities.user import User


class UserUseCases:
    """Casos de uso relacionados a usuários."""
    
    def __init__(self, user_repository: UserRepositoryInterface):
        """
        Inicializa os casos de uso de usuário.
        
        Args:
            user_repository: Implementação do repositório de usuários
        """
        self.user_repository = user_repository
    
    async def create_user(self, name: str, email: str) -> User:
        """
        Cria um novo usuário.
        
        Args:
            name: Nome do usuário
            email: Email do usuário
            
        Returns:
            O usuário criado
            
        Raises:
            ValueError: Se um usuário com o mesmo email já existir
        """
        # Verifica se já existe um usuário com o mesmo email
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError(f"Um usuário com o email '{email}' já existe")
        
        # Cria o usuário
        user = User.create(
            name=name,
            email=email
        )
        
        # Adiciona o usuário ao repositório
        return await self.user_repository.add(user)
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Recupera um usuário pelo ID.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        return await self.user_repository.get_by_id(user_id)
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Recupera um usuário pelo email.
        
        Args:
            email: Email do usuário
            
        Returns:
            O usuário encontrado ou None
        """
        return await self.user_repository.get_by_email(email)
    
    async def update_user(self, user_id: UUID, name: Optional[str] = None, email: Optional[str] = None) -> Optional[User]:
        """
        Atualiza um usuário.
        
        Args:
            user_id: ID do usuário a ser atualizado
            name: Novo nome (opcional)
            email: Novo email (opcional)
            
        Returns:
            O usuário atualizado ou None se não encontrado
            
        Raises:
            ValueError: Se um usuário com o novo email já existir
        """
        # Verifica se o usuário existe
        user = await self.user_repository.get_by_id(user_id)
        if not user:
            return None
        
        # Prepara os dados para atualização
        update_data = {}
        
        if name is not None:
            update_data["name"] = name
        
        if email is not None and email != user.email:
            # Verifica se o novo email já está em uso
            existing_user = await self.user_repository.get_by_email(email)
            if existing_user and existing_user.id != user_id:
                raise ValueError(f"Um usuário com o email '{email}' já existe")
            
            update_data["email"] = email
        
        if not update_data:
            # Nada para atualizar
            return user
        
        # Atualiza o usuário
        return await self.user_repository.update(user_id, update_data)
    
    async def delete_user(self, user_id: UUID) -> bool:
        """
        Remove um usuário.
        
        Args:
            user_id: ID do usuário a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        return await self.user_repository.delete(user_id)