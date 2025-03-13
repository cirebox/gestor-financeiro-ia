# src/interfaces/api/routes/analytics_routes.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.application.usecases.analytics_usecases import AnalyticsUseCases
from src.interfaces.api.dependencies import get_analytics_usecases, get_current_user_id


router = APIRouter(prefix="/analytics", tags=["analytics"])


class MonthlyReportResponse(BaseModel):
    """DTO para resposta de relatório mensal."""
    
    month: str
    summary: Dict[str, Any]
    categories: Dict[str, Dict[str, Any]]
    category_percentages: List[Dict[str, Any]]
    comparison: Dict[str, Any]
    predictions: Dict[str, Any]
    transaction_count: int


class TrendsResponse(BaseModel):
    """DTO para resposta de tendências financeiras."""
    
    period: Dict[str, Any]
    trends: Dict[str, Dict[str, Any]]
    monthly_data: List[Dict[str, Any]]
    category_trends: List[Dict[str, Any]]
    top_expenses: List[Dict[str, Any]]
    recurring_expenses: List[Dict[str, Any]]


class CategorySpendingResponse(BaseModel):
    """DTO para resposta de gastos por categoria."""
    
    category: str
    amount: float
    percentage: float


class PredictionResponse(BaseModel):
    """DTO para resposta de previsão de gastos."""
    
    month: str
    prediction_method: str
    predicted_expense: float
    predicted_income: float
    confidence: str
    categories: Dict[str, float]


class BudgetResponse(BaseModel):
    """DTO para resposta de sugestão de orçamento."""
    
    monthly_income: float
    current: Dict[str, Any]
    ideal: Dict[str, Any]
    suggested_budget: Dict[str, float]
    message: str


class FinancialHealthResponse(BaseModel):
    """DTO para resposta de saúde financeira."""
    
    score: Optional[float]
    category: Optional[str]
    metrics: Optional[Dict[str, float]]
    period: Optional[Dict[str, Any]]
    recommendations: Optional[List[str]]
    message: Optional[str]
    suggestion: Optional[str]


@router.get("/reports/monthly", response_model=MonthlyReportResponse)
async def get_monthly_report(
    year: int = Query(..., description="Ano do relatório"),
    month: int = Query(..., description="Mês do relatório (1-12)"),
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Gera um relatório mensal de finanças."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
            
        report = await analytics_usecases.generate_monthly_report(user_id, year, month)
        return report
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar relatório mensal: {str(e)}")


@router.get("/trends", response_model=TrendsResponse)
async def get_trends(
    months: int = Query(6, description="Número de meses para análise"),
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Identifica tendências financeiras nos últimos meses."""
    try:
        if months < 2:
            raise HTTPException(status_code=400, detail="Número de meses deve ser pelo menos 2")
            
        trends = await analytics_usecases.identify_trends(user_id, months)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao identificar tendências: {str(e)}")


@router.get("/spending-by-category", response_model=List[CategorySpendingResponse])
async def get_spending_by_category(
    start_date: Optional[datetime] = Query(None, description="Data inicial do período"),
    end_date: Optional[datetime] = Query(None, description="Data final do período"),
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Obtém os gastos por categoria em um período."""
    try:
        spending = await analytics_usecases.get_spending_by_category(user_id, start_date, end_date)
        return spending
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao obter gastos por categoria: {str(e)}")


@router.get("/predict-expense", response_model=PredictionResponse)
async def predict_monthly_expense(
    year: int = Query(..., description="Ano para previsão"),
    month: int = Query(..., description="Mês para previsão (1-12)"),
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Prediz os gastos mensais com base no histórico."""
    try:
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Mês deve estar entre 1 e 12")
            
        prediction = await analytics_usecases.predict_monthly_expense(user_id, month, year)
        return prediction
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao prever gastos: {str(e)}")


@router.get("/suggest-budget", response_model=BudgetResponse)
async def suggest_budget(
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Sugere um orçamento com base no histórico financeiro."""
    try:
        budget = await analytics_usecases.suggest_budget(user_id)
        return budget
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao sugerir orçamento: {str(e)}")


@router.get("/financial-health", response_model=FinancialHealthResponse)
async def get_financial_health(
    user_id: UUID = Depends(get_current_user_id),
    analytics_usecases: AnalyticsUseCases = Depends(get_analytics_usecases)
):
    """Calcula um score de saúde financeira para o usuário."""
    try:
        health_score = await analytics_usecases.get_financial_health_score(user_id)
        return health_score
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao calcular saúde financeira: {str(e)}")