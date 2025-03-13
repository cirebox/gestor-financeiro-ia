# src/interfaces/api/routes/category_routes.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.application.usecases.category_usecases import CategoryUseCases
from src.interfaces.api.dependencies import get_category_usecases, get_current_user_id


router = APIRouter(prefix="/categories", tags=["categories"])


class CategoryCreate(BaseModel):
    """DTO para criação de categoria."""
    
    name: str = Field(..., description="Nome da categoria")
    type: str = Field(..., description="Tipo da categoria ('income' ou 'expense')")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Lazer",
                "type": "expense"
            }
        }


class CategoryResponse(BaseModel):
    """DTO para resposta de categoria."""
    
    id: str
    name: str
    type: str
    created_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174002",
                "name": "Lazer",
                "type": "expense",
                "created_at": "2023-01-15T12:00:00Z"
            }
        }


@router.post("/", response_model=CategoryResponse)
async def create_category(
    category: CategoryCreate,
    category_usecases: CategoryUseCases = Depends(get_category_usecases)
):
    """Cria uma nova categoria."""
    try:
        if category.type not in ("income", "expense"):
            raise HTTPException(status_code=400, detail="Tipo deve ser 'income' ou 'expense'")
            
        created_category = await category_usecases.add_category(
            name=category.name,
            type=category.type
        )
        
        return CategoryResponse(
            id=str(created_category.id),
            name=created_category.name,
            type=created_category.type,
            created_at=created_category.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar categoria: {str(e)}")


@router.get("/", response_model=List[CategoryResponse])
async def list_categories(
    type: Optional[str] = Query(None, description="Filtrar por tipo ('income' ou 'expense')"),
    category_usecases: CategoryUseCases = Depends(get_category_usecases)
):
    """Lista todas as categorias, opcionalmente filtradas por tipo."""
    try:
        if type and type not in ("income", "expense"):
            raise HTTPException(status_code=400, detail="Tipo deve ser 'income' ou 'expense'")
            
        categories = await category_usecases.get_categories(type)
        
        return [
            CategoryResponse(
                id=str(category.id),
                name=category.name,
                type=category.type,
                created_at=category.created_at.isoformat()
            )
            for category in categories
        ]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar categorias: {str(e)}")


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: UUID,
    category_usecases: CategoryUseCases = Depends(get_category_usecases)
):
    """Recupera uma categoria específica pelo ID."""
    try:
        category = await category_usecases.get_category(category_id)
        
        if not category:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        return CategoryResponse(
            id=str(category.id),
            name=category.name,
            type=category.type,
            created_at=category.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar categoria: {str(e)}")


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: UUID,
    name: str,
    category_usecases: CategoryUseCases = Depends(get_category_usecases)
):
    """Atualiza o nome de uma categoria existente."""
    try:
        updated_category = await category_usecases.update_category(category_id, name)
        
        if not updated_category:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
        
        return CategoryResponse(
            id=str(updated_category.id),
            name=updated_category.name,
            type=updated_category.type,
            created_at=updated_category.created_at.isoformat()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar categoria: {str(e)}")


@router.delete("/{category_id}", status_code=204)
async def delete_category(
    category_id: UUID,
    category_usecases: CategoryUseCases = Depends(get_category_usecases)
):
    """Remove uma categoria existente."""
    try:
        deleted = await category_usecases.delete_category(category_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Categoria não encontrada")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir categoria: {str(e)}")