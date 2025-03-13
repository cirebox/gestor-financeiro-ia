# src/interfaces/api/routes/profile_routes.py
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.application.usecases.user_profile_usecases import UserProfileUseCases
from src.domain.entities.user import User
from src.domain.entities.user_profile import Currency, Theme
from src.application.security.auth import get_current_active_user
from src.interfaces.api.dependencies import get_user_profile_usecases


router = APIRouter(prefix="/profiles", tags=["profiles"])


class UserProfileResponse(BaseModel):
    """DTO para resposta de perfil de usuário."""
    
    id: str
    user_id: str
    currency: str
    language: str
    theme: str
    notification_email: bool
    notification_push: bool
    monthly_budget: Optional[float]
    dashboard_widgets: List[str]
    shared_with_users: List[str]
    extra_settings: Dict[str, Any]
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "currency": "BRL",
                "language": "pt-BR",
                "theme": "system",
                "notification_email": True,
                "notification_push": False,
                "monthly_budget": 3000.0,
                "dashboard_widgets": ["balance", "recent_transactions", "spending_by_category"],
                "shared_with_users": ["123e4567-e89b-12d3-a456-426614174002"],
                "extra_settings": {
                    "show_cents": True,
                    "default_view": "month"
                }
            }
        }


class UserProfileUpdate(BaseModel):
    """DTO para atualização de perfil de usuário."""
    
    currency: Optional[str] = Field(None, description="Código da moeda (BRL, USD, EUR, etc.)")
    language: Optional[str] = Field(None, description="Código de idioma (pt-BR, en-US, etc.)")
    theme: Optional[str] = Field(None, description="Tema visual (light, dark, system)")
    notification_email: Optional[bool] = Field(None, description="Receber notificações por email")
    notification_push: Optional[bool] = Field(None, description="Receber notificações push")
    monthly_budget: Optional[float] = Field(None, description="Orçamento mensal")
    dashboard_widgets: Optional[List[str]] = Field(None, description="Widgets do painel")
    extra_settings: Optional[Dict[str, Any]] = Field(None, description="Configurações extras")
    
    class Config:
        schema_extra = {
            "example": {
                "currency": "USD",
                "language": "en-US",
                "theme": "dark",
                "notification_email": False,
                "notification_push": True,
                "monthly_budget": 5000.0,
                "dashboard_widgets": ["balance", "recent_transactions", "budget", "goals"],
                "extra_settings": {
                    "show_cents": False,
                    "default_view": "week"
                }
            }
        }


class ShareProfileRequest(BaseModel):
    """DTO para compartilhamento de perfil."""
    
    user_id: str = Field(..., description="ID do usuário com quem compartilhar")
    
    class Config:
        schema_extra = {
            "example": {
                "user_id": "123e4567-e89b-12d3-a456-426614174002"
            }
        }


@router.get("/me", response_model=UserProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    profile_usecases: UserProfileUseCases = Depends(get_user_profile_usecases)
):
    """
    Obtém o perfil do usuário autenticado.
    
    Returns:
        Perfil do usuário autenticado
    """
    try:
        profile = await profile_usecases.get_or_create_profile(current_user.id)
        
        return UserProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            currency=profile.currency.value,
            language=profile.language,
            theme=profile.theme.value,
            notification_email=profile.notification_email,
            notification_push=profile.notification_push,
            monthly_budget=profile.monthly_budget,
            dashboard_widgets=profile.dashboard_widgets,
            shared_with_users=[str(user_id) for user_id in profile.shared_with_users],
            extra_settings=profile.extra_settings
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter perfil: {str(e)}"
        )


@router.patch("/me", response_model=UserProfileResponse)
async def update_my_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    profile_usecases: UserProfileUseCases = Depends(get_user_profile_usecases)
):
    """
    Atualiza o perfil do usuário autenticado.
    
    Args:
        profile_data: Dados do perfil a serem atualizados
        
    Returns:
        Perfil atualizado
    """
    try:
        # Converte o modelo Pydantic para dicionário
        update_data = profile_data.dict(exclude_unset=True)
        
        # Atualiza o perfil
        profile = await profile_usecases.update_profile(current_user.id, update_data)
        
        return UserProfileResponse(
            id=str(profile.id),
            user_id=str(profile.user_id),
            currency=profile.currency.value,
            language=profile.language,
            theme=profile.theme.value,
            notification_email=profile.notification_email,
            notification_push=profile.notification_push,
            monthly_budget=profile.monthly_budget,
            dashboard_widgets=profile.dashboard_widgets,
            shared_with_users=[str(user_id) for user_id in profile.shared_with_users],
            extra_settings=profile.extra_settings
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar perfil: {str(e)}"
        )


@router.get("/shared", response_model=List[UserProfileResponse])
async def get_shared_profiles(
    current_user: User = Depends(get_current_active_user),
    profile_usecases: UserProfileUseCases = Depends(get_user_profile_usecases)
):
    """
    Obtém os perfis compartilhados com o usuário autenticado.
    
    Returns:
        Lista de perfis compartilhados com o usuário
    """
    try:
        profiles = await profile_usecases.get_shared_profiles(current_user.id)
        
        return [
            UserProfileResponse(
                id=str(profile.id),
                user_id=str(profile.user_id),
                currency=profile.currency.value,
                language=profile.language,
                theme=profile.theme.value,
                notification_email=profile.notification_email,
                notification_push=profile.notification_push,
                monthly_budget=profile.monthly_budget,
                dashboard_widgets=profile.dashboard_widgets,
                shared_with_users=[str(user_id) for user_id in profile.shared_with_users],
                extra_settings=profile.extra_settings
            )
            for profile in profiles
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao obter perfis compartilhados: {str(e)}"
        )


@router.post("/share", status_code=status.HTTP_204_NO_CONTENT)
async def share_profile(
    share_request: ShareProfileRequest,
    current_user: User = Depends(get_current_active_user),
    profile_usecases: UserProfileUseCases = Depends(get_user_profile_usecases)
):
    """
    Compartilha o perfil do usuário autenticado com outro usuário.
    
    Args:
        share_request: Dados de compartilhamento
    """
    try:
        target_user_id = UUID(share_request.user_id)
        
        success = await profile_usecases.share_profile(current_user.id, target_user_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível compartilhar o perfil"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )