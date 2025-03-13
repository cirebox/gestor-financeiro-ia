# src/infrastructure/analytics/analytics_service.py
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID

from src.application.interfaces.services.analytics_service_interface import AnalyticsServiceInterface
from src.infrastructure.analytics.report_generator import ReportGenerator


class AnalyticsService(AnalyticsServiceInterface):
    """Implementação do serviço de análises financeiras."""
    
    def __init__(self):
        """Inicializa o serviço de análises."""
        self.report_generator = ReportGenerator()
    
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
        return await self.report_generator.generate_monthly_report(user_id, year, month)
    
    async def identify_trends(self, user_id: UUID, months: int = 6) -> Dict[str, Any]:
        """
        Identifica tendências financeiras nos últimos meses.
        
        Args:
            user_id: ID do usuário
            months: Número de meses para análise
            
        Returns:
            Análise de tendências financeiras
        """
        return await self.report_generator.identify_trends(user_id, months)
    
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
        return await self.report_generator.get_spending_by_category(user_id, start_date, end_date)
    
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
        return await self.report_generator.predict_monthly_expense(user_id, month, year)
    
    async def suggest_budget(self, user_id: UUID) -> Dict[str, Any]:
        """
        Sugere um orçamento com base no histórico financeiro.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Sugestão de orçamento
        """
        return await self.report_generator.suggest_budget(user_id)
    
    async def get_financial_health_score(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calcula um score de saúde financeira para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Score de saúde financeira e recomendações
        """
        return await self.report_generator.get_financial_health_score(user_id)