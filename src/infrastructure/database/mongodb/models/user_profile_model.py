# src/infrastructure/database/mongodb/models/user_profile_model.py
from typing import Dict, Any, Optional, List
from uuid import UUID

from src.domain.entities.user_profile import UserProfile, Currency, Theme


class UserProfileModel:
    """Modelo de dados para perfis de usuário no MongoDB."""
    
    @staticmethod
    def to_dict(profile: UserProfile) -> Dict[str, Any]:
        """
        Converte uma entidade UserProfile para um dicionário para armazenamento no MongoDB.
        
        Args:
            profile: Objeto UserProfile a ser convertido
            
        Returns:
            Dicionário representando o perfil de usuário
        """
        profile_dict = {
            "_id": str(profile.id),
            "userId": str(profile.user_id),
            "currency": profile.currency.value,
            "language": profile.language,
            "theme": profile.theme.value,
            "notificationEmail": profile.notification_email,
            "notificationPush": profile.notification_push,
            "createdAt": profile.created_at,
            "updatedAt": profile.updated_at,
            "dashboardWidgets": profile.dashboard_widgets,
            "extraSettings": profile.extra_settings,
            "sharedWithUsers": [str(user_id) for user_id in profile.shared_with_users]
        }
        
        if profile.monthly_budget is not None:
            profile_dict["monthlyBudget"] = profile.monthly_budget
        
        return profile_dict
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[UserProfile]:
        """
        Converte um dicionário do MongoDB para uma entidade UserProfile.
        
        Args:
            data: Dicionário contendo dados do perfil de usuário
            
        Returns:
            Objeto UserProfile ou None se o dicionário for inválido
        """
        if not data:
            return None
        
        try:
            # Converte os IDs de usuário compartilhados de string para UUID
            shared_with_users = []
            for user_id_str in data.get("sharedWithUsers", []):
                try:
                    shared_with_users.append(UUID(user_id_str))
                except ValueError:
                    continue  # Ignora IDs inválidos
            
            return UserProfile(
                id=UUID(data["_id"]),
                user_id=UUID(data["userId"]),
                currency=Currency(data.get("currency", Currency.BRL.value)),
                language=data.get("language", "pt-BR"),
                theme=Theme(data.get("theme", Theme.SYSTEM.value)),
                notification_email=data.get("notificationEmail", True),
                notification_push=data.get("notificationPush", False),
                monthly_budget=data.get("monthlyBudget"),
                dashboard_widgets=data.get("dashboardWidgets", []),
                created_at=data["createdAt"],
                updated_at=data["updatedAt"],
                shared_with_users=shared_with_users,
                extra_settings=data.get("extraSettings", {})
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para UserProfile: {e}")
            return None