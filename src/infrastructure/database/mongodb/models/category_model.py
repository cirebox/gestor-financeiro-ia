# src/infrastructure/database/mongodb/models/category_model.py
from typing import Dict, Any, Optional
from uuid import UUID

from src.domain.entities.category import Category


class CategoryModel:
    """Modelo de dados para categorias no MongoDB."""
    
    @staticmethod
    def to_dict(category: Category) -> Dict[str, Any]:
        """
        Converte uma entidade Category para um dicionário para armazenamento no MongoDB.
        
        Args:
            category: Objeto Category a ser convertido
            
        Returns:
            Dicionário representando a categoria
        """
        return {
            "_id": str(category.id),
            "name": category.name,
            "type": category.type,
            "createdAt": category.created_at
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[Category]:
        """
        Converte um dicionário do MongoDB para uma entidade Category.
        
        Args:
            data: Dicionário contendo dados da categoria
            
        Returns:
            Objeto Category ou None se o dicionário for inválido
        """
        if not data:
            return None
        
        try:
            return Category(
                id=UUID(data["_id"]),
                name=data["name"],
                type=data["type"],
                created_at=data["createdAt"]
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para Category: {e}")
            return None