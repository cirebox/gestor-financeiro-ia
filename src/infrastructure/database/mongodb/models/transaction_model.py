# src/infrastructure/database/mongodb/models/transaction_model.py
from datetime import datetime
from typing import Dict, Any, Optional, List
from uuid import UUID

from src.domain.entities.transaction import Transaction
from src.domain.value_objects.money import Money
from src.domain.value_objects.recurrence import Recurrence, RecurrenceType


class TransactionModel:
    """Modelo de dados para transações no MongoDB."""
    
    @staticmethod
    def to_dict(transaction: Transaction) -> Dict[str, Any]:
        """
        Converte uma entidade Transaction para um dicionário para armazenamento no MongoDB.
        
        Args:
            transaction: Objeto Transaction a ser convertido
            
        Returns:
            Dicionário representando a transação
        """
        transaction_dict = {
            "_id": str(transaction.id),
            "userId": str(transaction.user_id),
            "type": transaction.type,
            "amount": float(transaction.amount.amount),
            "category": transaction.category,
            "description": transaction.description,
            "date": transaction.date,
            "createdAt": transaction.created_at,
            "isPaid": transaction.is_paid
        }
        
        # Adiciona campos opcionais se existirem
        if transaction.priority:
            transaction_dict["priority"] = transaction.priority
            
        if transaction.tags:
            transaction_dict["tags"] = transaction.tags
            
        if transaction.recurrence:
            transaction_dict["recurrence"] = {
                "type": transaction.recurrence.type.value,
                "startDate": transaction.recurrence.start_date,
                "endDate": transaction.recurrence.end_date,
                "dayOfMonth": transaction.recurrence.day_of_month,
                "dayOfWeek": transaction.recurrence.day_of_week,
                "occurrences": transaction.recurrence.occurrences
            }
            
        if transaction.installment_info:
            transaction_dict["installmentInfo"] = transaction.installment_info
            
        if transaction.due_date:
            transaction_dict["dueDate"] = transaction.due_date
            
        if transaction.paid_date:
            transaction_dict["paidDate"] = transaction.paid_date
            
        return transaction_dict
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Converte um dicionário do MongoDB para uma entidade Transaction.
        
        Args:
            data: Dicionário contendo dados da transação
            
        Returns:
            Objeto Transaction ou None se o dicionário for inválido
        """
        if not data:
            return None
        
        try:
            # Processa dados de recorrência se existirem
            recurrence = None
            if "recurrence" in data:
                recurrence_data = data["recurrence"]
                recurrence = Recurrence(
                    type=RecurrenceType(recurrence_data["type"]),
                    start_date=recurrence_data["startDate"],
                    end_date=recurrence_data.get("endDate"),
                    day_of_month=recurrence_data.get("dayOfMonth"),
                    day_of_week=recurrence_data.get("dayOfWeek"),
                    occurrences=recurrence_data.get("occurrences")
                )
                
            # Processa dados de parcelamento se existirem
            installment_info = data.get("installmentInfo")
            
            # Processa tags se existirem
            tags = data.get("tags", [])
            
            # Cria a entidade Transaction
            return Transaction(
                id=UUID(data["_id"]),
                user_id=UUID(data["userId"]),
                type=data["type"],
                amount=Money(data["amount"]),
                category=data["category"],
                description=data["description"],
                date=data["date"],
                created_at=data["createdAt"],
                priority=data.get("priority"),
                recurrence=recurrence,
                installment_info=installment_info,
                tags=tags,
                due_date=data.get("dueDate"),
                is_paid=data.get("isPaid", False),
                paid_date=data.get("paidDate")
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para Transaction: {e}")
            return None