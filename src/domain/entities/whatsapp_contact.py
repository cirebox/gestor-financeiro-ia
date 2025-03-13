# src/domain/entities/whatsapp_contact.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4


@dataclass
class WhatsAppContact:
    """Entidade que representa um contato de WhatsApp."""
    
    id: UUID
    phone_number: str
    user_id: UUID
    created_at: datetime
    name: Optional[str] = None
    last_interaction: Optional[datetime] = None
    onboarding_complete: bool = False
    onboarding_step: Optional[str] = None
    
    @classmethod
    def create(cls, phone_number: str, name: Optional[str] = None) -> 'WhatsAppContact':
        """
        Cria uma nova instância de WhatsAppContact.
        
        Args:
            phone_number: Número de telefone do contato
            name: Nome do contato (opcional)
            
        Returns:
            Uma nova instância de WhatsAppContact
        """
        return cls(
            id=uuid4(),
            phone_number=phone_number,
            user_id=uuid4(),  # Cria um novo user_id para associar às transações
            name=name,
            created_at=datetime.now(),
            last_interaction=datetime.now(),
            onboarding_complete=False,
            onboarding_step="welcome"
        )