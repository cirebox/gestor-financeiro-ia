# src/interfaces/api/routes/whatsapp_routes.py
"""
Rotas para integração com WhatsApp.
Este módulo contém rotas específicas para processar mensagens do WhatsApp.
"""

from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from uuid import UUID

from src.application.usecases.nlp_usecases import NLPUseCases
from src.application.usecases.whatsapp_contact_usecases import WhatsAppContactUseCases
from src.interfaces.api.dependencies import get_nlp_usecases, get_whatsapp_contact_usecases
from src.infrastructure.whatsapp.thread_manager import get_thread_manager, is_greeting
from config import settings

# Constante para API key (em produção, usar variáveis de ambiente)
WHATSAPP_API_KEY = settings.WHATSAPP_API_KEY if hasattr(settings, 'WHATSAPP_API_KEY') else "whatsapp-integration-secret-key"

# Router específico para WhatsApp, separado do router NLP
router = APIRouter(
    prefix="/whatsapp",
    tags=["whatsapp-integration"],
)


class WhatsAppRequest(BaseModel):
    """Requisição para processamento de mensagem do WhatsApp."""
    
    command: str = Field(..., description="Comando ou mensagem enviada pelo usuário", example="listar despesas")
    phone_number: str = Field(..., description="Número de telefone do usuário (apenas números)", example="5511999999999")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "listar despesas",
                "phone_number": "5511999999999"
            }
        }


class WhatsAppResponse(BaseModel):
    """Resposta para processamento de mensagem do WhatsApp."""
    
    status: str = Field(..., description="Status do processamento", example="success")
    message: str = Field(..., description="Mensagem de resposta", example="Aqui estão suas despesas...")
    data: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais (opcional)")


async def validate_api_key(
    api_key: str = Header(
        ..., 
        alias="X-WhatsApp-API-Key",
        description="Chave de API para integração com WhatsApp"
    )
):
    """Valida a chave de API para integração com WhatsApp."""
    if api_key != WHATSAPP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid WhatsApp API key"
        )
    return api_key


@router.post(
    "/process",
    response_model=WhatsAppResponse,
    summary="Processa mensagem do WhatsApp",
    description="Recebe e processa mensagens enviadas por usuários via WhatsApp, gerenciando o onboarding e mantendo contexto por usuário.",
    responses={
        200: {"description": "Mensagem processada com sucesso"},
        401: {"description": "API Key inválida ou ausente"},
        500: {"description": "Erro ao processar a mensagem"}
    }
)
async def process_whatsapp_message(
    request: WhatsAppRequest,
    api_key: str = Depends(validate_api_key),
    nlp_usecases: NLPUseCases = Depends(get_nlp_usecases),
    whatsapp_contact_usecases: WhatsAppContactUseCases = Depends(get_whatsapp_contact_usecases)
):
    """
    Processa uma mensagem recebida via WhatsApp.
    
    Este endpoint:
    1. Requer autenticação via API Key no cabeçalho X-WhatsApp-API-Key
    2. Gerencia o fluxo de onboarding para novos usuários
    3. Utiliza threads separadas para cada usuário, mantendo o contexto da conversa
    
    Exemplos de comandos:
    - "adicionar despesa de R$ 50 em Alimentação"
    - "registrar receita de R$ 2000 como Salário"
    - "listar despesas de janeiro"
    - "qual meu saldo atual"
    """
    # Formata o número de telefone (remove espaços, símbolos etc.)
    phone_number = ''.join(filter(str.isdigit, request.phone_number))

    if is_greeting(request.command):
        try:
            # Verifica se o contato já existe para personalizar a saudação
            contact = await whatsapp_contact_usecases.get_contact_by_phone(phone_number)
            name_part = f", {contact.name}" if contact and contact.name else ""
            
            # Personaliza a mensagem de boas-vindas
            welcome_message = (
                f"👋 *Olá{name_part}!*\n\n"
                f"Bem-vindo ao Financial Tracker! Como posso ajudar hoje?\n\n"
                f"Você pode me pedir para:\n"
                f"• Registrar despesas e receitas\n"
                f"• Verificar seu saldo atual\n"
                f"• Listar suas transações recentes\n"
                f"• E muito mais!\n\n"
                f"Digite *ajuda* para ver todos os comandos disponíveis."
            )
            
            # Se o contato existe, atualiza última interação
            if contact:
                await whatsapp_contact_usecases.update_last_interaction(phone_number)
            
            return WhatsAppResponse(
                status="success",
                message=welcome_message
            )
        except Exception as e:
            # Se ocorrer algum erro ao processar a saudação, continua com o fluxo normal
            print(f"Erro ao processar saudação: {str(e)}")
    
    # Obtém o gerenciador de threads
    thread_manager = get_thread_manager()
    
    # Define a função a ser executada na thread do usuário
    async def process_in_user_thread():
        try:
            # Verifica se o contato já existe
            contact = await whatsapp_contact_usecases.get_contact_by_phone(phone_number)
            
            # Se não existir ou o onboarding não estiver completo, processa o onboarding
            if not contact or not contact.onboarding_complete:
                onboarding_complete, response_message, updated_data = await whatsapp_contact_usecases.handle_onboarding_step(
                    phone_number=phone_number,
                    message=request.command
                )
                
                # Atualiza os dados do contato se necessário
                if updated_data:
                    # Atualiza a última interação
                    contact = await whatsapp_contact_usecases.update_last_interaction(phone_number)
                    
                    # Atualiza o status de onboarding
                    if "onboarding_step" in updated_data or "onboarding_complete" in updated_data:
                        contact = await whatsapp_contact_usecases.update_onboarding_status(
                            phone_number=phone_number,
                            complete=updated_data.get("onboarding_complete", False),
                            step=updated_data.get("onboarding_step")
                        )
                
                # Se o onboarding não estiver completo, retorna a mensagem de onboarding
                if not onboarding_complete:
                    return WhatsAppResponse(
                        status="onboarding",
                        message=response_message,
                        data={"step": updated_data.get("onboarding_step", "welcome")}
                    )
            
            # Registra o contato se necessário (não deveria acontecer, mas é uma garantia)
            if not contact:
                contact = await whatsapp_contact_usecases.register_contact(phone_number)
            
            # Processa o comando com o NLP
            result = await nlp_usecases.process_command(contact.user_id, request.command)
            
            # Atualiza a última interação
            await whatsapp_contact_usecases.update_last_interaction(phone_number)
            
            # Retorna o resultado formatado como resposta WhatsApp
            return WhatsAppResponse(
                status=result.get("status", "success"),
                message=result.get("message", ""),
                data=result.get("data")
            )
            
        except Exception as e:
            # Loga o erro (em um sistema real, você registraria isso em um sistema de logs)
            import logging
            logging.error(f"Erro ao processar mensagem WhatsApp de {phone_number}: {str(e)}")
            
            # Retorna uma mensagem de erro amigável
            return WhatsAppResponse(
                status="error",
                message="Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente em alguns instantes.",
                data={"error": str(e)}
            )
    
    # Processa na thread do usuário
    return await thread_manager.process_message(phone_number, process_in_user_thread)