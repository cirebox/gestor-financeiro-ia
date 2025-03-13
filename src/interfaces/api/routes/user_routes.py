# src/interfaces/api/routes/user_routes.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, EmailStr

from src.application.usecases.user_usecases import UserUseCases
from src.interfaces.api.dependencies import get_user_usecases


router = APIRouter(prefix="/users", tags=["users"])


class UserCreate(BaseModel):
    """DTO para criação de usuário."""
    
    name: str = Field(..., description="Nome do usuário")
    email: EmailStr = Field(..., description="Email do usuário")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "João Silva",
                "email": "joao.silva@exemplo.com"
            }
        }


class UserUpdate(BaseModel):
    """DTO para atualização de usuário."""
    
    name: Optional[str] = Field(None, description="Nome do usuário")
    email: Optional[EmailStr] = Field(None, description="Email do usuário")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "João Silva Atualizado",
                "email": "joao.silva.atualizado@exemplo.com"
            }
        }


class UserResponse(BaseModel):
    """DTO para resposta de usuário."""
    
    id: str
    name: str
    email: str
    created_at: str
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "name": "João Silva",
                "email": "joao.silva@exemplo.com",
                "created_at": "2023-01-15T12:00:00Z"
            }
        }


@router.post("/", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """Cria um novo usuário."""
    try:
        created_user = await user_usecases.create_user(
            name=user.name,
            email=user.email
        )
        
        return UserResponse(
            id=str(created_user.id),
            name=created_user.name,
            email=created_user.email,
            created_at=created_user.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar usuário: {str(e)}")


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """Recupera um usuário específico pelo ID."""
    try:
        user = await user_usecases.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar usuário: {str(e)}")


@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """Recupera um usuário pelo email."""
    try:
        user = await user_usecases.get_user_by_email(email)
        
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat()
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar usuário: {str(e)}")


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user: UserUpdate,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """Atualiza um usuário existente."""
    try:
        updated_user = await user_usecases.update_user(
            user_id=user_id,
            name=user.name,
            email=user.email
        )
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(updated_user.id),
            name=updated_user.name,
            email=updated_user.email,
            created_at=updated_user.created_at.isoformat()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar usuário: {str(e)}")


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: UUID,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """Remove um usuário existente."""
    try:
        deleted = await user_usecases.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir usuário: {str(e)}")