# src/domain/entities/user_profile.py
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


class Currency(str, Enum):
    """Moedas suportadas pelo sistema."""
    BRL = "BRL"  # Real brasileiro
    USD = "USD"  # Dólar americano
    EUR = "EUR"  # Euro
    GBP = "GBP"  # Libra britânica
    JPY = "JPY"  # Iene japonês
    CAD = "CAD"  # Dólar canadense
    AUD = "AUD"  # Dólar australiano
    CHF = "CHF"  # Franco suíço


class Theme(str, Enum):
    """Temas visuais suportados pelo sistema."""
    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


@dataclass
class UserProfile:
    """Entidade que representa o perfil de um usuário."""
    
    id: UUID
    user_id: UUID
    currency: Currency = Currency.BRL
    language: str = "pt-BR"
    theme: Theme = Theme.SYSTEM
    notification_email: bool = True
    notification_push: bool = False
    monthly_budget: Optional[float] = None
    dashboard_widgets: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    shared_with_users: List[UUID] = field(default_factory=list)
    extra_settings: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def create(cls, user_id: UUID) -> 'UserProfile':
        """
        Cria um novo perfil de usuário com valores padrão.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Um novo perfil de usuário
        """
        return cls(
            id=uuid4(),
            user_id=user_id,
            dashboard_widgets=["balance", "recent_transactions", "spending_by_category"],
        )
    
    def update(self, **kwargs) -> None:
        """
        Atualiza os atributos do perfil de usuário.
        
        Args:
            **kwargs: Atributos a serem atualizados
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        
        self.updated_at = datetime.now()