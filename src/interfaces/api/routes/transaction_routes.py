# src/interfaces/api/routes/transaction_routes.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.usecases.transaction_usecases import TransactionUseCases
from src.domain.value_objects.money import Money
from src.domain.entities.user import User
from src.application.security.auth import get_current_active_user
from src.interfaces.api.dependencies import get_transaction_usecases, get_user_id_from_user, get_current_user_id


router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    """DTO para criação de transação."""
    
    type: str = Field(..., description="Tipo da transação ('income' ou 'expense')")
    amount: float = Field(..., description="Valor da transação")
    category: str = Field(..., description="Categoria da transação")
    description: str = Field(..., description="Descrição da transação")
    date: Optional[datetime] = Field(None, description="Data da transação (opcional)")
    priority: Optional[str] = Field(None, description="Prioridade da transação (alta, média, baixa)")
    tags: Optional[List[str]] = Field(None, description="Tags para classificação")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "expense",
                "amount": 50.0,
                "category": "Alimentação",
                "description": "Almoço",
                "date": "2023-01-15T12:00:00Z",
                "priority": "média",
                "tags": ["trabalho", "restaurante"]
            }
        }


class TransactionUpdate(BaseModel):
    """DTO para atualização de transação."""
    
    amount: Optional[float] = Field(None, description="Valor da transação")
    category: Optional[str] = Field(None, description="Categoria da transação")
    description: Optional[str] = Field(None, description="Descrição da transação")
    date: Optional[datetime] = Field(None, description="Data da transação")
    priority: Optional[str] = Field(None, description="Prioridade da transação")
    tags: Optional[List[str]] = Field(None, description="Tags para classificação")
    
    class Config:
        schema_extra = {
            "example": {
                "amount": 75.0,
                "category": "Alimentação",
                "description": "Almoço e jantar",
                "date": "2023-01-15T12:00:00Z",
                "priority": "alta",
                "tags": ["trabalho", "restaurante", "importante"]
            }
        }


class RecurringTransactionCreate(BaseModel):
    """DTO para criação de transação recorrente."""
    
    type: str = Field(..., description="Tipo da transação ('income' ou 'expense')")
    amount: float = Field(..., description="Valor da transação")
    category: str = Field(..., description="Categoria da transação")
    description: str = Field(..., description="Descrição da transação")
    frequency: str = Field(..., description="Frequência da recorrência (diária, semanal, mensal, etc.)")
    start_date: Optional[datetime] = Field(None, description="Data inicial (opcional)")
    end_date: Optional[datetime] = Field(None, description="Data final (opcional)")
    occurrences: Optional[int] = Field(None, description="Número de ocorrências (opcional)")
    priority: Optional[str] = Field(None, description="Prioridade da transação")
    tags: Optional[List[str]] = Field(None, description="Tags para classificação")


class InstallmentTransactionCreate(BaseModel):
    """DTO para criação de transação parcelada."""
    
    amount: float = Field(..., description="Valor da transação")
    category: str = Field(..., description="Categoria da transação")
    description: str = Field(..., description="Descrição da transação")
    total_installments: int = Field(..., description="Número total de parcelas")
    start_date: Optional[datetime] = Field(None, description="Data da primeira parcela (opcional)")
    priority: Optional[str] = Field(None, description="Prioridade da transação")
    tags: Optional[List[str]] = Field(None, description="Tags para classificação")


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
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    
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
                "created_at": "2023-01-15T12:00:00Z",
                "priority": "média",
                "tags": ["trabalho", "restaurante"]
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


@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_active_user),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Cria uma nova transação."""
    try:
        created_transaction = await transaction_usecases.add_transaction(
            user_id=current_user.id,  # Usa o ID do usuário autenticado
            type=transaction.type,
            amount=transaction.amount,
            category=transaction.category,
            description=transaction.description,
            date=transaction.date,
            priority=transaction.priority,
            tags=transaction.tags
        )
        
        return TransactionResponse(
            id=str(created_transaction.id),
            user_id=str(created_transaction.user_id),
            type=created_transaction.type,
            amount=float(created_transaction.amount.amount),
            category=created_transaction.category,
            description=created_transaction.description,
            date=created_transaction.date,
            created_at=created_transaction.created_at,
            priority=created_transaction.priority,
            tags=created_transaction.tags
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar transação: {str(e)}")


@router.post("/recurring", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_transaction(
    transaction: RecurringTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Cria uma nova transação recorrente."""
    try:
        created_transaction = await transaction_usecases.add_recurring_transaction(
            user_id=current_user.id,  # Usa o ID do usuário autenticado
            type=transaction.type,
            amount=transaction.amount,
            category=transaction.category,
            description=transaction.description,
            frequency=transaction.frequency,
            start_date=transaction.start_date,
            end_date=transaction.end_date,
            occurrences=transaction.occurrences,
            priority=transaction.priority,
            tags=transaction.tags
        )
        
        return TransactionResponse(
            id=str(created_transaction.id),
            user_id=str(created_transaction.user_id),
            type=created_transaction.type,
            amount=float(created_transaction.amount.amount),
            category=created_transaction.category,
            description=created_transaction.description,
            date=created_transaction.date,
            created_at=created_transaction.created_at,
            priority=created_transaction.priority,
            tags=created_transaction.tags
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar transação recorrente: {str(e)}")


@router.post("/installment", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_installment_transaction(
    transaction: InstallmentTransactionCreate,
    current_user: User = Depends(get_current_active_user),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Cria uma nova transação parcelada."""
    try:
        created_transaction = await transaction_usecases.add_installment_transaction(
            user_id=current_user.id,  # Usa o ID do usuário autenticado
            type="expense",  # Transações parceladas são sempre despesas
            amount=transaction.amount,
            category=transaction.category,
            description=transaction.description,
            total_installments=transaction.total_installments,
            start_date=transaction.start_date,
            priority=transaction.priority,
            tags=transaction.tags
        )
        
        return TransactionResponse(
            id=str(created_transaction.id),
            user_id=str(created_transaction.user_id),
            type=created_transaction.type,
            amount=float(created_transaction.amount.amount),
            category=created_transaction.category,
            description=created_transaction.description,
            date=created_transaction.date,
            created_at=created_transaction.created_at,
            priority=created_transaction.priority,
            tags=created_transaction.tags
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao criar transação parcelada: {str(e)}")


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    start_date: Optional[datetime] = Query(None, description="Data inicial do período"),
    end_date: Optional[datetime] = Query(None, description="Data final do período"),
    category: Optional[str] = Query(None, description="Filtrar por categoria"),
    type: Optional[str] = Query(None, description="Filtrar por tipo ('income' ou 'expense')"),
    priority: Optional[str] = Query(None, description="Filtrar por prioridade"),
    tags: Optional[List[str]] = Query(None, description="Filtrar por tags"),
    current_user: User = Depends(get_current_active_user),
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
        
    if priority:
        filters["priority"] = priority
        
    if tags:
        filters["tags"] = tags
    
    try:
        transactions = await transaction_usecases.get_transactions(current_user.id, filters)
        
        return [
            TransactionResponse(
                id=str(tx.id),
                user_id=str(tx.user_id),
                type=tx.type,
                amount=float(tx.amount.amount),
                category=tx.category,
                description=tx.description,
                date=tx.date,
                created_at=tx.created_at,
                priority=tx.priority,
                tags=tx.tags
            )
            for tx in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar transações: {str(e)}")


@router.get("/recurring", response_model=List[TransactionResponse])
async def list_recurring_transactions(
    current_user: User = Depends(get_current_active_user),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Lista as transações recorrentes do usuário."""
    try:
        transactions = await transaction_usecases.get_recurring_transactions(current_user.id)
        
        return [
            TransactionResponse(
                id=str(tx.id),
                user_id=str(tx.user_id),
                type=tx.type,
                amount=float(tx.amount.amount),
                category=tx.category,
                description=tx.description,
                date=tx.date,
                created_at=tx.created_at,
                priority=tx.priority,
                tags=tx.tags
            )
            for tx in transactions
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao listar transações recorrentes: {str(e)}")


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_active_user),
    transaction_usecases: TransactionUseCases = Depends(get_transaction_usecases)
):
    """Recupera uma transação específica pelo ID."""
    try:
        transaction = await transaction_usecases.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transação não encontrada")
        
        # Verifica se a transação pertence ao usuário atual
        if transaction.user_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso negado a esta transação")
        
        return TransactionResponse(
            id=str(transaction.id),
            user_id=str(transaction.user_id),
            type=transaction.type,
            amount=float(transaction.amount.amount),
            category=transaction.category,
            description=transaction.description,
            date=transaction.date,
            created_at=transaction.created_at,
            priority=transaction.priority,
            tags=transaction.tags
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao recuperar transação: {str(e)}")