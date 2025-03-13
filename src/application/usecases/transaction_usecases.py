# src/application/usecases/transaction_usecases.py
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Tuple
from uuid import UUID, uuid4

from src.application.interfaces.repositories.transaction_repository_interface import TransactionRepositoryInterface
from src.application.interfaces.repositories.category_repository_interface import CategoryRepositoryInterface
from src.domain.entities.transaction import Transaction
from src.domain.exceptions.domain_exceptions import CategoryNotFoundException
from src.domain.value_objects.money import Money
from src.domain.value_objects.recurrence import Recurrence, RecurrenceType


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
                              date: Optional[datetime] = None,
                              priority: Optional[str] = None,
                              recurrence: Optional[Dict[str, Any]] = None,
                              installment_info: Optional[Dict[str, Any]] = None,
                              tags: Optional[List[str]] = None) -> Transaction:
        """
        Adiciona uma nova transação.
        
        Args:
            user_id: ID do usuário
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação
            category: Categoria da transação
            description: Descrição da transação
            date: Data da transação (opcional)
            priority: Prioridade da transação ('alta', 'média', 'baixa')
            recurrence: Informações de recorrência {'frequency': 'mensal', 'end_date': datetime, 'occurrences': int}
            installment_info: Informações de parcelamento {'total': int, 'current': int}
            tags: Lista de tags para classificação adicional
            
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
        
        # Processa informações de recorrência
        recurrence_obj = None
        if recurrence:
            frequency = recurrence.get('frequency', 'mensal')
            start_date = date or datetime.now()
            end_date = recurrence.get('end_date')
            occurrences = recurrence.get('occurrences')
            
            recurrence_obj = Recurrence.from_string(
                frequency=frequency,
                start_date=start_date,
                end_date=end_date,
                occurrences=occurrences
            )
        
        # Processa informações de parcelamento
        processed_installment_info = None
        if installment_info:
            total_installments = installment_info.get('total', 1)
            current_installment = installment_info.get('current', 1)
            
            if total_installments < 1:
                raise ValueError("O número total de parcelas deve ser pelo menos 1")
                
            if current_installment < 1 or current_installment > total_installments:
                raise ValueError(f"O número da parcela atual deve estar entre 1 e {total_installments}")
                
            # Gera um ID de referência para todas as parcelas
            installment_id = installment_info.get('reference_id') or str(uuid4())
            
            processed_installment_info = {
                'total': total_installments,
                'current': current_installment,
                'reference_id': installment_id
            }
            
        # Cria a transação
        transaction = Transaction.create(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=date,
            priority=priority,
            recurrence=recurrence_obj,
            installment_info=processed_installment_info,
            tags=tags
        )
        
        # Adiciona a transação ao repositório
        added_transaction = await self.transaction_repository.add(transaction)
        
        # Se for a primeira parcela e tiver mais de uma parcela, cria as demais parcelas
        if processed_installment_info and processed_installment_info['current'] == 1 and processed_installment_info['total'] > 1:
            await self._create_remaining_installments(
                user_id=user_id,
                original_transaction=added_transaction,
                installment_info=processed_installment_info
            )
            
        return added_transaction
    
    async def _create_remaining_installments(self, 
                                           user_id: UUID, 
                                           original_transaction: Transaction,
                                           installment_info: Dict[str, Any]) -> None:
        """
        Cria as parcelas restantes de uma transação parcelada.
        
        Args:
            user_id: ID do usuário
            original_transaction: Transação original (primeira parcela)
            installment_info: Informações de parcelamento
        """
        total_installments = installment_info['total']
        reference_id = installment_info['reference_id']
        
        # Calcula intervalo de datas (assume mensal)
        base_date = original_transaction.date
        
        # Para cada parcela restante
        for i in range(1, total_installments):
            # Calcula a data da parcela (incrementa o mês)
            installment_date = datetime(
                year=base_date.year + ((base_date.month + i - 1) // 12),
                month=((base_date.month + i - 1) % 12) + 1,
                day=min(base_date.day, self._get_last_day_of_month(
                    base_date.year + ((base_date.month + i - 1) // 12),
                    ((base_date.month + i - 1) % 12) + 1
                )),
                hour=base_date.hour,
                minute=base_date.minute,
                second=base_date.second
            )
            
            # Cria a parcela
            installment = Transaction.create(
                user_id=user_id,
                type=original_transaction.type,
                amount=original_transaction.amount,
                category=original_transaction.category,
                description=f"{original_transaction.description} ({i+1}/{total_installments})",
                date=installment_date,
                priority=original_transaction.priority,
                recurrence=None,
                installment_info={
                    'total': total_installments,
                    'current': i + 1,
                    'reference_id': reference_id
                },
                tags=original_transaction.tags
            )
            
            # Adiciona a parcela ao repositório
            await self.transaction_repository.add(installment)
    
    def _get_last_day_of_month(self, year: int, month: int) -> int:
        """
        Retorna o último dia do mês especificado.
        """
        if month == 12:
            next_month = datetime(year + 1, 1, 1)
        else:
            next_month = datetime(year, month + 1, 1)
            
        last_day = (next_month - datetime.timedelta(days=1)).day
        return last_day
    
    async def add_recurring_transaction(self,
                                      user_id: UUID,
                                      type: str,
                                      amount: Union[Money, float, str],
                                      category: str,
                                      description: str,
                                      frequency: str,
                                      start_date: Optional[datetime] = None,
                                      end_date: Optional[datetime] = None,
                                      occurrences: Optional[int] = None,
                                      priority: Optional[str] = None,
                                      tags: Optional[List[str]] = None) -> Transaction:
        """
        Adiciona uma transação recorrente.
        
        Args:
            user_id: ID do usuário
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação
            category: Categoria da transação
            description: Descrição da transação
            frequency: Frequência da recorrência ('diária', 'semanal', 'mensal', etc.)
            start_date: Data inicial (opcional)
            end_date: Data final (opcional)
            occurrences: Número de ocorrências (opcional)
            priority: Prioridade da transação ('alta', 'média', 'baixa')
            tags: Lista de tags para classificação adicional
            
        Returns:
            A transação recorrente criada
        """
        # Cria o objeto de recorrência
        if start_date is None:
            start_date = datetime.now()
            
        recurrence_obj = Recurrence.from_string(
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            occurrences=occurrences
        )
        
        # Cria a transação recorrente
        return await self.add_transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=description,
            date=start_date,
            priority=priority,
            recurrence={
                'frequency': frequency,
                'end_date': end_date,
                'occurrences': occurrences
            },
            tags=tags
        )
    
    async def add_installment_transaction(self,
                                        user_id: UUID,
                                        type: str,
                                        amount: Union[Money, float, str],
                                        category: str,
                                        description: str,
                                        total_installments: int,
                                        start_date: Optional[datetime] = None,
                                        priority: Optional[str] = None,
                                        tags: Optional[List[str]] = None) -> Transaction:
        """
        Adiciona uma transação parcelada.
        
        Args:
            user_id: ID do usuário
            type: Tipo da transação ('income' ou 'expense')
            amount: Valor da transação
            category: Categoria da transação
            description: Descrição da transação
            total_installments: Número total de parcelas
            start_date: Data da primeira parcela (opcional)
            priority: Prioridade da transação ('alta', 'média', 'baixa')
            tags: Lista de tags para classificação adicional
            
        Returns:
            A primeira parcela da transação parcelada
        """
        if total_installments < 1:
            raise ValueError("O número total de parcelas deve ser pelo menos 1")
            
        # Determina o valor total e o valor de cada parcela
        if isinstance(amount, (float, int, str)):
            amount = Money(amount)
            
        # Cria a primeira parcela
        return await self.add_transaction(
            user_id=user_id,
            type=type,
            amount=amount,
            category=category,
            description=f"{description} (1/{total_installments})",
            date=start_date,
            priority=priority,
            installment_info={
                'total': total_installments,
                'current': 1
            },
            tags=tags
        )
    
    async def get_transactions(self, 
                             user_id: UUID, 
                             filters: Optional[Dict[str, Any]] = None) -> List[Transaction]:
        """
        Recupera as transações de um usuário, opcionalmente filtradas.
        
        Args:
            user_id: ID do usuário
            filters: Filtros opcionais como data, categoria, tipo, recorrência, etc.
            
        Returns:
            Lista de transações que correspondem aos critérios
        """
        # Adiciona suporte para novos filtros
        enhanced_filters = filters.copy() if filters else {}
        
        # Permite filtrar por prioridade
        if filters and 'priority' in filters:
            enhanced_filters['priority'] = filters['priority']
            
        # Permite filtrar transações recorrentes
        if filters and 'is_recurring' in filters:
            enhanced_filters['has_recurrence'] = filters['is_recurring']
            
        # Permite filtrar transações parceladas
        if filters and 'is_installment' in filters:
            enhanced_filters['has_installment_info'] = filters['is_installment']
            
        # Permite filtrar por tags
        if filters and 'tags' in filters:
            enhanced_filters['tags'] = filters['tags']
            
        return await self.transaction_repository.get_by_user(user_id, enhanced_filters)
    
    async def get_recurring_transactions(self, user_id: UUID) -> List[Transaction]:
        """
        Recupera todas as transações recorrentes de um usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            Lista de transações recorrentes
        """
        return await self.get_transactions(user_id, {'is_recurring': True})
    
    async def get_installment_transactions(self, 
                                         user_id: UUID, 
                                         reference_id: Optional[str] = None) -> List[Transaction]:
        """
        Recupera transações parceladas de um usuário.
        
        Args:
            user_id: ID do usuário
            reference_id: ID de referência da parcela (opcional)
            
        Returns:
            Lista de transações parceladas
        """
        filters = {'is_installment': True}
        if reference_id:
            filters['installment_reference_id'] = reference_id
            
        return await self.get_transactions(user_id, filters)
    
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
        
        # Processa atualizações de recorrência, se houver
        if 'recurrence' in data:
            recurrence_data = data['recurrence']
            if recurrence_data is None:
                # Remove a recorrência
                data['recurrence'] = None
            else:
                frequency = recurrence_data.get('frequency', 'mensal')
                start_date = recurrence_data.get('start_date', transaction.date)
                end_date = recurrence_data.get('end_date')
                occurrences = recurrence_data.get('occurrences')
                
                recurrence_obj = Recurrence.from_string(
                    frequency=frequency,
                    start_date=start_date,
                    end_date=end_date,
                    occurrences=occurrences
                )
                
                data['recurrence'] = recurrence_obj
        
        # Atualiza a transação
        return await self.transaction_repository.update(transaction_id, data)
    
    async def update_installment_series(self,
                                      reference_id: str, 
                                      data: Dict[str, Any],
                                      update_future_only: bool = True) -> int:
        """
        Atualiza uma série de parcelas.
        
        Args:
            reference_id: ID de referência das parcelas
            data: Dados a serem atualizados
            update_future_only: Se True, atualiza apenas parcelas futuras
            
        Returns:
            Número de parcelas atualizadas
        """
        # Busca todas as parcelas com o ID de referência
        filters = {'installment_reference_id': reference_id}
        
        if update_future_only:
            # Se for para atualizar apenas parcelas futuras, adiciona filtro de data
            filters['date_after'] = datetime.now()
            
        # Recupera as parcelas
        transactions = await self.transaction_repository.get_by_installment_reference(reference_id, update_future_only)
        
        # Contador de atualizações bem-sucedidas
        update_count = 0
        
        # Atualiza cada parcela
        for transaction in transactions:
            updated = await self.update_transaction(transaction.id, data)
            if updated:
                update_count += 1
                
        return update_count
    
    async def generate_recurring_transaction_instances(self, 
                                                     user_id: UUID, 
                                                     months_ahead: int = 3) -> int:
        """
        Gera instâncias futuras de transações recorrentes.
        
        Args:
            user_id: ID do usuário
            months_ahead: Número de meses à frente para gerar instâncias
            
        Returns:
            Número de instâncias geradas
        """
        # Recupera todas as transações recorrentes do usuário
        recurring_transactions = await self.get_recurring_transactions(user_id)
        
        # Calcula a data limite (hoje + meses_ahead)
        now = datetime.now()
        limit_date = datetime(
            year=now.year + ((now.month + months_ahead - 1) // 12),
            month=((now.month + months_ahead - 1) % 12) + 1,
            day=1
        )
        
        # Contador de instâncias geradas
        instance_count = 0
        
        # Para cada transação recorrente
        for transaction in recurring_transactions:
            if not transaction.recurrence:
                continue
                
            # Verifica se já temos instâncias suficientes
            existing_instances = await self.transaction_repository.get_recurring_instances(
                recurring_transaction_id=transaction.id,
                limit_date=limit_date
            )
            
            # Calcula a última data das instâncias existentes
            last_date = max([instance.date for instance in existing_instances]) if existing_instances else transaction.date
            
            # Gera novas instâncias até a data limite
            while True:
                # Calcula a próxima data
                next_date = transaction.recurrence.get_next_occurrence(last_date)
                
                # Se não houver próxima data ou estiver além do limite, para
                if not next_date or next_date > limit_date:
                    break
                    
                # Cria uma nova instância
                instance = Transaction.create(
                    user_id=user_id,
                    type=transaction.type,
                    amount=transaction.amount,
                    category=transaction.category,
                    description=transaction.description,
                    date=next_date,
                    priority=transaction.priority,
                    tags=transaction.tags,
                    # Não herda recorrência ou parcelas
                )
                
                # Adiciona a instância ao repositório
                await self.transaction_repository.add(instance)
                instance_count += 1
                
                # Atualiza a última data
                last_date = next_date
                
        return instance_count
    
    async def delete_transaction(self, transaction_id: UUID) -> bool:
        """
        Remove uma transação.
        
        Args:
            transaction_id: ID da transação a ser removida
            
        Returns:
            True se removida com sucesso, False caso contrário
        """
        return await self.transaction_repository.delete(transaction_id)
    
    async def delete_installment_series(self, 
                                      reference_id: str, 
                                      delete_future_only: bool = True) -> int:
        """
        Remove uma série de parcelas.
        
        Args:
            reference_id: ID de referência das parcelas
            delete_future_only: Se True, remove apenas parcelas futuras
            
        Returns:
            Número de parcelas removidas
        """
        # Recupera as parcelas
        transactions = await self.transaction_repository.get_by_installment_reference(reference_id, delete_future_only)
        
        # Contador de remoções bem-sucedidas
        delete_count = 0
        
        # Remove cada parcela
        for transaction in transactions:
            deleted = await self.delete_transaction(transaction.id)
            if deleted:
                delete_count += 1
                
        return delete_count
    
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
    
    async def get_transactions_by_priority(self,
                                         user_id: UUID,
                                         priority: str,
                                         start_date: Optional[datetime] = None,
                                         end_date: Optional[datetime] = None) -> List[Transaction]:
        """
        Recupera transações por prioridade.
        
        Args:
            user_id: ID do usuário
            priority: Prioridade ('alta', 'média', 'baixa')
            start_date: Data inicial opcional do período
            end_date: Data final opcional do período
            
        Returns:
            Lista de transações com a prioridade especificada
        """
        filters = {'priority': priority}
        
        if start_date:
            filters['start_date'] = start_date
            
        if end_date:
            filters['end_date'] = end_date
            
        return await self.get_transactions(user_id, filters)
    
    async def get_transactions_by_tags(self,
                                     user_id: UUID,
                                     tags: List[str],
                                     start_date: Optional[datetime] = None,
                                     end_date: Optional[datetime] = None) -> List[Transaction]:
        """
        Recupera transações que possuem determinadas tags.
        
        Args:
            user_id: ID do usuário
            tags: Lista de tags para filtrar
            start_date: Data inicial opcional do período
            end_date: Data final opcional do período
            
        Returns:
            Lista de transações com as tags especificadas
        """
        filters = {'tags': tags}
        
        if start_date:
            filters['start_date'] = start_date
            
        if end_date:
            filters['end_date'] = end_date
            
        return await self.get_transactions(user_id, filters)