# src/interfaces/api/routes/nlp_routes.py
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Header, Request
from pydantic import BaseModel, Field

from src.application.usecases.nlp_usecases import NLPUseCases
from src.application.usecases.whatsapp_contact_usecases import WhatsAppContactUseCases
from src.domain.entities.user import User
from src.application.security.auth import get_current_active_user
from src.interfaces.api.dependencies import get_nlp_usecases, get_current_user_id, get_whatsapp_contact_usecases
from config import settings

# Secret key for WhatsApp integration API authentication
WHATSAPP_API_KEY = settings.WHATSAPP_API_KEY if hasattr(settings, 'WHATSAPP_API_KEY') else "whatsapp-integration-secret-key"

router = APIRouter(prefix="/nlp", tags=["nlp"])

class NLPRequest(BaseModel):
    """Requisição para processamento de linguagem natural."""
    
    command: str = Field(..., description="Comando em linguagem natural")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "adicionar despesa de R$ 50 em Alimentação"
            }
        }


class WhatsAppNLPRequest(BaseModel):
    """Requisição para processamento de linguagem natural via WhatsApp."""
    
    command: str = Field(..., description="Comando em linguagem natural", example="adicionar despesa de R$ 50 em Alimentação")
    phone_number: str = Field(..., description="Número de telefone do usuário do WhatsApp (apenas números)", example="5511999999999")
    
    class Config:
        schema_extra = {
            "example": {
                "command": "adicionar despesa de R$ 50 em Alimentação",
                "phone_number": "5511999999999"
            }
        }


class NLPResponse(BaseModel):
    """Resposta do processamento de linguagem natural."""
    
    status: str
    message: str
    data: Optional[Dict[str, Any]] = None
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Despesa de R$ 50,00 em Alimentação registrada com sucesso!",
                "data": {
                    "transaction_id": "123e4567-e89b-12d3-a456-426614174000"
                }
            }
        }


async def validate_whatsapp_api_key(
    api_key: str = Header(
        ..., 
        alias="X-WhatsApp-API-Key",
        description="Chave de API para autenticação da integração com WhatsApp",
        example="whatsapp-integration-secret-key"
    )
):
    """
    Valida a chave de API para integração com WhatsApp.
    
    Args:
        api_key: Chave de API fornecida no cabeçalho X-WhatsApp-API-Key
        
    Returns:
        A chave de API validada
        
    Raises:
        HTTPException: Se a chave de API for inválida
    """
    if api_key != WHATSAPP_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid WhatsApp API key"
        )
    return api_key


@router.post("/process", response_model=NLPResponse)
async def process_command(
    request: NLPRequest,
    current_user: User = Depends(get_current_active_user),
    nlp_usecases: NLPUseCases = Depends(get_nlp_usecases)
):
    """
    Processa um comando em linguagem natural.
    
    Exemplos de comandos:
    - "adicionar despesa de R$ 50 em Alimentação"
    - "registrar receita de R$ 2000 como Salário"
    - "listar despesas de janeiro"
    - "qual meu saldo atual"
    - "excluir transação id abc123"
    """
    try:
        result = await nlp_usecases.process_command(current_user.id, request.command)
        return NLPResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"Erro ao processar comando: {str(e)}"
        )


    