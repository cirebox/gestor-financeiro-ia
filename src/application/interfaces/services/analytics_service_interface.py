# src/application/interfaces/services/analytics_service_interface.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, List, Optional
from uuid import UUID


class AnalyticsServiceInterface(ABC):
    """Interface para o serviço de análises financeiras."""
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def identify_trends(self, user_id: UUID, months: int = 6) -> Dict[str, Any]:
        """
        Identifica tendências financeiras nos últimos meses.
        
        Args:
            user_id: ID do usuário
            months: Número de meses para análise
            
        Returns:
            Análise de tendências financeiras
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def suggest_budget(self, user_id: UUID) -> Dict[str, Any]:
        """
        Sugere um orçamento com base no histórico financeiro.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Sugestão de orçamento
        """
        pass
    
    @abstractmethod
    async def get_financial_health_score(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calcula um score de saúde financeira para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Score de saúde financeira e recomendações
        """
        pass