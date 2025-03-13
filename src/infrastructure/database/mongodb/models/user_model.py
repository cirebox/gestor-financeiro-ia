# src/infrastructure/database/mongodb/models/user_model.py
from typing import Dict, Any, Optional
from uuid import UUID

from src.domain.entities.user import User


class UserModel:
    """Modelo de dados para usuários no MongoDB."""
    
    @staticmethod
    def to_dict(user: User) -> Dict[str, Any]:
        """
        Converte uma entidade User para um dicionário para armazenamento no MongoDB.
        
        Args:
            user: Objeto User a ser convertido
            
        Returns:
            Dicionário representando o usuário
        """
        return {
            "_id": str(user.id),
            "name": user.name,
            "email": user.email,
            "createdAt": user.created_at
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[User]:
        """
        Converte um dicionário do MongoDB para uma entidade User.
        
        Args:
            data: Dicionário contendo dados do usuário
            
        Returns:
            Objeto User ou None se o dicionário for inválido
        """
        if not data:
            return None
        
        try:
            return User(
                id=UUID(data["_id"]),
                name=data["name"],
                email=data["email"],
                created_at=data["createdAt"]
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para User: {e}")
            return None