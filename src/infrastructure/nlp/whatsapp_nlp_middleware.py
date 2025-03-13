# src/infrastructure/nlp/whatsapp_nlp_middleware.py
from typing import Dict, Any, Tuple, Optional
from uuid import UUID

from src.application.usecases.nlp_usecases import NLPUseCases
from src.application.usecases.whatsapp_contact_usecases import WhatsAppContactUseCases


class WhatsAppNLPMiddleware:
    """Middleware para processar comandos de WhatsApp antes de passar para o NLP."""
    
    def __init__(self, 
                nlp_usecases: NLPUseCases,
                whatsapp_contact_usecases: WhatsAppContactUseCases):
        """
        Inicializa o middleware de NLP para WhatsApp.
        
        Args:
            nlp_usecases: Casos de uso de NLP
            whatsapp_contact_usecases: Casos de uso de contatos de WhatsApp
        """
        self.nlp_usecases = nlp_usecases
        self.whatsapp_contact_usecases = whatsapp_contact_usecases
    
    async def process_whatsapp_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa uma mensagem de WhatsApp.
        
        Args:
            phone_number: Número de telefone do remetente
            message: Mensagem enviada pelo remetente
            
        Returns:
            Resultado do processamento
        """
        # Primeiro, verifica se o contato existe e está em onboarding
        contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
        
        # Se não existir ou onboarding não estiver completo, realiza o onboarding
        if not contact or not contact.onboarding_complete:
            onboarding_complete, response_message, updated_data = await self.whatsapp_contact_usecases.handle_onboarding_step(
                phone_number=phone_number,
                message=message
            )
            
            # Atualiza os dados do contato
            if updated_data:
                contact = await self.whatsapp_contact_usecases.whatsapp_contact_repository.update_by_phone_number(
                    phone_number=phone_number,
                    data=updated_data
                )
            
            # Se o onboarding não estiver completo, retorna a mensagem de onboarding
            if not onboarding_complete:
                return {
                    "status": "onboarding",
                    "message": response_message,
                    "data": {
                        "step": updated_data.get("onboarding_step", "welcome")
                    }
                }
        
        # Se chegou aqui, o onboarding está completo
        # Busca o user_id para processar o comando NLP
        if not contact:
            # Isso não deveria acontecer, mas registra um novo contato se necessário
            contact = await self.whatsapp_contact_usecases.register_contact(phone_number)
            await self.whatsapp_contact_usecases.update_onboarding_status(phone_number, True, "completed")
        
        # Processa o comando usando o NLP
        result = await self.nlp_usecases.process_command(contact.user_id, message)
        
        return result
    
    async def get_user_id_from_phone(self, phone_number: str) -> Optional[UUID]:
        """
        Recupera o ID do usuário a partir do número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            ID do usuário ou None se o contato não existir
        """
        contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
        return contact.user_id if contact else None