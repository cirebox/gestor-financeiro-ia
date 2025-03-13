# src/infrastructure/database/repositories/mongodb_category_repository.py
from typing import List, Optional
from uuid import UUID

from src.application.interfaces.repositories.category_repository_interface import CategoryRepositoryInterface
from src.domain.entities.category import Category
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.infrastructure.database.mongodb.models.category_model import CategoryModel


class MongoDBCategoryRepository(CategoryRepositoryInterface):
    """Implementação do repositório de categorias usando MongoDB."""
    
    def __init__(self):
        """Inicializa o repositório com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.collection = self.connection.db.categories
    
    async def add(self, category: Category) -> Category:
        """
        Adiciona uma nova categoria.
        
        Args:
            category: A categoria a ser adicionada
            
        Returns:
            A categoria adicionada com ID atualizado
        """
        category_dict = CategoryModel.to_dict(category)
        await self.collection.insert_one(category_dict)
        return category
    
    async def get_by_id(self, category_id: UUID) -> Optional[Category]:
        """
        Recupera uma categoria pelo ID.
        
        Args:
            category_id: ID da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        data = await self.collection.find_one({"_id": str(category_id)})
        return CategoryModel.from_dict(data)
    
    async def get_by_name(self, name: str) -> Optional[Category]:
        """
        Recupera uma categoria pelo nome.
        
        Args:
            name: Nome da categoria
            
        Returns:
            A categoria encontrada ou None
        """
        data = await self.collection.find_one({"name": name})
        return CategoryModel.from_dict(data)
    
    async def get_all(self, type: Optional[str] = None) -> List[Category]:
        """
        Recupera todas as categorias, opcionalmente filtradas por tipo.
        
        Args:
            type: Tipo opcional de categoria ('income' ou 'expense')
            
        Returns:
            Lista de categorias que correspondem ao tipo
        """
        query = {}
        if type:
            query["type"] = type
        
        cursor = self.collection.find(query).sort("name", 1)
        
        categories = []
        async for document in cursor:
            category = CategoryModel.from_dict(document)
            if category:
                categories.append(category)
        
        return categories
    
    async def update(self, category_id: UUID, name: str) -> Optional[Category]:
        """
        Atualiza o nome de uma categoria.
        
        Args:
            category_id: ID da categoria a ser atualizada
            name: Novo nome
            
        Returns:
            A categoria atualizada ou None se não encontrada
        """
        result = await self.collection.update_one(
            {"_id": str(category_id)},
            {"$set": {"name": name}}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_by_id(category_id)
    
    async def delete(self, category_id: UUID) -> bool:
        """
        Remove uma categoria.
        
        Args:
            category_id: ID da categoria a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        result = await self.collection.delete_one({"_id": str(category_id)})
        return result.deleted_count > 0
    
    async def initialize_default_categories(self) -> None:
        """
        Inicializa as categorias padrão no sistema.
        """
        default_categories = [
            {"name": "Alimentação", "type": "expense"},
            {"name": "Transporte", "type": "expense"},
            {"name": "Moradia", "type": "expense"},
            {"name": "Lazer", "type": "expense"},
            {"name": "Saúde", "type": "expense"},
            {"name": "Educação", "type": "expense"},
            {"name": "Salário", "type": "income"},
            {"name": "Freelance", "type": "income"},
            {"name": "Investimentos", "type": "income"},
            {"name": "Outros", "type": "expense"},
            {"name": "Outros", "type": "income"}
        ]
        
        for category_data in default_categories:
            try:
                # Verifica se a categoria já existe
                existing = await self.get_by_name(category_data["name"])
                
                # Se não existir ou se o tipo for diferente do esperado, cria/atualiza
                if not existing:
                    # Cria nova categoria
                    category = Category.create(
                        name=category_data["name"],
                        type=category_data["type"]
                    )
                    await self.add(category)
                    print(f"Categoria criada: {category_data['name']} ({category_data['type']})")
                elif existing and existing.type != category_data["type"] and category_data["name"] != "Outros":
                    # Para categorias com o mesmo nome mas tipo diferente (exceto "Outros")
                    # Cria com nome modificado
                    new_name = f"{category_data['name']} ({category_data['type']})"
                    category = Category.create(
                        name=new_name,
                        type=category_data["type"]
                    )
                    await self.add(category)
                    print(f"Categoria criada com nome modificado: {new_name}")
            except Exception as e:
                # Ignora erros de chave duplicada
                if "duplicate key error" in str(e):
                    print(f"Categoria já existe: {category_data['name']} ({category_data['type']})")
                else:
                    print(f"Erro ao criar categoria {category_data['name']}: {e}")