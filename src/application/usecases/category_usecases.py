# src/application/usecases/category_usecases.py
from typing import List, Optional
from uuid import UUID

from src.application.interfaces.repositories.category_repository_interface import CategoryRepositoryInterface
from src.domain.entities.category import Category


class CategoryUseCases:
    """Casos de uso relacionados a categorias financeiras."""
    
    def __init__(self, category_repository: CategoryRepositoryInterface):
        """
        Inicializa os casos de uso de categoria.
        
        Args:
            category_repository: Implementação do repositório de categorias
        """
        self.category_repository = category_repository
    
    async def add_category(self, name: str, type: str) -> Category:
        """
        Adiciona uma nova categoria.
        
        Args:
            name: Nome da categoria
            type: Tipo da categoria ('income' ou 'expense')
            
        Returns:
            A categoria criada
        """
        # Verifica se já existe uma categoria com o mesmo nome
        existing = await self.category_repository.get_by_name(name)
        if existing:
            return existing
        
        # Cria a categoria
        category = Category.create(name=name, type=type)
        
        # Adiciona a categoria ao repositório
        return await self.category_repository.add(category)
    
    async def get_categories(self, type: Optional[str] = None) -> List[Category]:
        """
        Recupera todas as categorias, opcionalmente filtradas por tipo.
        
        Args:
            type: Tipo opcional de categoria ('income' ou 'expense')
            
        Returns:
            Lista de categorias que correspondem ao tipo
        """
        return await self.category_repository.get_all(type)
    
    async def get_category(self, category_id: UUID) -> Optional[Category]:
        """
        Recupera uma categoria pelo ID.
        
        Args:
            category_id: ID da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        return await self.category_repository.get_by_id(category_id)
    
    async def get_category_by_name(self, name: str) -> Optional[Category]:
        """
        Recupera uma categoria pelo nome.
        
        Args:
            name: Nome da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        return await self.category_repository.get_by_name(name)
    
    async def update_category(self, category_id: UUID, name: str) -> Optional[Category]:
        """
        Atualiza o nome de uma categoria.
        
        Args:
            category_id: ID da categoria a ser atualizada
            name: Novo nome
            
        Returns:
            A categoria atualizada ou None se não encontrada
        """
        return await self.category_repository.update(category_id, name)
    
    async def delete_category(self, category_id: UUID) -> bool:
        """
        Remove uma categoria.
        
        Args:
            category_id: ID da categoria a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        return await self.category_repository.delete(category_id)
    
    async def initialize_default_categories(self) -> None:
        """
        Inicializa as categorias padrão no sistema.
        """
        await self.category_repository.initialize_default_categories()