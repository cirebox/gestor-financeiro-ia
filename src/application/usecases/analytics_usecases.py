# src/application/usecases/analytics_usecases.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from src.application.interfaces.services.analytics_service_interface import AnalyticsServiceInterface
from src.application.interfaces.repositories.transaction_repository_interface import TransactionRepositoryInterface


class AnalyticsUseCases:
    """Casos de uso relacionados a análises financeiras."""
    
    def __init__(self, 
                 analytics_service: AnalyticsServiceInterface,
                 transaction_repository: TransactionRepositoryInterface):
        """
        Inicializa os casos de uso de análises.
        
        Args:
            analytics_service: Serviço de análise financeira
            transaction_repository: Repositório de transações
        """
        self.analytics_service = analytics_service
        self.transaction_repository = transaction_repository
    
    async def generate_monthly_report(self, user_id: UUID, year: int, month: int) -> Dict[str, Any]:
        """
        Gera um relatório mensal de finanças.
        
        Args:
            user_id: ID do usuário
            year: Ano do relatório
            month: Mês do relatório (1-12)
            
        Returns:
            Relatório mensal com análises financeiras
        """
        # Verifica se o mês é válido
        if month < 1 or month > 12:
            raise ValueError("Mês deve estar entre 1 e 12")
        
        # Gera o relatório
        return await self.analytics_service.generate_monthly_report(user_id, year, month)
    
    async def identify_trends(self, user_id: UUID, months: int = 6) -> Dict[str, Any]:
        """
        Identifica tendências financeiras nos últimos meses.
        
        Args:
            user_id: ID do usuário
            months: Número de meses para análise
            
        Returns:
            Análise de tendências financeiras
        """
        return await self.analytics_service.identify_trends(user_id, months)
    
    async def get_spending_by_category(self, 
                                     user_id: UUID, 
                                     start_date: Optional[datetime] = None, 
                                     end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Obtém os gastos por categoria em um período.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial do período
            end_date: Data final do período
            
        Returns:
            Lista de gastos por categoria
        """
        return await self.analytics_service.get_spending_by_category(user_id, start_date, end_date)
    
    async def predict_monthly_expense(self, user_id: UUID, month: int, year: int) -> Dict[str, Any]:
        """
        Prediz os gastos mensais com base no histórico.
        
        Args:
            user_id: ID do usuário
            month: Mês para previsão (1-12)
            year: Ano para previsão
            
        Returns:
            Previsão de gastos para o mês
        """
        # Verifica se o mês é válido
        if month < 1 or month > 12:
            raise ValueError("Mês deve estar entre 1 e 12")
        
        return await self.analytics_service.predict_monthly_expense(user_id, month, year)
    
    async def suggest_budget(self, user_id: UUID) -> Dict[str, Any]:
        """
        Sugere um orçamento com base no histórico financeiro.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Sugestão de orçamento
        """
        return await self.analytics_service.suggest_budget(user_id)
    
    async def get_financial_health_score(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calcula um score de saúde financeira para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Score de saúde financeira e recomendações
        """
        return await self.analytics_service.get_financial_health_score(user_id)