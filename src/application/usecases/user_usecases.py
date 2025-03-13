# src/application/usecases/user_usecases.py
from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from src.application.interfaces.repositories.user_repository_interface import UserRepositoryInterface
from src.application.security.password import get_password_hash, verify_password
from src.application.security.token import create_access_token, create_refresh_token
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
    
    async def create_user(self, name: str, email: str, password: str) -> User:
        """
        Cria um novo usuário.
        
        Args:
            name: Nome do usuário
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            O usuário criado
            
        Raises:
            ValueError: Se um usuário com o mesmo email já existir
        """
        # Verifica se já existe um usuário com o mesmo email
        existing_user = await self.user_repository.get_by_email(email)
        if existing_user:
            raise ValueError(f"Um usuário com o email '{email}' já existe")
        
        # Gera o hash da senha
        password_hash = get_password_hash(password)
        
        # Cria o usuário
        user = User.create(
            name=name,
            email=email,
            password_hash=password_hash
        )
        
        # Adiciona o usuário ao repositório
        return await self.user_repository.add(user)
    
    async def authenticate_user(self, email: str, password: str) -> Tuple[bool, Optional[User]]:
        """
        Autentica um usuário com email e senha.
        
        Args:
            email: Email do usuário
            password: Senha do usuário
            
        Returns:
            Uma tupla contendo um booleano que indica se a autenticação foi bem-sucedida
            e o usuário autenticado (ou None se a autenticação falhar)
        """
        user = await self.user_repository.get_by_email(email)
        
        if not user:
            return False, None
            
        if not verify_password(password, user.password_hash):
            return False, None
            
        # Atualiza a data do último login
        update_data = {"last_login": datetime.now()}
        updated_user = await self.user_repository.update(user.id, update_data)
        
        return True, updated_user or user
    
    async def generate_tokens(self, user: User) -> dict:
        """
        Gera tokens de acesso e atualização para um usuário.
        
        Args:
            user: Usuário para o qual gerar tokens
            
        Returns:
            Dicionário contendo o token de acesso e o token de atualização
        """
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
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
    
    async def update_user(self, user_id: UUID, name: Optional[str] = None, 
                          email: Optional[str] = None, password: Optional[str] = None,
                          is_active: Optional[bool] = None) -> Optional[User]:
        """
        Atualiza um usuário.
        
        Args:
            user_id: ID do usuário a ser atualizado
            name: Novo nome (opcional)
            email: Novo email (opcional)
            password: Nova senha (opcional)
            is_active: Novo status de ativação (opcional)
            
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
            
        if password is not None:
            update_data["password_hash"] = get_password_hash(password)
            
        if is_active is not None:
            update_data["is_active"] = is_active
        
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
        
    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        """
        Altera a senha de um usuário.
        
        Args:
            user_id: ID do usuário
            current_password: Senha atual
            new_password: Nova senha
            
        Returns:
            True se a senha foi alterada com sucesso, False caso contrário
            
        Raises:
            ValueError: Se a senha atual estiver incorreta
        """
        user = await self.user_repository.get_by_id(user_id)
        
        if not user:
            return False
            
        # Verifica a senha atual
        if not verify_password(current_password, user.password_hash):
            raise ValueError("Senha atual incorreta")
            
        # Gera o hash da nova senha
        password_hash = get_password_hash(new_password)
        
        # Atualiza a senha
        update_data = {"password_hash": password_hash}
        updated_user = await self.user_repository.update(user_id, update_data)
        
        return updated_user is not None