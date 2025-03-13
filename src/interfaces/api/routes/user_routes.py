# src/interfaces/api/routes/user_routes.py
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr

from src.application.usecases.user_usecases import UserUseCases
from src.application.security.auth import get_current_active_user, get_admin_user
from src.domain.entities.user import User
from src.interfaces.api.dependencies import get_user_usecases


router = APIRouter(prefix="/users", tags=["users"])


class UserUpdate(BaseModel):
    """DTO para atualização de usuário."""
    
    name: Optional[str] = Field(None, description="Nome do usuário")
    email: Optional[EmailStr] = Field(None, description="Email do usuário")
    is_active: Optional[bool] = Field(None, description="Status de ativação")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "João Silva Atualizado",
                "email": "joao.silva.atualizado@exemplo.com",
                "is_active": True
            }
        }


class UserResponse(BaseModel):
    """DTO para resposta de usuário."""
    
    id: str
    name: str
    email: str
    created_at: str
    is_active: bool
    is_admin: bool
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174003",
                "name": "João Silva",
                "email": "joao.silva@exemplo.com",
                "created_at": "2023-01-15T12:00:00Z",
                "is_active": True,
                "is_admin": False
            }
        }


# Esta rota está disponível apenas para administradores
@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_admin_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Lista todos os usuários. Requer privilégios de administrador.
    
    Args:
        skip: Número de registros para pular (paginação)
        limit: Número máximo de registros a retornar
        
    Returns:
        Lista de usuários
    """
    # Esta é uma implementação simplificada
    # Em uma versão completa, deveria ter suporte a paginação no repositório
    users = []  # Aqui você implementaria a consulta no repositório
    
    return [
        UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat(),
            is_active=user.is_active,
            is_admin=user.is_admin
        )
        for user in users
    ]


# Esta rota está disponível apenas para administradores
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Recupera um usuário específico pelo ID. Requer privilégios de administrador.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dados do usuário
    """
    try:
        user = await user_usecases.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat(),
            is_active=user.is_active,
            is_admin=user.is_admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao recuperar usuário: {str(e)}")


# Esta rota está disponível apenas para administradores
@router.get("/email/{email}", response_model=UserResponse)
async def get_user_by_email(
    email: str,
    current_user: User = Depends(get_admin_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Recupera um usuário pelo email. Requer privilégios de administrador.
    
    Args:
        email: Email do usuário
        
    Returns:
        Dados do usuário
    """
    try:
        user = await user_usecases.get_user_by_email(email)
        
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            created_at=user.created_at.isoformat(),
            is_active=user.is_active,
            is_admin=user.is_admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao recuperar usuário: {str(e)}")


# Esta rota está disponível apenas para o próprio usuário ou para administradores
@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Atualiza um usuário existente. Requer ser o próprio usuário ou um administrador.
    
    Args:
        user_id: ID do usuário a ser atualizado
        user_data: Dados do usuário a serem atualizados
        
    Returns:
        Dados do usuário atualizado
    """
    # Verifica se o usuário está tentando atualizar outro usuário sem ser administrador
    if str(current_user.id) != str(user_id) and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permissão negada. Você só pode atualizar seu próprio perfil."
        )
    
    # Apenas administradores podem atualizar o campo is_active
    if user_data.is_active is not None and not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem alterar o status de ativação."
        )
    
    try:
        updated_user = await user_usecases.update_user(
            user_id=user_id,
            name=user_data.name,
            email=user_data.email,
            is_active=user_data.is_active
        )
        
        if not updated_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        return UserResponse(
            id=str(updated_user.id),
            name=updated_user.name,
            email=updated_user.email,
            created_at=updated_user.created_at.isoformat(),
            is_active=updated_user.is_active,
            is_admin=updated_user.is_admin
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao atualizar usuário: {str(e)}")


# Esta rota está disponível apenas para administradores
@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Remove um usuário existente. Requer privilégios de administrador.
    
    Args:
        user_id: ID do usuário a ser removido
    """
    try:
        # Impede a remoção do próprio usuário administrador
        if str(current_user.id) == str(user_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Você não pode remover seu próprio usuário."
            )
        
        deleted = await user_usecases.delete_user(user_id)
        
        if not deleted:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao excluir usuário: {str(e)}")


# Rota para promoção de usuário a administrador (apenas administradores podem acessar)
@router.post("/{user_id}/promote", response_model=UserResponse, status_code=status.HTTP_200_OK)
async def promote_to_admin(
    user_id: UUID,
    current_user: User = Depends(get_admin_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Promove um usuário a administrador. Requer privilégios de administrador.
    
    Args:
        user_id: ID do usuário a ser promovido
        
    Returns:
        Dados do usuário atualizado
    """
    try:
        # Verifica se o usuário existe
        user = await user_usecases.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
        
        # Já é administrador
        if user.is_admin:
            return UserResponse(
                id=str(user.id),
                name=user.name,
                email=user.email,
                created_at=user.created_at.isoformat(),
                is_active=user.is_active,
                is_admin=user.is_admin
            )
        
        # Atualiza o usuário para ser administrador
        updated_user = await user_usecases.update_user(
            user_id=user_id,
            is_active=True,  # Garante que o usuário esteja ativo
            is_admin=True
        )
        
        return UserResponse(
            id=str(updated_user.id),
            name=updated_user.name,
            email=updated_user.email,
            created_at=updated_user.created_at.isoformat(),
            is_active=updated_user.is_active,
            is_admin=updated_user.is_admin
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao promover usuário: {str(e)}")