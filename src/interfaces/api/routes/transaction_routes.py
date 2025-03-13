# src/interfaces/api/routes/transaction_routes.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.application.usecases.transaction_usecases import TransactionUseCases
from src.domain.value_objects.money import Money
from src.interfaces.api.dependencies import get_transaction_usecases, get_current_user_id


router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    """DTO para criação de transação."""
    
    type: str = Field(..., description="Tipo da transação ('income' ou 'expense')")
    amount: float = Field(..., description="Valor da transação")
    category: str = Field(..., description="Categoria da transação")
    description: str = Field(..., description="Descrição da transação")
    date: Optional[datetime] = Field(None, description="Data da transação (opcional)")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "expense",
                "amount": 50.0,
                "category": "Alimentação",
                "description": "Almoço",
                "date": "2023-01-15T12:00:00Z"
            }
        }


class TransactionUpdate(BaseModel):
    """DTO para atualização de transação."""
    
    amount: Optional[float] = Field(None, description="Valor da transação")
    category: Optional[str] = Field(None, description="Categoria da transação")
    description: Optional[str] = Field(None, description="Descrição da transação")
    date: Optional[datetime] = Field(None, description="Data da transação")
    
    class Config:
        schema_extra = {
            "example": {
                "amount": 75.0,
                "category": "Alimentação",
                "description": "Almoço e jantar",
                "date": "2023-01-15T12:00:00Z"
            }
        }


class TransactionResponse(BaseModel):
    """DTO para resposta de transação."""
    
    id: str
    user_id: str
    type: str
    amount: float
    category: str
    description: str
    date: datetime
    created_at: datetime
    
    class Config:
        schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "type": "expense",
                "amount": 50.0,
                "category": "Alimentação",
                "description": "Almoço",
                "date": "2023-01-15T12:00:00Z",
                "created_at": "2023-01-15T12:00:00Z"
            }
        }


class BalanceResponse(BaseModel):
    """DTO para resposta de balanço financeiro."""
    
    total_income: float
    total_expense: float
    balance: float
    period: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "total_income": 2000.0,
                "total_expense": 1500.0,
                "balance": 500.0,
                "period": "Janeiro 2023"
            }
        }


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Cria uma nova transação."""
    try:
        created_transaction = await transaction_usecases.add_transaction(
            user_id=user_id,
            type=transaction.type,
            amount=transaction.amount,
            category=transaction.category,
            description=transaction.description,
            date=transaction.date
        )
        
        return TransactionResponse(
            id=str(created_transaction.id),
            user_id=str(created_transaction.user_id),
            type=created_transaction.type,
            amount=float(created_transaction.amount.amount),
            category=created_transaction.category,
            description=created_transaction.description,
            date=created_transaction.date,
            created_at=created_transaction.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao criar transação: {str(e)}")


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Data inicial do período"),
    end_date: Optional[datetime] = Query(None, description="Data final do período"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    type: Optional[str] = Query(None, description="Filtrar por tipo ('income' ou 'expense')"),
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Lista as transações do usuário com filtros opcionais."""
    filters = {}
    
    if start_date:
        filters["start_date"] = start_date
    
    if end_date:
        filters["end_date"] = end_date
    
    if category:
        filters["category"] = category
    
    if type:
        filters["type"] = type
    
    try:
        transactions = await transaction_usecases.get_transactions(user_id, filters)
        
        return [
            TransactionResponse(
                id=str(tx.id),
                user_id=str(tx.user_id),
                type=tx.type,
                amount=float(tx.amount.amount),
                category=tx.category,
                description=tx.description,
                date=tx.date,
                created_at=tx.created_at
            )
            for tx in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar transações: {str(e)}")


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Recupera uma transação específica pelo ID."""
    try:
        transaction = await transaction_usecases.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada")
        
        if transaction.user_id != user_id:
            raise HTTPException(status_code=403, detail="Acesso negado a esta transação")
        
        return TransactionResponse(
            id=str(transaction.id),
            user_id=str(transaction.user_id),
            type=transaction.type,
            amount=float(transaction.amount.amount),
            category=transaction.category,
            description=transaction.description,
            date=transaction.date,
            created_at=transaction.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao recuperar transação: {str(e)}")


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: UUID,
    transaction: TransactionUpdate,
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Atualiza uma transação existente."""
    # Verifica se a transação existe e pertence ao usuário
    tx = await transaction_usecases.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    if tx.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta transação")
    
    # Prepara dados para atualização
    update_data = {}
    
    if transaction.amount is not None:
        update_data["amount"] = Money(transaction.amount)
    
    if transaction.category is not None:
        update_data["category"] = transaction.category
    
    if transaction.description is not None:
        update_data["description"] = transaction.description
    
    if transaction.date is not None:
        update_data["date"] = transaction.date
    
    try:
        updated_transaction = await transaction_usecases.update_transaction(transaction_id, update_data)
        
        if not updated_transaction:
            raise HTTPException(status_code=404, detail="Transação não encontrada ou não foi possível atualizá-la")
        
        return TransactionResponse(
            id=str(updated_transaction.id),
            user_id=str(updated_transaction.user_id),
            type=updated_transaction.type,
            amount=float(updated_transaction.amount.amount),
            category=updated_transaction.category,
            description=updated_transaction.description,
            date=updated_transaction.date,
            created_at=updated_transaction.created_at
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao atualizar transação: {str(e)}")


@router.delete("/{transaction_id}", status_code=204)
async def delete_transaction(
    transaction_id: UUID,
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Remove uma transação existente."""
    # Verifica se a transação existe e pertence ao usuário
    tx = await transaction_usecases.get_transaction(transaction_id)
    if not tx:
        raise HTTPException(status_code=404, detail="Transação não encontrada")
    
    if tx.user_id != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado a esta transação")
    
    try:
        deleted = await transaction_usecases.delete_transaction(transaction_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="Transação não encontrada ou não foi possível excluí-la")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao excluir transação: {str(e)}")


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    start_date: Optional[datetime] = Query(None, description="Data inicial do período"),
    end_date: Optional[datetime] = Query(None, description="Data final do período"),
    user_id: UUID = Depends(get_current_user_id),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Calcula o balanço financeiro do usuário no período especificado."""
    try:
        balance = await transaction_usecases.get_balance(user_id, start_date, end_date)
        
        period = None
        if start_date and end_date:
            period = f"{start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')}"
        
        return BalanceResponse(
            total_income=balance["total_income"],
            total_expense=balance["total_expense"],
            balance=balance["balance"],
            period=period
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular balanço: {str(e)}")
