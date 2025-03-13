# src/infrastructure/database/mongodb/models/transaction_model.py
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID

from src.domain.entities.transaction import Transaction
from src.domain.value_objects.money import Money


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
        return {
            "_id": str(transaction.id),
            "userId": str(transaction.user_id),
            "type": transaction.type,
            "amount": float(transaction.amount.amount),
            "category": transaction.category,
            "description": transaction.description,
            "date": transaction.date,
            "createdAt": transaction.created_at
        }
    
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
            return Transaction(
                id=UUID(data["_id"]),
                user_id=UUID(data["userId"]),
                type=data["type"],
                amount=Money(data["amount"]),
                category=data["category"],
                description=data["description"],
                date=data["date"],
                created_at=data["createdAt"]
            )
        except (KeyError, ValueError) as e:
            # Log do erro seria apropriado aqui
            print(f"Erro ao converter dicionário para Transaction: {e}")
            return None
