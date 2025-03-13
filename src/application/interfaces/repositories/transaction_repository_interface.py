# src/application/interfaces/repositories/transaction_repository_interface.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from src.domain.entities.transaction import Transaction


class TransactionRepositoryInterface(ABC):
    """Interface para repositório de transações."""
    
    @abstractmethod
    async def add(self, transaction: Transaction) -> Transaction:
        """
        Adiciona uma nova transação.
        
        Args:
            transaction: A transação a ser adicionada
            
        Returns:
            A transação adicionada com ID atualizado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Recupera uma transação pelo ID.
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            A transação encontrada ou None
        """
        pass
    
    @abstractmethod
    async def get_by_user(self, user_id: UUID, filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        Recupera as transações de um usuário, opcionalmente filtradas.
        
        Args:
            user_id: ID do usuário
            filters: Filtros opcionais como data, categoria, tipo, etc.
            
        Returns:
            Lista de transações que correspondem aos critérios
        """
        pass
    
    @abstractmethod
    async def get_by_installment_reference(self, reference_id: str, future_only: bool = False) -> List[Transaction]:
        """
        Recupera transações que fazem parte de uma série de parcelas.
        
        Args:
            reference_id: ID de referência das parcelas
            future_only: Se True, retorna apenas parcelas com data futura
            
        Returns:
            Lista de transações da série de parcelas
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def update(self, transaction_id: UUID, data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Atualiza uma transação.
        
        Args:
            transaction_id: ID da transação a ser atualizada
            data: Dados a serem atualizados
            
        Returns:
            A transação atualizada ou None se não encontrada
        """
        pass
    
    @abstractmethod
    async def delete(self, transaction_id: UUID) -> bool:
        """
        Remove uma transação.
        
        Args:
            transaction_id: ID da transação a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        pass
    
    @abstractmethod
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
        pass