# src/application/interfaces/repositories/category_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.category import Category


class CategoryRepositoryInterface(ABC):
    """Interface para repositório de categorias."""
    
    @abstractmethod
    async def add(self, category: Category) -> Category:
        """
        Adiciona uma nova categoria.
        
        Args:
            category: A categoria a ser adicionada
            
        Returns:
            A categoria adicionada com ID atualizado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """
        Recupera uma categoria pelo ID.
        
        Args:
            category_id: ID da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        pass
    
    @abstractmethod
    async def get_by_name(self, name: str) -> Optional[Category]:
        """
        Recupera uma categoria pelo nome.
        
        Args:
            name: Nome da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        pass
    
    @abstractmethod
    async def get_all(self, type: Optional[str] = None) -> List[Category]:
        """
        Recupera todas as categorias, opcionalmente filtradas por tipo.
        
        Args:
            type: Tipo opcional de categoria ('income' ou 'expense')
            
        Returns:
            Lista de categorias que correspondem ao tipo
        """
        pass
    
    @abstractmethod
    async def update(self, category_id: UUID, name: str) -> Optional[Category]:
        """
        Atualiza o nome de uma categoria.
        
        Args:
            category_id: ID da categoria a ser atualizada
            name: Novo nome
            
        Returns:
            A categoria atualizada ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def delete(self, category_id: UUID) -> bool:
        """
        Remove uma categoria.
        
        Args:
            category_id: ID da categoria a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
    async def initialize_default_categories(self) -> None:
        """
        Inicializa as categorias padrão no sistema.
        """
        pass