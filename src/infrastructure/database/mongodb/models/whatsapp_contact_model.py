# src/infrastructure/database/mongodb/models/whatsapp_contact_model.py
from typing import Dict, Any, Optional
from uuid import UUID

from src.domain.entities.whatsapp_contact import WhatsAppContact


class WhatsAppContactModel:
    """Modelo de dados para contatos de WhatsApp no MongoDB."""
    
    @staticmethod
    def to_dict(contact: WhatsAppContact) -> Dict[str, Any]:
        """
        Converte uma entidade WhatsAppContact para um dicionário para armazenamento no MongoDB.
        
        Args:
            contact: Objeto WhatsAppContact a ser convertido
            
        Returns:
            Dicionário representando o contato
        """
        return {
            "_id": str(contact.id),
            "phoneNumber": contact.phone_number,
            "userId": str(contact.user_id),
            "createdAt": contact.created_at,
            "name": contact.name,
            "lastInteraction": contact.last_interaction,
            "onboardingComplete": contact.onboarding_complete,
            "onboardingStep": contact.onboarding_step
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[WhatsAppContact]:
        """
        Converte um dicionário do MongoDB para uma entidade WhatsAppContact.
        
        Args:
            data: Dicionário contendo dados do contato
            
        Returns:
            Objeto WhatsAppContact ou None se o dicionário for inválido
        """
        if not data:
            return None
        
        try:
            return WhatsAppContact(
                id=UUID(data["_id"]),
                phone_number=data["phoneNumber"],
                user_id=UUID(data["userId"]),
                created_at=data["createdAt"],
                name=data.get("name"),
                last_interaction=data.get("lastInteraction"),
                onboarding_complete=data.get("onboardingComplete", False),
                onboarding_step=data.get("onboardingStep")
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para WhatsAppContact: {e}")
            return None