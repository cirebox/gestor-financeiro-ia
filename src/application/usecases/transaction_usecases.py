# src/application/usecases/transaction_usecases.py
from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from uuid import UUID

from src.application.interfaces.repositories.transaction_repository_interface import TransactionRepositoryInterface
from src.application.interfaces.repositories.category_repository_interface import CategoryRepositoryInterface
from src.domain.entities.transaction import Transaction
from src.domain.exceptions.domain_exceptions import CategoryNotFoundException
from src.domain.value_objects.money import Money


class TransactionUseCases:
    """Casos de uso relacionados a transações financeiras."""
    
    def __init__(self, 
                 transaction_repository: TransactionRepositoryInterface,
                 category_repository: CategoryRepositoryInterface):
        """
        Inicializa os casos de uso de transação.
        
        Args:
            transaction_repository: Implementação do repositório de transações
            category_repository: Implementação do repositório de categorias
        """
        self.transaction_repository = transaction_repository
        self.category_repository = category_repository
    
    async def add_transaction(self, 
                            user_id: UUID, 
                            type: str, 
                            amount: Union[Money, float, str], 
                            category: str, 
                            description: str, 
                            date: Optional[datetime] = None) -> Transaction:
        """
        Adiciona uma nova transação.
        
        Args:
            user_id: ID do usuário
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação
            category: Categoria da transação
            description: Descrição da transação
            date: Data da transação (opcional)
            
        Returns:
            A transação criada
            
        Raises:
            CategoryNotFoundException: Se a categoria não existir
            ValueError: Se os dados forem inválidos
        """
        # Verifica se a categoria existe
        if not await self.category_repository.get_by_name(category):
            # Se a categoria não existe, tenta encontrar uma categoria do mesmo tipo
            categories = await self.category_repository.get_all(type=type)
            if not categories:
                raise CategoryNotFoundException(f"Categoria '{category}' não encontrada e não há categorias do tipo '{type}'")
            
            # Usa a primeira categoria encontrada
            category = categories[0].name
        
        # Cria a transação
        transaction = Transaction.create(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=date
        )
        
        # Adiciona a transação ao repositório
        return await self.transaction_repository.add(transaction)
    
    async def get_transactions(self, 
                             user_id: UUID, 
                             filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        Recupera as transações de um usuário, opcionalmente filtradas.
        
        Args:
            user_id: ID do usuário
            filters: Filtros opcionais como data, categoria, tipo etc.
            
        Returns:
            Lista de transações que correspondem aos critérios
        """
        return await self.transaction_repository.get_by_user(user_id, filters)
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """
        Recupera uma transação pelo ID.
        
        Args:
            transaction_id: ID da transação
            
        Returns:
            A transação encontrada ou None
        """
        return await self.transaction_repository.get_by_id(transaction_id)
    
    async def update_transaction(self, 
                              transaction_id: UUID, 
                              data: Dict[str, Any]) -> Optional[Transaction]:
        """
        Atualiza uma transação.
        
        Args:
            transaction_id: ID da transação a ser atualizada
            data: Dados a serem atualizados
            
        Returns:
            A transação atualizada ou None se não encontrada
        """
        # Verifica se a transação existe
        transaction = await self.transaction_repository.get_by_id(transaction_id)
        if not transaction:
            return None
        
        # Se estiver atualizando a categoria, verifica se ela existe
        if 'category' in data:
            category = await self.category_repository.get_by_name(data['category'])
            if not category:
                # Se a categoria não existe, tenta encontrar uma categoria do mesmo tipo
                categories = await self.category_repository.get_all(type=transaction.type)
                if not categories:
                    raise CategoryNotFoundException(f"Categoria '{data['category']}' não encontrada e não há categorias do tipo '{transaction.type}'")
                
                # Usa a primeira categoria encontrada
                data['category'] = categories[0].name
        
        # Atualiza a transação
        return await self.transaction_repository.update(transaction_id, data)
    
    async def delete_transaction(self, transaction_id: UUID) -> bool:
        """
        Remove uma transação.
        
        Args:
            transaction_id: ID da transação a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        return await self.transaction_repository.delete(transaction_id)
    
    async def get_balance(self, 
                        user_id: UUID, 
                        start_date: Optional[datetime] = None, 
                        end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calcula o balanço financeiro para um usuário em um período específico.
        
        Args:
            user_id: ID do usuário
            start_date: Data inicial opcional do período
            end_date: Data final opcional do período
            
        Returns:
            Dicionário contendo total de receitas, total de despesas e saldo
        """
        return await self.transaction_repository.get_balance(user_id, start_date, end_date)