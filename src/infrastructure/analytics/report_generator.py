# src/infrastructure/analytics/report_generator.py
import calendar
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from uuid import UUID

from src.application.interfaces.services.analytics_service_interface import AnalyticsServiceInterface
from src.infrastructure.database.mongodb.connection import MongoDBConnection


class ReportGenerator(AnalyticsServiceInterface):
    """Implementação do serviço de análises financeiras."""
    
    def __init__(self):
        """Inicializa o gerador de relatórios com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.db = self.connection.db
    
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
        # Define o período do mês
        start_date = datetime(year, month, 1)
        last_day = calendar.monthrange(year, month)[1]
        end_date = datetime(year, month, last_day, 23, 59, 59)
        
        # Busca as transações do mês
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Calcula totais
        total_income, total_expense = self._calculate_totals(transactions)
        
        # Agrupa por categoria
        category_summary = self._group_by_category(transactions)
        
        # Calcula percentuais por categoria
        category_percentages = self._calculate_category_percentages(category_summary, total_income, total_expense)
        
        # Calcula variação em relação ao mês anterior
        previous_month_stats = await self._get_previous_month_stats(user_id, year, month)
        
        # Calcula tendências para o mês seguinte
        future_predictions = await self._predict_next_month(user_id, year, month)
        
        # Formata o relatório final
        month_name = calendar.month_name[month]
        
        return {
            "month": f"{month_name} {year}",
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "balance": total_income - total_expense,
                "save_rate": (total_income - total_expense) / total_income * 100 if total_income > 0 else 0
            },
            "categories": category_summary,
            "category_percentages": category_percentages,
            "comparison": {
                "previous_month": previous_month_stats,
                "income_change_percentage": self._calculate_change_percentage(
                    previous_month_stats.get("total_income", 0), 
                    total_income
                ),
                "expense_change_percentage": self._calculate_change_percentage(
                    previous_month_stats.get("total_expense", 0), 
                    total_expense
                )
            },
            "predictions": future_predictions,
            "transaction_count": len(transactions)
        }
    
    async def identify_trends(self, user_id: UUID, months: int = 6) -> Dict[str, Any]:
        """
        Identifica tendências financeiras nos últimos meses.
        
        Args:
            user_id: ID do usuário
            months: Número de meses para análise
            
        Returns:
            Análise de tendências financeiras
        """
        # Calcula o período de análise
        end_date = datetime.now()
        start_date = datetime(end_date.year, end_date.month, 1) - timedelta(days=30 * (months - 1))
        
        # Busca as transações do período
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Agrupa por mês
        monthly_data = self._group_by_month(transactions)
        
        # Calcula tendências
        income_trend = self._calculate_trend([m.get("total_income", 0) for m in monthly_data.values()])
        expense_trend = self._calculate_trend([m.get("total_expense", 0) for m in monthly_data.values()])
        savings_trend = self._calculate_trend([
            m.get("total_income", 0) - m.get("total_expense", 0) for m in monthly_data.values()
        ])
        
        # Analisa tendências por categoria
        category_trends = self._analyze_category_trends(monthly_data)
        
        # Identifica os maiores gastos (top 5)
        top_expenses = self._identify_top_expenses(transactions, 5)
        
        # Identifica gastos recorrentes
        recurring_expenses = self._identify_recurring_expenses(transactions)
        
        return {
            "period": {
                "start": start_date.strftime("%B %Y"),
                "end": end_date.strftime("%B %Y"),
                "months": months
            },
            "trends": {
                "income": {
                    "direction": "up" if income_trend > 0 else "down" if income_trend < 0 else "stable",
                    "percentage": abs(income_trend) * 100
                },
                "expense": {
                    "direction": "up" if expense_trend > 0 else "down" if expense_trend < 0 else "stable",
                    "percentage": abs(expense_trend) * 100
                },
                "savings": {
                    "direction": "up" if savings_trend > 0 else "down" if savings_trend < 0 else "stable",
                    "percentage": abs(savings_trend) * 100
                }
            },
            "monthly_data": [
                {
                    "month": month,
                    "income": data.get("total_income", 0),
                    "expense": data.get("total_expense", 0),
                    "balance": data.get("total_income", 0) - data.get("total_expense", 0)
                }
                for month, data in monthly_data.items()
            ],
            "category_trends": category_trends,
            "top_expenses": top_expenses,
            "recurring_expenses": recurring_expenses
        }
    
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
        # Se não foi informado um período, usa o mês atual
        if not start_date or not end_date:
            now = datetime.now()
            start_date = datetime(now.year, now.month, 1)
            end_date = datetime(now.year, now.month, calendar.monthrange(now.year, now.month)[1], 23, 59, 59)
        
        # Busca as transações do período
        transactions = await self._get_transactions(user_id, start_date, end_date, "expense")
        
        # Agrupa por categoria
        result = []
        category_totals = {}
        
        for tx in transactions:
            category = tx.get("category", "Outros")
            amount = tx.get("amount", 0)
            
            if category not in category_totals:
                category_totals[category] = 0
                
            category_totals[category] += amount
        
        # Calcula o total geral
        total_expense = sum(category_totals.values())
        
        # Formata o resultado
        for category, amount in category_totals.items():
            result.append({
                "category": category,
                "amount": amount,
                "percentage": (amount / total_expense * 100) if total_expense > 0 else 0
            })
        
        # Ordena por valor (maior para menor)
        result.sort(key=lambda x: x["amount"], reverse=True)
        
        return result
    
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
        # Busca histórico dos últimos 6 meses
        end_date = datetime(year, month, 1) - timedelta(days=1)  # Último dia do mês anterior
        start_date = end_date - timedelta(days=180)  # Aproximadamente 6 meses antes
        
        # Busca as transações do período
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Agrupa por mês
        monthly_data = self._group_by_month(transactions)
        
        # Se não há dados suficientes, usa a média dos meses disponíveis
        if len(monthly_data) < 3:
            avg_expense = sum([m.get("total_expense", 0) for m in monthly_data.values()]) / max(1, len(monthly_data))
            avg_income = sum([m.get("total_income", 0) for m in monthly_data.values()]) / max(1, len(monthly_data))
            
            return {
                "month": f"{calendar.month_name[month]} {year}",
                "prediction_method": "average",
                "predicted_expense": avg_expense,
                "predicted_income": avg_income,
                "confidence": "low",
                "categories": {}
            }
        
        # Usa um modelo simples de regressão linear para prever gastos
        x = list(range(len(monthly_data)))
        y_expense = [m.get("total_expense", 0) for m in monthly_data.values()]
        y_income = [m.get("total_income", 0) for m in monthly_data.values()]
        
        # Calcula a tendência para o próximo mês
        predicted_expense = self._linear_regression_predict(x, y_expense, len(monthly_data))
        predicted_income = self._linear_regression_predict(x, y_income, len(monthly_data))
        
        # Previsão por categoria (média dos últimos 3 meses)
        category_predictions = {}
        last_3_months = list(monthly_data.values())[-3:]
        
        all_categories = set()
        for month_data in last_3_months:
            for category, amounts in month_data.get("categories", {}).items():
                all_categories.add(category)
        
        for category in all_categories:
            category_values = []
            for month_data in last_3_months:
                categories = month_data.get("categories", {})
                if category in categories:
                    category_values.append(categories[category].get("expense", 0))
            
            if category_values:
                category_predictions[category] = sum(category_values) / len(category_values)
        
        return {
            "month": f"{calendar.month_name[month]} {year}",
            "prediction_method": "linear_regression",
            "predicted_expense": max(0, predicted_expense),  # Evita valores negativos
            "predicted_income": max(0, predicted_income),
            "confidence": "medium" if len(monthly_data) >= 6 else "low",
            "categories": category_predictions
        }
    
    async def suggest_budget(self, user_id: UUID) -> Dict[str, Any]:
        """
        Sugere um orçamento com base no histórico financeiro.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Sugestão de orçamento
        """
        # Busca histórico dos últimos 3 meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)  # Aproximadamente 3 meses
        
        # Busca as transações do período
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Se não há dados suficientes, retorna um orçamento genérico
        if not transactions:
            return {
                "message": "Não há dados suficientes para sugerir um orçamento personalizado.",
                "suggestion": "Comece registrando suas despesas e receitas para receber sugestões personalizadas.",
                "budget": {}
            }
        
        # Calcula a média de receita mensal
        income_transactions = [tx for tx in transactions if tx.get("type") == "income"]
        monthly_income = sum([tx.get("amount", 0) for tx in income_transactions]) / 3
        
        # Agrupa despesas por categoria e calcula a média mensal
        expense_by_category = {}
        for tx in transactions:
            if tx.get("type") == "expense":
                category = tx.get("category", "Outros")
                amount = tx.get("amount", 0)
                
                if category not in expense_by_category:
                    expense_by_category[category] = 0
                    
                expense_by_category[category] += amount
        
        # Calcula a média mensal por categoria
        for category in expense_by_category:
            expense_by_category[category] /= 3
        
        # Aplica regras de orçamento sugeridas (50/30/20)
        # 50% para necessidades, 30% para desejos, 20% para economias
        total_expense = sum(expense_by_category.values())
        current_saving_rate = (monthly_income - total_expense) / monthly_income if monthly_income > 0 else 0
        
        # Categorias essenciais (exemplo)
        essential_categories = ["Moradia", "Alimentação", "Transporte", "Saúde", "Educação"]
        
        # Separa despesas em essenciais e não essenciais
        essential_expenses = sum([expense_by_category.get(cat, 0) for cat in essential_categories])
        non_essential_expenses = total_expense - essential_expenses
        
        # Calcula os valores ideais conforme a regra 50/30/20
        ideal_essentials = monthly_income * 0.5
        ideal_non_essentials = monthly_income * 0.3
        ideal_savings = monthly_income * 0.2
        
        # Ajusta o orçamento sugerido
        suggested_budget = {}
        
        # Ajusta categorias essenciais
        essential_ratio = ideal_essentials / essential_expenses if essential_expenses > 0 else 1
        for category in essential_categories:
            if category in expense_by_category:
                suggested_budget[category] = min(expense_by_category[category], expense_by_category[category] * essential_ratio)
        
        # Ajusta categorias não essenciais
        non_essential_categories = [cat for cat in expense_by_category if cat not in essential_categories]
        non_essential_ratio = ideal_non_essentials / non_essential_expenses if non_essential_expenses > 0 else 1
        for category in non_essential_categories:
            suggested_budget[category] = min(expense_by_category[category], expense_by_category[category] * non_essential_ratio)
        
        return {
            "monthly_income": monthly_income,
            "current": {
                "total_expense": total_expense,
                "essential_expenses": essential_expenses,
                "non_essential_expenses": non_essential_expenses,
                "savings": monthly_income - total_expense,
                "saving_rate": current_saving_rate * 100
            },
            "ideal": {
                "essential_expenses": ideal_essentials,
                "non_essential_expenses": ideal_non_essentials,
                "savings": ideal_savings
            },
            "suggested_budget": suggested_budget,
            "message": self._get_budget_message(current_saving_rate)
        }
    
    async def get_financial_health_score(self, user_id: UUID) -> Dict[str, Any]:
        """
        Calcula um score de saúde financeira para o usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Score de saúde financeira e recomendações
        """
        # Busca histórico dos últimos 6 meses
        end_date = datetime.now()
        start_date = end_date - timedelta(days=180)
        
        # Busca as transações do período
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Se não há dados suficientes, retorna uma mensagem informativa
        if not transactions:
            return {
                "message": "Não há dados suficientes para calcular um score de saúde financeira.",
                "suggestion": "Registre suas transações por pelo menos 3 meses para receber uma avaliação.",
                "score": None
            }
        
        # Agrupa transações por mês
        monthly_data = self._group_by_month(transactions)
        
        # Calcula métricas
        total_months = len(monthly_data)
        positive_balance_months = sum(1 for m in monthly_data.values() if m.get("total_income", 0) >= m.get("total_expense", 0))
        saving_rates = [(m.get("total_income", 0) - m.get("total_expense", 0)) / m.get("total_income", 1) for m in monthly_data.values()]
        avg_saving_rate = sum(saving_rates) / total_months if total_months > 0 else 0
        
        # Calcula a consistência da economia
        consistency = positive_balance_months / total_months if total_months > 0 else 0
        
        # Avalia a variação de gastos mês a mês (menor variação é melhor)
        expenses = [m.get("total_expense", 0) for m in monthly_data.values()]
        expense_variation = np.std(expenses) / np.mean(expenses) if expenses and np.mean(expenses) > 0 else 1
        
        # Calcula o score
        saving_score = min(100, max(0, avg_saving_rate * 100))  # 0-100 baseado na taxa de economia
        consistency_score = consistency * 100  # 0-100 baseado na consistência
        variation_score = max(0, 100 - (expense_variation * 100))  # 0-100 (menor variação = maior pontuação)
        
        # Combina os scores com pesos
        final_score = (saving_score * 0.5) + (consistency_score * 0.3) + (variation_score * 0.2)
        
        # Determina a categoria do score
        category = "Excelente" if final_score >= 80 else \
                  "Boa" if final_score >= 60 else \
                  "Regular" if final_score >= 40 else \
                  "Preocupante" if final_score >= 20 else "Crítica"
        
        # Gera recomendações com base no score
        recommendations = self._get_financial_recommendations(final_score, saving_score, consistency_score, variation_score)
        
        return {
            "score": final_score,
            "category": category,
            "metrics": {
                "saving_rate": avg_saving_rate * 100,
                "consistency": consistency * 100,
                "expense_variation": expense_variation * 100
            },
            "period": {
                "start": start_date.strftime("%B %Y"),
                "end": end_date.strftime("%B %Y"),
                "months": total_months
            },
            "recommendations": recommendations
        }
    
    # Métodos auxiliares
    
    async def _get_transactions(self, 
                              user_id: UUID, 
                              start_date: datetime, 
                              end_date: datetime,
                              type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Busca transações no banco de dados."""
        query = {
            "userId": str(user_id),
            "date": {
                "$gte": start_date,
                "$lte": end_date
            }
        }
        
        if type:
            query["type"] = type
        
        cursor = self.db.transactions.find(query)
        return await cursor.to_list(length=None)
    
    def _calculate_totals(self, transactions: List[Dict[str, Any]]) -> Tuple[float, float]:
        """Calcula o total de receitas e despesas."""
        total_income = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "income")
        total_expense = sum(tx.get("amount", 0) for tx in transactions if tx.get("type") == "expense")
        return total_income, total_expense
    
    def _group_by_category(self, transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Agrupa transações por categoria."""
        result = {}
        
        for tx in transactions:
            category = tx.get("category", "Outros")
            tx_type = tx.get("type", "expense")
            amount = tx.get("amount", 0)
            
            if category not in result:
                result[category] = {
                    "income": 0,
                    "expense": 0,
                    "transactions": []
                }
            
            result[category][tx_type] += amount
            result[category]["transactions"].append(tx)
        
        return result
    
    def _calculate_category_percentages(self, 
                                      category_summary: Dict[str, Dict[str, Any]], 
                                      total_income: float, 
                                      total_expense: float) -> List[Dict[str, Any]]:
        """Calcula percentuais de cada categoria em relação ao total."""
        result = []
        
        for category, data in category_summary.items():
            income_percentage = (data["income"] / total_income * 100) if total_income > 0 else 0
            expense_percentage = (data["expense"] / total_expense * 100) if total_expense > 0 else 0
            
            result.append({
                "category": category,
                "income_percentage": income_percentage,
                "expense_percentage": expense_percentage
            })
        
        return result
    
    async def _get_previous_month_stats(self, user_id: UUID, year: int, month: int) -> Dict[str, Any]:
        """Obtém estatísticas do mês anterior."""
        # Calcula o mês anterior
        if month == 1:
            previous_month = 12
            previous_year = year - 1
        else:
            previous_month = month - 1
            previous_year = year
        
        # Define o período do mês anterior
        start_date = datetime(previous_year, previous_month, 1)
        last_day = calendar.monthrange(previous_year, previous_month)[1]
        end_date = datetime(previous_year, previous_month, last_day, 23, 59, 59)
        
        # Busca as transações do mês anterior
        transactions = await self._get_transactions(user_id, start_date, end_date)
        
        # Calcula totais
        total_income, total_expense = self._calculate_totals(transactions)
        
        return {
            "month": f"{calendar.month_name[previous_month]} {previous_year}",
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense
        }
    
    async def _predict_next_month(self, user_id: UUID, year: int, month: int) -> Dict[str, Any]:
        """Prediz dados para o próximo mês."""
        # Calcula o próximo mês
        if month == 12:
            next_month = 1
            next_year = year + 1
        else:
            next_month = month + 1
            next_year = year
        
        # Usa o método existente para fazer a previsão
        return await self.predict_monthly_expense(user_id, next_month, next_year)
    
    def _calculate_change_percentage(self, previous_value: float, current_value: float) -> float:
        """Calcula o percentual de variação entre dois valores."""
        if previous_value == 0:
            return 100 if current_value > 0 else 0
        
        return ((current_value - previous_value) / previous_value) * 100
    
    def _group_by_month(self, transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Agrupa transações por mês."""
        result = {}
        
        for tx in transactions:
            date = tx.get("date", datetime.now())
            month_key = f"{date.year}-{date.month:02d}"
            tx_type = tx.get("type", "expense")
            amount = tx.get("amount", 0)
            category = tx.get("category", "Outros")
            
            if month_key not in result:
                result[month_key] = {
                    "month": date.strftime("%B %Y"),
                    "total_income": 0,
                    "total_expense": 0,
                    "categories": {},
                    "transactions": []
                }
            
            # Atualiza totais
            if tx_type == "income":
                result[month_key]["total_income"] += amount
            else:
                result[month_key]["total_expense"] += amount
            
            # Atualiza categorias
            if category not in result[month_key]["categories"]:
                result[month_key]["categories"][category] = {
                    "income": 0,
                    "expense": 0
                }
            
            result[month_key]["categories"][category][tx_type] += amount
            
            # Adiciona transação
            result[month_key]["transactions"].append(tx)
        
        return dict(sorted(result.items()))
    
    def _calculate_trend(self, values: List[float]) -> float:
        """Calcula a tendência linear de uma série de valores."""
        if not values or len(values) < 2:
            return 0
        
        # Normaliza valores
        if max(values) > 0:
            normalized = [v / max(values) for v in values]
        else:
            return 0
        
        # Se todos os valores forem iguais, não há tendência
        if len(set(normalized)) == 1:
            return 0
        
        # Calcula a tendência linear usando regressão linear simples
        x = list(range(len(normalized)))
        
        # Coeficientes
        n = len(normalized)
        sum_x = sum(x)
        sum_y = sum(normalized)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, normalized))
        sum_xx = sum(x_i ** 2 for x_i in x)
        
        # Cálculo da inclinação (slope)
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
        
        # Retorna a inclinação como indicador de tendência
        return slope
    
    def _analyze_category_trends(self, monthly_data: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Analisa tendências por categoria."""
        result = []
        
        # Coleta todas as categorias
        all_categories = set()
        for month_data in monthly_data.values():
            for category in month_data.get("categories", {}):
                all_categories.add(category)
        
        # Analisa tendência de cada categoria
        for category in all_categories:
            # Coleta valores mensais para a categoria
            values = []
            for month_data in monthly_data.values():
                categories = month_data.get("categories", {})
                expense = categories.get(category, {}).get("expense", 0)
                values.append(expense)
            
            # Calcula a tendência
            trend = self._calculate_trend(values)
            
            # Adiciona ao resultado se houver uma tendência significativa
            if abs(trend) > 0.05:  # Limiar para considerar uma tendência significativa
                result.append({
                    "category": category,
                    "direction": "up" if trend > 0 else "down",
                    "strength": abs(trend) * 100  # Percentual
                })
        
        # Ordena por força da tendência (mais forte primeiro)
        result.sort(key=lambda x: x["strength"], reverse=True)
        
        return result
    
    def _identify_top_expenses(self, transactions: List[Dict[str, Any]], limit: int = 5) -> List[Dict[str, Any]]:
        """Identifica as maiores despesas do período."""
        expenses = [tx for tx in transactions if tx.get("type") == "expense"]
        expenses.sort(key=lambda x: x.get("amount", 0), reverse=True)
        
        result = []
        for tx in expenses[:limit]:
            result.append({
                "id": tx.get("_id", ""),
                "description": tx.get("description", "Sem descrição"),
                "category": tx.get("category", "Outros"),
                "amount": tx.get("amount", 0),
                "date": tx.get("date", datetime.now()).strftime("%d/%m/%Y")
            })
        
        return result
    
    def _identify_recurring_expenses(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identifica despesas recorrentes baseadas em padrões de descrição e valor."""
        # Agrupa transações por descrição e categoria
        expense_groups = {}
        
        for tx in transactions:
            if tx.get("type") == "expense":
                key = f"{tx.get('description', '').lower()}|{tx.get('category', '')}"
                amount = tx.get("amount", 0)
                
                if key not in expense_groups:
                    expense_groups[key] = {
                        "transactions": [],
                        "total": 0,
                        "count": 0,
                        "amounts": []
                    }
                
                expense_groups[key]["transactions"].append(tx)
                expense_groups[key]["total"] += amount
                expense_groups[key]["count"] += 1
                expense_groups[key]["amounts"].append(amount)
        
        # Filtra grupos que aparecem pelo menos 3 vezes
        recurring = []
        
        for key, data in expense_groups.items():
            if data["count"] >= 3:
                description, category = key.split("|")
                first_tx = data["transactions"][0]
                
                # Calcula a variação dos valores
                std_dev = np.std(data["amounts"])
                mean = np.mean(data["amounts"])
                variation = std_dev / mean if mean > 0 else 1
                
                # Se a variação for pequena, considera como despesa recorrente
                if variation < 0.1:  # Menos de 10% de variação
                    recurring.append({
                        "description": description.capitalize(),
                        "category": category,
                        "average_amount": mean,
                        "frequency": self._determine_frequency(data["transactions"]),
                        "count": data["count"],
                        "last_date": max(tx.get("date", datetime.now()) for tx in data["transactions"]).strftime("%d/%m/%Y")
                    })
        
        # Ordena por valor médio (maior para menor)
        recurring.sort(key=lambda x: x["average_amount"], reverse=True)
        
        return recurring
    
    def _determine_frequency(self, transactions: List[Dict[str, Any]]) -> str:
        """Determina a frequência aproximada de transações recorrentes."""
        if not transactions or len(transactions) < 2:
            return "Desconhecida"
        
        # Ordena por data
        sorted_tx = sorted(transactions, key=lambda x: x.get("date", datetime.now()))
        
        # Calcula intervalos entre transações (em dias)
        intervals = []
        for i in range(1, len(sorted_tx)):
            current_date = sorted_tx[i].get("date", datetime.now())
            previous_date = sorted_tx[i-1].get("date", datetime.now())
            interval_days = (current_date - previous_date).days
            intervals.append(interval_days)
        
        # Calcula a média de intervalos
        avg_interval = sum(intervals) / len(intervals)
        
        # Determina a frequência aproximada
        if avg_interval <= 7:
            return "Semanal"
        elif avg_interval <= 15:
            return "Quinzenal"
        elif avg_interval <= 35:
            return "Mensal"
        elif avg_interval <= 95:
            return "Trimestral"
        elif avg_interval <= 185:
            return "Semestral"
        else:
            return "Anual"
    
    def _linear_regression_predict(self, x: List[int], y: List[float], predict_x: int) -> float:
        """Realiza uma regressão linear simples e faz uma previsão."""
        if not x or not y or len(x) != len(y):
            return 0
        
        n = len(x)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x_i * y_i for x_i, y_i in zip(x, y))
        sum_xx = sum(x_i ** 2 for x_i in x)
        
        # Cálculo dos coeficientes da regressão linear (y = a + bx)
        try:
            b = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
            a = (sum_y - b * sum_x) / n
            
            # Previsão
            return a + b * predict_x
        except ZeroDivisionError:
            # Se houver divisão por zero, retorna a média dos valores
            return sum_y / n if n > 0 else 0
    
    def _get_budget_message(self, saving_rate: float) -> str:
        """Retorna uma mensagem personalizada baseada na taxa de economia."""
        if saving_rate < 0:
            return "Alerta: Seus gastos estão excedendo sua renda. Considere reduzir despesas ou aumentar receitas urgentemente."
        elif saving_rate < 0.1:
            return "Atenção: Sua taxa de economia está abaixo de 10%. Tente reduzir gastos não essenciais para aumentar sua margem de segurança financeira."
        elif saving_rate < 0.2:
            return "Bom trabalho: Você está economizando entre 10% e 20% da sua renda. Para maior estabilidade financeira, considere aumentar ainda mais sua taxa de economia."
        else:
            return "Excelente: Você está economizando mais de 20% da sua renda, o que é um ótimo indicador de saúde financeira. Continue assim!"
    
    def _get_financial_recommendations(self, 
                                     final_score: float, 
                                     saving_score: float, 
                                     consistency_score: float, 
                                     variation_score: float) -> List[str]:
        """Gera recomendações personalizadas com base nos scores financeiros."""
        recommendations = []
        
        # Recomendações com base na taxa de economia
        if saving_score < 30:
            recommendations.append("Aumente sua taxa de economia. Tente implementar a regra 50/30/20: 50% para necessidades, 30% para desejos e 20% para economias.")
            recommendations.append("Analise seus maiores gastos e identifique áreas onde pode reduzir despesas sem comprometer sua qualidade de vida.")
        elif saving_score < 60:
            recommendations.append("Sua taxa de economia está razoável, mas pode ser melhorada. Tente aumentar gradualmente o valor economizado a cada mês.")
        
        # Recomendações com base na consistência
        if consistency_score < 50:
            recommendations.append("Procure manter seus gastos consistentemente abaixo da sua renda. Estabeleça um orçamento mensal e siga-o rigorosamente.")
            recommendations.append("Use a técnica de 'pagar-se primeiro': separe uma porcentagem da sua renda para economias assim que receber.")
        
        # Recomendações com base na variação de gastos
        if variation_score < 60:
            recommendations.append("Seus gastos mensais têm variado significativamente. Tente identificar despesas extraordinárias e planeje-se para elas com antecedência.")
            recommendations.append("Crie um fundo de emergência para cobrir despesas inesperadas sem comprometer seu orçamento regular.")
        
        # Recomendações gerais baseadas no score final
        if final_score < 40:
            recommendations.append("Considere usar ferramentas de orçamento ou aplicativos para monitorar seus gastos diários e categorizá-los adequadamente.")
            recommendations.append("Estabeleça metas financeiras claras de curto, médio e longo prazo para se manter motivado.")
        elif final_score < 70:
            recommendations.append("Você está no caminho certo! Continue monitorando seus gastos e considere investir o dinheiro que está economizando.")
        else:
            recommendations.append("Sua saúde financeira está excelente! Considere diversificar seus investimentos e planejar metas financeiras mais ambiciosas.")
        
        return recommendations