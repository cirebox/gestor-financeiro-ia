# src/application/security/password_reset.py
import secrets
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

from src.domain.entities.user import User
from src.application.interfaces.repositories.user_repository_interface import UserRepositoryInterface


class PasswordResetToken(BaseModel):
    """Modelo para representar um token de redefinição de senha."""
    
    token: str
    user_id: str
    expires_at: datetime
    
    @classmethod
    def create(cls, user_id: str, expires_in_minutes: int = 30) -> 'PasswordResetToken':
        """
        Cria um novo token de redefinição de senha.
        
        Args:
            user_id: ID do usuário
            expires_in_minutes: Tempo de expiração em minutos
            
        Returns:
            Um novo token de redefinição de senha
        """
        return cls(
            token=secrets.token_urlsafe(64),
            user_id=user_id,
            expires_at=datetime.now() + timedelta(minutes=expires_in_minutes)
        )
    
    def is_valid(self) -> bool:
        """
        Verifica se o token ainda é válido.
        
        Returns:
            True se o token ainda for válido, False caso contrário
        """
        return datetime.now() < self.expires_at


class PasswordResetService:
    """Serviço para gerenciar tokens de redefinição de senha."""
    
    # Armazenamento em memória para tokens (em produção, deveria ser um banco de dados)
    _tokens = {}
    
    @classmethod
    def create_token(cls, user_id: str, expires_in_minutes: int = 30) -> PasswordResetToken:
        """
        Cria um novo token de redefinição de senha.
        
        Args:
            user_id: ID do usuário
            expires_in_minutes: Tempo de expiração em minutos
            
        Returns:
            O token criado
        """
        token = PasswordResetToken.create(user_id, expires_in_minutes)
        cls._tokens[token.token] = token
        return token
    
    @classmethod
    def validate_token(cls, token_str: str) -> Optional[PasswordResetToken]:
        """
        Valida um token de redefinição de senha.
        
        Args:
            token_str: String do token
            
        Returns:
            O token se for válido, None caso contrário
        """
        token = cls._tokens.get(token_str)
        if token and token.is_valid():
            return token
        return None
    
    @classmethod
    def invalidate_token(cls, token_str: str) -> None:
        """
        Invalida um token de redefinição de senha.
        
        Args:
            token_str: String do token
        """
        if token_str in cls._tokens:
            del cls._tokens[token_str]
    
    @classmethod
    async def process_password_reset(
        cls, 
        token_str: str, 
        new_password: str, 
        user_repository: UserRepositoryInterface
    ) -> bool:
        """
        Processa um pedido de redefinição de senha.
        
        Args:
            token_str: String do token
            new_password: Nova senha
            user_repository: Repositório de usuários
            
        Returns:
            True se a senha foi redefinida com sucesso, False caso contrário
        """
        token = cls.validate_token(token_str)
        if not token:
            return False
        
        from uuid import UUID
        from src.application.security.password import get_password_hash
        
        # Atualiza a senha do usuário
        password_hash = get_password_hash(new_password)
        user_id = UUID(token.user_id)
        
        try:
            await user_repository.update(user_id, {"password_hash": password_hash})
            cls.invalidate_token(token_str)
            return True
        except Exception:
            return False