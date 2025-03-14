# src/infrastructure/database/repositories/mongodb_transaction_repository.py
from datetime import datetime
from typing import Dict, List, Optional, Any
from uuid import UUID

from src.application.interfaces.repositories.transaction_repository_interface import TransactionRepositoryInterface
from src.domain.entities.transaction import Transaction
from src.domain.value_objects.money import Money
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.infrastructure.database.mongodb.models.transaction_model import TransactionModel


class MongoDBTransactionRepository(TransactionRepositoryInterface):
    """Implementação do repositório de transações usando MongoDB."""
    
    def __init__(self):
        """Inicializa o repositório com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.collection = self.connection.db.transactions
    
    async def add(self, transaction: Transaction) -> Transaction:
        """
        Adiciona uma nova transação.
        
        Args:
            transaction: A transação a ser adicionada
            
        Returns:
            A transação adicionada com ID atualizado
        """
        transaction_dict = TransactionModel.to_dict(transaction)
        await self.collection.insert_one(transaction_dict)
        return transaction
    
    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Recupera uma transação pelo ID.
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            A transação encontrada ou None
        """
        data = await self.collection.find_one({"_id": str(transaction_id)})
        return TransactionModel.from_dict(data)
    
    async def get_by_user(self, user_id: UUID, filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        Recupera as transações de um usuário, opcionalmente filtradas.
        
        Args:
            user_id: ID do usuário
            filters: Filtros opcionais como data, categoria, tipo, etc.
            
        Returns:
            Lista de transações que correspondem aos critérios
        """
        query = {"userId": str(user_id)}
        
        if filters:
            # Processamento de filtros existentes
            if "start_date" in filters and "end_date" in filters:
                query["date"] = {
                    "$gte": filters["start_date"],
                    "$lte": filters["end_date"]
                }
            elif "date_after" in filters:
                query["date"] = {"$gte": filters["date_after"]}
            elif "date_before" in filters:
                query["date"] = {"$lte": filters["date_before"]}
            
            # Filtro de mês específico
            elif "month" in filters:
                month_start = filters["month"]
                if month_start.month == 12:
                    month_end = datetime(month_start.year + 1, 1, 1) - datetime.timedelta(days=1)
                else:
                    month_end = datetime(month_start.year, month_start.month + 1, 1) - datetime.timedelta(days=1)
                
                query["date"] = {
                    "$gte": month_start,
                    "$lte": month_end
                }
            
            # Filtro de categoria
            if "category" in filters:
                query["category"] = filters["category"]
            
            # Filtro de tipo
            if "type" in filters:
                query["type"] = filters["type"]
                
            # Filtro de prioridade
            if "priority" in filters:
                query["priority"] = filters["priority"]
                
            # Filtro de recorrência
            if "has_recurrence" in filters:
                if filters["has_recurrence"]:
                    query["recurrence"] = {"$exists": True, "$ne": None}
                else:
                    query["$or"] = [
                        {"recurrence": {"$exists": False}},
                        {"recurrence": None}
                    ]
                    
            # Filtro de parcelamento
            if "has_installment_info" in filters:
                if filters["has_installment_info"]:
                    query["installmentInfo"] = {"$exists": True, "$ne": None}
                else:
                    query["$or"] = [
                        {"installmentInfo": {"$exists": False}},
                        {"installmentInfo": None}
                    ]
                    
            # Filtro de ID de referência de parcela
            if "installment_reference_id" in filters:
                query["installmentInfo.reference_id"] = filters["installment_reference_id"]
                
            # Filtro de tags
            if "tags" in filters:
                tags = filters["tags"]
                if isinstance(tags, list):
                    if len(tags) == 1:
                        query["tags"] = tags[0]
                    else:
                        query["tags"] = {"$in": tags}
                else:
                    query["tags"] = tags
        
        # Ordena por data decrescente (mais recente primeiro)
        cursor = self.collection.find(query).sort("date", -1)
        
        # Converte documentos para entidades Transaction
        transactions = []
        async for document in cursor:
            transaction = TransactionModel.from_dict(document)
            if transaction:
                transactions.append(transaction)
        
        return transactions
    
    async def get_by_installment_reference(self, reference_id: str, future_only: bool = False) -> List[Transaction]:
        """
        Recupera transações que fazem parte de uma série de parcelas.
        
        Args:
            reference_id: ID de referência das parcelas
            future_only: Se True, retorna apenas parcelas com data futura
            
        Returns:
            Lista de transações da série de parcelas
        """
        query = {"installmentInfo.reference_id": reference_id}
        
        if future_only:
            query["date"] = {"$gte": datetime.now()}
            
        # Ordena por número da parcela
        cursor = self.collection.find(query).sort("installmentInfo.current", 1)
        
        # Converte documentos para entidades Transaction
        transactions = []
        async for document in cursor:
            transaction = TransactionModel.from_dict(document)
            if transaction:
                transactions.append(transaction)
                
        return transactions
    
    async def get_recurring_instances(self, 
                                     recurring_transaction_id: UUID,
                                     limit_date: Optional[datetime] = None) -> List[Transaction]:
        """
        Recupera instâncias de uma transação recorrente.
        
        Args:
            recurring_transaction_id: ID da transação recorrente
            limit_date: Data limite para busca de instâncias
            
        Returns:
            Lista de instâncias da transação recorrente
        """
        # Primeiro, recupera a transação recorrente original
        recurring_transaction = await self.get_by_id(recurring_transaction_id)
        
        if not recurring_transaction or not recurring_transaction.recurrence:
            return []
            
        # Busca instâncias que tenham a mesma descrição, categoria e valor
        query = {
            "description": recurring_transaction.description,
            "category": recurring_transaction.category,
            "amount": float(recurring_transaction.amount.amount),
            "type": recurring_transaction.type
        }
        
        if limit_date:
            query["date"] = {"$lte": limit_date}
            
        # Ordena por data crescente
        cursor = self.collection.find(query).sort("date", 1)
        
        # Converte documentos para entidades Transaction
        transactions = []
        async for document in cursor:
            transaction = TransactionModel.from_dict(document)
            if transaction:
                transactions.append(transaction)
                
        return transactions
    
    async def update(self, transaction_id: UUID, data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Atualiza uma transação.
        
        Args:
            transaction_id: ID da transação a ser atualizada
            data: Dados a serem atualizados
            
        Returns:
            A transação atualizada ou None se não encontrada
        """
        update_data = {}
        
        # Processa os dados de atualização
        if "amount" in data:
            if isinstance(data["amount"], Money):
                update_data["amount"] = float(data["amount"].amount)
            else:
                update_data["amount"] = float(Money(data["amount"]).amount)
        
        if "category" in data:
            update_data["category"] = data["category"]
        
        if "description" in data:
            update_data["description"] = data["description"]
        
        if "date" in data:
            update_data["date"] = data["date"]
            
        if "priority" in data:
            update_data["priority"] = data["priority"]
            
        if "tags" in data:
            update_data["tags"] = data["tags"]
            
        if "recurrence" in data:
            if data["recurrence"] is None:
                # Remove o campo de recorrência
                await self.collection.update_one(
                    {"_id": str(transaction_id)},
                    {"$unset": {"recurrence": ""}}
                )
            else:
                # Converte o objeto de recorrência para formato MongoDB
                update_data["recurrence"] = {
                    "type": data["recurrence"].type.value,
                    "startDate": data["recurrence"].start_date,
                    "endDate": data["recurrence"].end_date,
                    "dayOfMonth": data["recurrence"].day_of_month,
                    "dayOfWeek": data["recurrence"].day_of_week,
                    "occurrences": data["recurrence"].occurrences
                }
                
        if "installment_info" in data:
            if data["installment_info"] is None:
                # Remove o campo de parcelamento
                await self.collection.update_one(
                    {"_id": str(transaction_id)},
                    {"$unset": {"installmentInfo": ""}}
                )
            else:
                # Converte o dicionário de parcelamento para formato MongoDB
                update_data["installmentInfo"] = data["installment_info"]
        
        if not update_data:
            return None
        
        # Atualiza o documento no MongoDB
        result = await self.collection.update_one(
            {"_id": str(transaction_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        # Retorna a transação atualizada
        return await self.get_by_id(transaction_id)
    
    async def delete(self, transaction_id: UUID) -> bool:
        """
        Remove uma transação.
        
        Args:
            transaction_id: ID da transação a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        result = await self.collection.delete_one({"_id": str(transaction_id)})
        return result.deleted_count > 0
    
    async def get_balance(self, user_id: UUID, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calcula o balanço financeiro para um usuário em um período específico.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial opcional do período
            end_date: Data final opcional do período
            
        Returns:
            Dicionário contendo total de receitas, total de despesas e saldo
        """
        # Constrói a query para o aggregation pipeline
        match_stage = {"userId": str(user_id)}
        
        if start_date or end_date:
            match_stage["date"] = {}
            
            if start_date:
                match_stage["date"]["$gte"] = start_date
            
            if end_date:
                match_stage["date"]["$lte"] = end_date
        
        # Pipeline de agregação para calcular totais
        pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$type",
                "total": {"$sum": "$amount"}
            }}
        ]
        
        # Executa a agregação
        cursor = self.collection.aggregate(pipeline)
        
        # Processa os resultados
        total_income = 0.0
        total_expense = 0.0
        
        async for document in cursor:
            if document["_id"] == "income":
                total_income = document["total"]
            elif document["_id"] == "expense":
                total_expense = document["total"]
        
        # Calcula o saldo
        balance = total_income - total_expense
        
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": balance
        }