# src/interfaces/api/routes/nlp_routes.py
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from src.application.usecases.nlp_usecases import NLPUseCases
from src.interfaces.api.dependencies import get_nlp_usecases, get_current_user_id


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


@router.post("/process", response_model=NLPResponse)
async def process_command(
    request: NLPRequest,
    user_id: UUID = Depends(get_current_user_id),
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
        result = await nlp_usecases.process_command(user_id, request.command)
        return NLPResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao processar comando: {str(e)}")