# src/application/usecases/nlp_usecases.py
import re
from typing import Dict, Any, Optional
from uuid import UUID

from src.application.interfaces.services.nlp_service_interface import NLPServiceInterface
from src.application.usecases.transaction_usecases import TransactionUseCases
from src.application.usecases.category_usecases import CategoryUseCases
from src.application.usecases.analytics_usecases import AnalyticsUseCases


class NLPUseCases:
    """Casos de uso relacionados ao processamento de linguagem natural."""
    
    def __init__(self, 
                 nlp_service: NLPServiceInterface,
                 transaction_usecases: TransactionUseCases,
                 category_usecases: CategoryUseCases,
                 analytics_usecases: Optional[AnalyticsUseCases] = None):
        """
        Inicializa os casos de uso de NLP.
        
        Args:
            nlp_service: Serviço de processamento de linguagem natural
            transaction_usecases: Casos de uso de transações
            category_usecases: Casos de uso de categorias
            analytics_usecases: Casos de uso de análises (opcional)
        """
        self.nlp_service = nlp_service
        self.transaction_usecases = transaction_usecases
        self.category_usecases = category_usecases
        self.analytics_usecases = analytics_usecases
    
    async def process_command(self, user_id: UUID, command: str) -> Dict[str, Any]:
        """
        Processa um comando em linguagem natural.
        
        Args:
            user_id: ID do usuário
            command: Comando em linguagem natural
            
        Returns:
            Resultado do processamento
        """
        # Identifica a intenção e extrai entidades do comando
        intent, entities = await self.nlp_service.analyze(command)
        
        # Processa a intenção
        if intent == "ADD_EXPENSE":
            return await self._handle_add_expense(user_id, entities)
        elif intent == "ADD_INCOME":
            return await self._handle_add_income(user_id, entities)
        elif intent == "ADD_RECURRING":
            return await self._handle_add_recurring(user_id, entities)
        elif intent == "ADD_INSTALLMENT":
            return await self._handle_add_installment(user_id, entities)
        elif intent == "LIST_TRANSACTIONS":
            return await self._handle_list_transactions(user_id, entities)
        elif intent == "LIST_RECURRING":
            return await self._handle_list_recurring(user_id, entities)
        elif intent == "LIST_INSTALLMENTS":
            return await self._handle_list_installments(user_id, entities)
        elif intent == "GET_BALANCE":
            return await self._handle_get_balance(user_id, entities)
        elif intent == "DELETE_TRANSACTION":
            return await self._handle_delete_transaction(user_id, entities)
        elif intent == "UPDATE_TRANSACTION":
            return await self._handle_update_transaction(user_id, entities)
        elif intent == "ADD_CATEGORY":
            return await self._handle_add_category(entities)
        elif intent == "LIST_CATEGORIES":
            return await self._handle_list_categories(entities)
        elif intent == "HELP":
            return self._get_help_message()
        else:
            return {"status": "error", "message": "Comando não reconhecido. Digite 'ajuda' para ver os comandos disponíveis."}
    
    async def _handle_add_expense(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de adicionar uma despesa."""
        # Verifica se todas as informações necessárias estão presentes
        missing_info = []
        
        if "amount" not in entities:
            missing_info.append("valor")
        
        if "category" not in entities:
            missing_info.append("categoria")
        
        if "description" not in entities and not entities.get("inference_description", False):
            missing_info.append("descrição")
        
        # Se faltar informações, solicita complementação
        if missing_info:
            missing_str = ", ".join(missing_info)
            
            # Sugestões de categorias para facilitar
            suggested_categories = []
            categories = await self.category_usecases.get_categories(type="expense")
            if categories:
                suggested_categories = [cat.name for cat in categories[:5]]
            
            return {
                "status": "confirmation_needed",
                "message": f"Por favor, informe {missing_str} para registrar a despesa.",
                "data": {
                    "partial_entities": {
                        **entities,
                        "suggested_categories": suggested_categories
                    },
                    "missing_fields": missing_info
                }
            }
        
        # Se tem descrição inferida mas não explícita, utiliza a inferida
        if "inference_description" in entities and "description" not in entities:
            entities["description"] = entities["inference_description"]
        
        # Verifica se tem informações sobre vencimento e pagamento
        due_date = entities.get("due_date")
        is_paid = entities.get("is_paid", False)
        paid_date = entities.get("paid_date")
        
        try:
            transaction = await self.transaction_usecases.add_transaction(
                user_id=user_id,
                type="expense",
                amount=entities.get("amount", 0),
                category=entities.get("category", "Outros"),
                description=entities.get("description", "Despesa sem descrição"),
                date=entities.get("date"),
                priority=entities.get("priority"),
                tags=entities.get("tags"),
                due_date=due_date,
                is_paid=is_paid,
                paid_date=paid_date
            )
            
            # Mensagem específica dependendo se está paga ou não
            message = ""
            if is_paid:
                message = f"Despesa de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada como quitada!"
            else:
                if due_date:
                    message = f"Despesa de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada com vencimento em {due_date.strftime('%d/%m/%Y')}!"
                else:
                    message = f"Despesa de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada!"
            
            return {
                "status": "success",
                "message": message,
                "data": {"transaction_id": str(transaction.id)}
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_add_income(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de adicionar uma receita."""
        try:
            transaction = await self.transaction_usecases.add_transaction(
                user_id=user_id,
                type="income",
                amount=entities.get("amount", 0),
                category=entities.get("category", "Outros"),
                description=entities.get("description", "Receita sem descrição"),
                date=entities.get("date"),
                priority=entities.get("priority"),
                tags=entities.get("tags")
            )
            return {
                "status": "success",
                "message": f"Receita de R$ {transaction.amount.amount:.2f} como {transaction.category} registrada com sucesso!",
                "data": {"transaction_id": str(transaction.id)}
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_add_recurring(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de adicionar uma transação recorrente."""
        try:
            # Determina o tipo (despesa ou receita)
            type_val = "expense"  # Tipo padrão
            if "type" in entities:
                type_val = entities["type"]
            
            # Extrai informações de recorrência
            recurrence = entities.get("recurrence", {
                "frequency": "mensal",
                "end_date": None,
                "occurrences": None
            })
            
            transaction = await self.transaction_usecases.add_recurring_transaction(
                user_id=user_id,
                type=type_val,
                amount=entities.get("amount", 0),
                category=entities.get("category", "Outros"),
                description=entities.get("description", f"{type_val.title()} recorrente"),
                frequency=recurrence.get("frequency", "mensal"),
                start_date=entities.get("date"),
                end_date=recurrence.get("end_date"),
                occurrences=recurrence.get("occurrences"),
                priority=entities.get("priority"),
                tags=entities.get("tags")
            )
            
            type_desc = "Despesa" if type_val == "expense" else "Receita"
            frequency_desc = recurrence.get("frequency", "mensal")
            
            return {
                "status": "success",
                "message": f"{type_desc} recorrente {frequency_desc} de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada com sucesso!",
                "data": {"transaction_id": str(transaction.id)}
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_add_installment(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de adicionar uma transação parcelada."""
        try:
            # Extrai informações de parcelamento
            installment_info = entities.get("installment_info", {
                "total": 2,
                "current": 1
            })
            
            total_installments = installment_info.get("total", 2)
            
            transaction = await self.transaction_usecases.add_installment_transaction(
                user_id=user_id,
                type="expense",  # Parcelamentos são sempre despesas
                amount=entities.get("amount", 0),
                category=entities.get("category", "Outros"),
                description=entities.get("description", "Despesa parcelada"),
                total_installments=total_installments,
                start_date=entities.get("date"),
                priority=entities.get("priority"),
                tags=entities.get("tags")
            )
            
            return {
                "status": "success",
                "message": f"Despesa parcelada em {total_installments}x de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada com sucesso!",
                "data": {"transaction_id": str(transaction.id)}
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_list_transactions(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de listar transações."""
        try:
            filters = {}
            
            # Aplica filtros de data se fornecidos
            if "start_date" in entities and "end_date" in entities:
                filters["start_date"] = entities["start_date"]
                filters["end_date"] = entities["end_date"]
            elif "month" in entities:
                # Configurar filtros para mês específico
                filters["month"] = entities["month"]
            
            # Filtro de tipo (receita/despesa)
            if "type" in entities:
                filters["type"] = entities["type"]
            
            # Filtro de categoria
            if "category" in entities:
                filters["category"] = entities["category"]
                
            # Filtro de prioridade
            if "priority" in entities:
                filters["priority"] = entities["priority"]
                
            # Filtro de tags
            if "tags" in entities:
                filters["tags"] = entities["tags"]
            
            transactions = await self.transaction_usecases.get_transactions(user_id, filters)
            
            if not transactions:
                return {"status": "info", "message": "Nenhuma transação encontrada para os filtros informados."}
            
            # Formata a saída
            result = f"Encontradas {len(transactions)} transações:\n\n"
            
            for i, tx in enumerate(transactions):
                result += f"{i + 1}. {'Receita' if tx.type == 'income' else 'Despesa'}: R$ {tx.amount.amount:.2f}\n"
                result += f"   Categoria: {tx.category}\n"
                result += f"   Descrição: {tx.description}\n"
                result += f"   Data: {tx.date.strftime('%d/%m/%Y')}\n"
                
                if tx.priority:
                    result += f"   Prioridade: {tx.priority}\n"
                    
                if tx.is_recurring():
                    result += f"   Recorrência: {tx.recurrence.type.value}\n"
                    
                if tx.is_installment():
                    result += f"   Parcela: {tx.installment_info['current']}/{tx.installment_info['total']}\n"
                    
                if tx.tags:
                    result += f"   Tags: {', '.join(tx.tags)}\n"
                    
                result += f"   ID: {tx.id}\n\n"
            
            return {"status": "success", "message": result, "data": {"count": len(transactions)}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_list_recurring(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de listar transações recorrentes."""
        try:
            filters = {"is_recurring": True}
            
            # Aplica filtros adicionais
            if "type" in entities:
                filters["type"] = entities["type"]
            
            if "category" in entities:
                filters["category"] = entities["category"]
                
            if "priority" in entities:
                filters["priority"] = entities["priority"]
                
            if "tags" in entities:
                filters["tags"] = entities["tags"]
            
            transactions = await self.transaction_usecases.get_transactions(user_id, filters)
            
            if not transactions:
                return {"status": "info", "message": "Nenhuma transação recorrente encontrada."}
            
            # Formata a saída
            result = f"Encontradas {len(transactions)} transações recorrentes:\n\n"
            
            for i, tx in enumerate(transactions):
                result += f"{i + 1}. {'Receita' if tx.type == 'income' else 'Despesa'} recorrente: R$ {tx.amount.amount:.2f}\n"
                result += f"   Categoria: {tx.category}\n"
                result += f"   Descrição: {tx.description}\n"
                result += f"   Frequência: {tx.recurrence.type.value}\n"
                result += f"   Próximo vencimento: {tx.date.strftime('%d/%m/%Y')}\n"
                
                if tx.priority:
                    result += f"   Prioridade: {tx.priority}\n"
                    
                if tx.tags:
                    result += f"   Tags: {', '.join(tx.tags)}\n"
                    
                result += f"   ID: {tx.id}\n\n"
            
            return {"status": "success", "message": result, "data": {"count": len(transactions)}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_list_installments(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de listar transações parceladas."""
        try:
            filters = {"is_installment": True}
            
            # Aplica filtros adicionais
            if "category" in entities:
                filters["category"] = entities["category"]
                
            if "priority" in entities:
                filters["priority"] = entities["priority"]
                
            if "tags" in entities:
                filters["tags"] = entities["tags"]
                
            if "installment_reference_id" in entities:
                filters["installment_reference_id"] = entities["installment_reference_id"]
            
            transactions = await self.transaction_usecases.get_transactions(user_id, filters)
            
            if not transactions:
                return {"status": "info", "message": "Nenhuma transação parcelada encontrada."}
            
            # Agrupa as transações por ID de referência de parcela
            grouped_transactions = {}
            for tx in transactions:
                if tx.installment_info and "reference_id" in tx.installment_info:
                    ref_id = tx.installment_info["reference_id"]
                    if ref_id not in grouped_transactions:
                        grouped_transactions[ref_id] = []
                    grouped_transactions[ref_id].append(tx)
                else:
                    # Caso não tenha ID de referência, usa o próprio ID da transação
                    if str(tx.id) not in grouped_transactions:
                        grouped_transactions[str(tx.id)] = []
                    grouped_transactions[str(tx.id)].append(tx)
            
            # Formata a saída
            result = f"Encontradas {len(grouped_transactions)} compras parceladas:\n\n"
            
            for i, (ref_id, txs) in enumerate(grouped_transactions.items()):
                # Ordena parcelas por número
                txs.sort(key=lambda x: x.installment_info.get("current", 1))
                
                # Pega a primeira transação para informações comuns
                first_tx = txs[0]
                
                total_installments = first_tx.installment_info.get("total", len(txs))
                
                result += f"{i + 1}. Compra parcelada: R$ {first_tx.amount.amount * total_installments:.2f} em {total_installments}x\n"
                result += f"   Categoria: {first_tx.category}\n"
                result += f"   Descrição: {first_tx.description.split(' (')[0]}\n"  # Remove o sufixo (1/N)
                result += f"   Valor da parcela: R$ {first_tx.amount.amount:.2f}\n"
                result += f"   Parcelas: {', '.join([f'''{tx.installment_info.get('current', 1)}/{total_installments} ({tx.date.strftime('%d/%m/%Y')})''' for tx in txs])}\n"
                
                if first_tx.priority:
                    result += f"   Prioridade: {first_tx.priority}\n"
                    
                if first_tx.tags:
                    result += f"   Tags: {', '.join(first_tx.tags)}\n"
                    
                result += f"   ID: {ref_id}\n\n"
            
            return {"status": "success", "message": result, "data": {"count": len(grouped_transactions)}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_get_balance(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de verificar o saldo."""
        try:
            start_date = entities.get("start_date")
            end_date = entities.get("end_date")
            
            # Se um mês específico foi mencionado, configura datas
            if "month" in entities:
                # Lógica para converter mês para datas de início e fim
                # Implementação depende do formato da entidade "month"
                month_date = entities["month"]
                start_date = month_date
                
                # Calcula o último dia do mês
                year = month_date.year
                month = month_date.month
                
                if month == 12:
                    next_month = 1
                    next_year = year + 1
                else:
                    next_month = month + 1
                    next_year = year
                
                from datetime import timedelta
                end_date = datetime(next_year, next_month, 1) - timedelta(days=1)
                end_date = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            
            balance = await self.transaction_usecases.get_balance(user_id, start_date, end_date)
            
            period_desc = ""
            if start_date and end_date:
                period_desc = f" ({start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')})"
            elif "month" in entities:
                period_desc = f" ({entities['month'].strftime('%B %Y')})"
            
            result = f"Balanço financeiro{period_desc}:\n\n"
            result += f"Total de Receitas: R$ {balance['total_income']:.2f}\n"
            result += f"Total de Despesas: R$ {balance['total_expense']:.2f}\n"
            
            balance_value = balance['balance']
            result += f"Saldo: R$ {balance_value:.2f} {'✅' if balance_value >= 0 else '❌'}\n"
            
            return {"status": "success", "message": result, "data": balance}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_delete_transaction(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de excluir uma transação."""
        try:
            if "transaction_id" not in entities:
                return {
                    "status": "error", 
                    "message": "Por favor, informe o ID da transação que deseja excluir. Você pode ver os IDs usando o comando 'listar transações'."
                }
            
            transaction_id = UUID(entities["transaction_id"])
            
            # Verifica se a transação existe e pertence ao usuário
            transaction = await self.transaction_usecases.get_transaction(transaction_id)
            if not transaction or transaction.user_id != user_id:
                return {"status": "error", "message": f"Transação com ID {transaction_id} não encontrada."}
            
            # Verifica se é uma transação recorrente ou parcelada
            is_recurring = transaction.is_recurring()
            is_installment = transaction.is_installment()
            
            if (is_recurring or is_installment) and "delete_all" in entities and entities["delete_all"]:
                # Para recorrências, não há um método específico de exclusão em série
                if is_recurring:
                    deleted = await self.transaction_usecases.delete_transaction(transaction_id)
                    return {"status": "success", "message": f"Transação recorrente com ID {transaction_id} excluída com sucesso!"}
                    
                # Para parcelamentos, exclui toda a série
                elif is_installment and "reference_id" in transaction.installment_info:
                    ref_id = transaction.installment_info["reference_id"]
                    deleted_count = await self.transaction_usecases.delete_installment_series(
                        reference_id=ref_id, 
                        delete_future_only=entities.get("future_only", True)
                    )
                    
                    future_only = entities.get("future_only", True)
                    message = f"Todas as parcelas{' futuras' if future_only else ''} da compra foram excluídas com sucesso! Total: {deleted_count} parcelas."
                    
                    return {"status": "success", "message": message}
            else:
                # Exclusão normal de transação única
                deleted = await self.transaction_usecases.delete_transaction(transaction_id)
                
                if deleted:
                    message = f"Transação com ID {transaction_id} excluída com sucesso!"
                    
                    # Adiciona informação sobre série de parcelas, se aplicável
                    if is_installment and "reference_id" in transaction.installment_info:
                        message += f"\nEsta é uma parcela ({transaction.installment_info.get('current', 1)}/{transaction.installment_info.get('total', '?')}) de uma compra parcelada. Para excluir todas as parcelas, use o comando 'excluir todas as parcelas id [reference_id]'."
                    
                    # Adiciona informação sobre recorrência, se aplicável
                    if is_recurring:
                        message += f"\nEsta é uma transação recorrente ({transaction.recurrence.type.value}). As ocorrências futuras não serão geradas."
                        
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f"Não foi possível excluir a transação com ID {transaction_id}."}
        except ValueError:
            return {"status": "error", "message": "ID de transação inválido."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_update_transaction(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de atualizar uma transação."""
        try:
            if "transaction_id" not in entities:
                return {
                    "status": "error", 
                    "message": "Por favor, informe o ID da transação que deseja atualizar. Você pode ver os IDs usando o comando 'listar transações'."
                }
            
            transaction_id = UUID(entities["transaction_id"])
            
            # Verifica se a transação existe e pertence ao usuário
            transaction = await self.transaction_usecases.get_transaction(transaction_id)
            if not transaction or transaction.user_id != user_id:
                return {"status": "error", "message": f"Transação com ID {transaction_id} não encontrada."}
            
            # Prepara os dados para atualização
            update_data = {}
            
            if "amount" in entities:
                update_data["amount"] = entities["amount"]
            
            if "category" in entities:
                update_data["category"] = entities["category"]
            
            if "description" in entities:
                update_data["description"] = entities["description"]
            
            if "date" in entities:
                update_data["date"] = entities["date"]
                
            if "priority" in entities:
                update_data["priority"] = entities["priority"]
                
            if "tags" in entities:
                update_data["tags"] = entities["tags"]
                
            if "recurrence" in entities:
                update_data["recurrence"] = entities["recurrence"]
            
            if not update_data:
                return {"status": "error", "message": "Por favor, especifique pelo menos um campo para atualizar (valor, categoria, descrição, data, prioridade, etc)."}
            
            # Verifica se é uma transação recorrente ou parcelada
            is_recurring = transaction.is_recurring()
            is_installment = transaction.is_installment()
            
            if (is_recurring or is_installment) and "update_all" in entities and entities["update_all"]:
                # Para recorrências, não há um método específico de atualização em série
                if is_recurring:
                    updated_transaction = await self.transaction_usecases.update_transaction(transaction_id, update_data)
                    if updated_transaction:
                        return {"status": "success", "message": f"Transação recorrente com ID {transaction_id} atualizada com sucesso!"}
                    else:
                        return {"status": "error", "message": f"Não foi possível atualizar a transação com ID {transaction_id}."}
                        
                # Para parcelamentos, atualiza toda a série
                elif is_installment and "reference_id" in transaction.installment_info:
                    ref_id = transaction.installment_info["reference_id"]
                    updated_count = await self.transaction_usecases.update_installment_series(
                        reference_id=ref_id,
                        data=update_data,
                        update_future_only=entities.get("future_only", True)
                    )
                    
                    future_only = entities.get("future_only", True)
                    message = f"Todas as parcelas{' futuras' if future_only else ''} da compra foram atualizadas com sucesso! Total: {updated_count} parcelas."
                    
                    return {"status": "success", "message": message}
            else:
                # Atualização normal de transação única
                updated_transaction = await self.transaction_usecases.update_transaction(transaction_id, update_data)
                
                if updated_transaction:
                    message = f"Transação com ID {transaction_id} atualizada com sucesso!"
                    
                    # Adiciona informação sobre série de parcelas, se aplicável
                    if is_installment and "reference_id" in transaction.installment_info:
                        message += f"\nEsta é uma parcela ({transaction.installment_info.get('current', 1)}/{transaction.installment_info.get('total', '?')}) de uma compra parcelada. Para atualizar todas as parcelas, use o comando 'atualizar todas as parcelas id [reference_id]'."
                    
                    # Adiciona informação sobre recorrência, se aplicável
                    if is_recurring:
                        message += f"\nEsta é uma transação recorrente ({transaction.recurrence.type.value}). As configurações de recorrência foram atualizadas."
                        
                    return {"status": "success", "message": message}
                else:
                    return {"status": "error", "message": f"Não foi possível atualizar a transação com ID {transaction_id}."}
        except ValueError:
            return {"status": "error", "message": "ID de transação inválido."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_add_category(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de adicionar uma categoria."""
        try:
            if "name" not in entities:
                return {"status": "error", "message": "Por favor, informe o nome da categoria que deseja adicionar."}
            
            name = entities["name"]
            type_val = entities.get("type", "expense")  # Por padrão, é uma categoria de despesa
            
            category = await self.category_usecases.add_category(name, type_val)
            
            return {
                "status": "success", 
                "message": f"Categoria \"{category.name}\" ({('Receita' if category.type == 'income' else 'Despesa')}) adicionada com sucesso!",
                "data": {"category_id": str(category.id)}
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def _handle_list_categories(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de listar categorias."""
        try:
            type_val = entities.get("type")
            
            categories = await self.category_usecases.get_categories(type_val)
            
            if not categories:
                return {"status": "info", "message": "Nenhuma categoria encontrada."}
            
            # Agrupa categorias por tipo
            grouped = {}
            for cat in categories:
                if cat.type not in grouped:
                    grouped[cat.type] = []
                grouped[cat.type].append(cat.name)
            
            result = "Categorias disponíveis:\n\n"
            
            if "expense" in grouped and grouped["expense"]:
                result += "Despesas:\n"
                for i, name in enumerate(grouped["expense"]):
                    result += f"{i + 1}. {name}\n"
                result += "\n"
            
            if "income" in grouped and grouped["income"]:
                result += "Receitas:\n"
                for i, name in enumerate(grouped["income"]):
                    result += f"{i + 1}. {name}\n"
            
            return {"status": "success", "message": result, "data": {"categories": grouped}}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    def _get_help_message(self) -> Dict[str, Any]:
        """Retorna a mensagem de ajuda."""
        help_text = """Comandos disponíveis:

        1. Adicionar transações:
        "adicionar despesa de R$ 50 em Alimentação"
        "registrar gasto de 120,50 com descrição 'Mercado semanal'"
        "adicionar receita de R$ 2000 como Salário"
        "registrar renda de 500 de Freelance descrição 'Projeto XYZ'"

        2. Adicionar transações recorrentes:
        "adicionar despesa recorrente de R$ 99,90 em Assinaturas com descrição 'Netflix'"
        "registrar despesa fixa de R$ 1200 em Moradia frequência mensal"
        "adicionar receita recorrente de R$ 3000 como Salário"

        3. Adicionar despesas parceladas:
        "adicionar despesa parcelada de R$ 1200 em 12x em Eletrônicos"
        "registrar compra de 600 reais em 6 parcelas em Vestuário"
        "adicionar gasto de 300 em 3 vezes como 'Presente de aniversário'"

        4. Usar prioridades e tags:
        "adicionar despesa de R$ 200 em Alimentação prioridade alta"
        "registrar gasto de 50 reais com Uber tags transporte, trabalho"
        "adicionar despesa fixa de 200 reais em Internet prioridade média tags casa, essencial"

        5. Listar transações:
        "listar todas as transações"
        "mostrar despesas de janeiro"
        "exibir receitas de 01/01/2023 até 31/01/2023"
        "listar transações com prioridade alta"
        "mostrar gastos com tag essencial"

        6. Listar transações recorrentes e parceladas:
        "listar despesas recorrentes"
        "mostrar assinaturas"
        "listar parcelas"
        "exibir compras parceladas"

        7. Verificar saldo:
        "saldo atual"
        "balanço de janeiro"
        "resumo de 01/01/2023 até 31/01/2023"

        8. Gerenciar transações:
        "excluir transação id abc123"
        "atualizar transação id abc123 valor para 75,50"
        "excluir todas as parcelas id xyz789"
        "atualizar todas as parcelas futuras id xyz789 categoria para Lazer"

        9. Gerenciar categorias:
        "adicionar categoria Educação tipo despesa"
        "listar categorias de despesas"

        Digite "ajuda" a qualquer momento para ver esta mensagem novamente."""
                
        return {"status": "info", "message": help_text}
    
    # src/application/usecases/nlp_usecases.py - Adição de tratamento de confirmação

    async def process_command(self, user_id: UUID, command: str) -> Dict[str, Any]:
        """
        Processa um comando em linguagem natural e formata a resposta para WhatsApp.
        
        Args:
            user_id: ID do usuário
            command: Comando em linguagem natural
            
        Returns:
            Resultado do processamento formatado para WhatsApp
        """
        # Identifica a intenção e extrai entidades do comando
        intent, entities = await self.nlp_service.analyze(command)
        
        # Processa a intenção
        result = {}
        
        # Trata necessidade de confirmação
        if intent == "CONFIRM_NEEDED":
            return self._handle_confirmation_needed(entities)
        
        # Processa a intenção normal
        if intent == "ADD_EXPENSE":
            result = await self._handle_add_expense(user_id, entities)
        elif intent == "ADD_INCOME":
            result = await self._handle_add_income(user_id, entities)
        elif intent == "ADD_RECURRING":
            result = await self._handle_add_recurring(user_id, entities)
        elif intent == "ADD_INSTALLMENT":
            result = await self._handle_add_installment(user_id, entities)
        elif intent == "LIST_TRANSACTIONS":
            # Verifica se é para excluir todas as transações
            if entities.get("soft_delete", False):
                result = await self._handle_delete_all_transactions(user_id, entities)
            else:
                result = await self._handle_list_transactions(user_id, entities)
        elif intent == "LIST_RECURRING":
            result = await self._handle_list_recurring(user_id, entities)
        elif intent == "LIST_INSTALLMENTS":
            result = await self._handle_list_installments(user_id, entities)
        elif intent == "GET_BALANCE":
            result = await self._handle_get_balance(user_id, entities)
        elif intent == "DELETE_TRANSACTION":
            result = await self._handle_delete_transaction(user_id, entities)
        elif intent == "UPDATE_TRANSACTION":
            result = await self._handle_update_transaction(user_id, entities)
        elif intent == "ADD_CATEGORY":
            result = await self._handle_add_category(entities)
        elif intent == "LIST_CATEGORIES":
            result = await self._handle_list_categories(entities)
        elif intent == "HELP":
            result = self._get_help_message()
        else:
            result = {"status": "error", "message": "🤔 Não entendi o comando. Digite *ajuda* para ver os comandos disponíveis."}
        
        # Formata a resposta para ser amigável no WhatsApp
        result = self._format_for_whatsapp(result)
        
        return result
    
    def _handle_confirmation_needed(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a necessidade de confirmação do usuário."""
        
        confirmation_message = entities.get("confirmation_message", 
            "Não entendi completamente. Você pode fornecer mais detalhes?")
        
        # Armazena as entidades parciais extraídas para uso futuro
        partial_entities = entities.get("partial_entities", {})
        
        # Formata a resposta
        message = f"🤔 {confirmation_message}\n\n"
        
        # Se temos sugestões de categorias, as mostramos
        if "suggested_categories" in partial_entities:
            categories = partial_entities["suggested_categories"]
            message += "Categorias sugeridas:\n"
            for i, category in enumerate(categories):
                message += f"{i+1}. {category}\n"
            
            message += "\nResponda com o número ou nome da categoria que deseja usar."
        
        return {
            "status": "confirmation",
            "message": message,
            "data": {"partial_entities": partial_entities}
        }
    
    async def _handle_delete_all_transactions(self, user_id: UUID, entities: Dict[str, Any]) -> Dict[str, Any]:
        """Manipula a intenção de excluir todas as transações (soft delete)."""
        try:
            # Primeiro, lista as transações para mostrar ao usuário
            filters = {}
            
            # Filtro de tipo (receita/despesa)
            if "type" in entities:
                filters["type"] = entities["type"]
            
            transactions = await self.transaction_usecases.get_transactions(user_id, filters)
            
            if not transactions:
                return {"status": "info", "message": "Nenhuma transação encontrada para excluir."}
            
            # Em uma implementação real, aqui marcaríamos as transações como soft deleted
            # Por enquanto, apenas exibimos quais seriam excluídas
            
            # Formata a saída
            result = f"⚠️ *ATENÇÃO:* Você solicitou excluir {len(transactions)} transações.\n\n"
            result += f"🔍 *Transações que seriam excluídas:*\n\n"
            
            # Lista as primeiras 5 transações como exemplo
            for i, tx in enumerate(transactions[:5]):
                if i >= 5:
                    break
                result += f"*{i + 1}.* {'💵 Receita' if tx.type == 'income' else '💸 Despesa'}: R$ {tx.amount.amount:.2f}\n"
                result += f"   📋 {tx.category} | {tx.description}\n"
                result += f"   📅 {tx.date.strftime('%d/%m/%Y')}\n"
                result += f"   🆔 {tx.id}\n\n"
            
            if len(transactions) > 5:
                result += f"... e mais {len(transactions) - 5} transações.\n\n"
            
            result += "⚠️ Para confirmar a exclusão, responda com *\"confirmar exclusão\"*.\n"
            result += "Para cancelar, responda com *\"cancelar\"*."
            
            return {"status": "warning", "message": result, "data": {"count": len(transactions), "action": "confirm_delete"}}
        except Exception as e:
            return {"status": "error", "message": f"❌ Erro ao processar exclusão: {str(e)}"}
    
    def _format_for_whatsapp(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Formata a resposta para ser amigável no WhatsApp."""
        if "message" not in result:
            return result
        
        message = result["message"]
        status = result.get("status", "info")
        
        # Aplica emojis e formatação
        formatted_message = message
        
        # Adiciona emojis conforme o status
        prefix = ""
        if status == "success":
            prefix = "✅ "
        elif status == "error":
            prefix = "❌ "
        elif status == "info":
            prefix = "ℹ️ "
        elif status == "warning":
            prefix = "⚠️ "
        
        # Não adiciona prefixo se a mensagem já tem formatação WhatsApp
        if not any(marker in message[:15] for marker in ["*", "_", "~", "```"]):
            formatted_message = prefix + formatted_message
        
        # Substitui formatação específica para WhatsApp
        formatted_message = self._apply_whatsapp_formatting(formatted_message)
        
        # Atualiza a mensagem no resultado
        result["message"] = formatted_message
        
        return result
    
    def _apply_whatsapp_formatting(self, text: str) -> str:
        """Aplica formatação específica do WhatsApp ao texto."""
        # Lista de substituições para melhorar a experiência no WhatsApp
        replacements = [
            # Adiciona negrito para títulos e elementos importantes
            (r"Encontradas (\d+) transações:", r"*Encontradas \1 transações:*"),
            (r"Balanço financeiro", r"*Balanço financeiro*"),
            (r"Total de Receitas:", r"*Total de Receitas:*"),
            (r"Total de Despesas:", r"*Total de Despesas:*"),
            (r"Saldo:", r"*Saldo:*"),
            (r"Categoria: (.+)", r"📋 Categoria: *\1*"),
            (r"Descrição: (.+)", r"📝 Descrição: _\1_"),
            (r"Data: (.+)", r"📅 Data: \1"),
            (r"ID: (.+)", r"🆔 ID: `\1`"),
            (r"Receita: R\$ ([0-9,.]+)", r"💵 Receita: *R$ \1*"),
            (r"Despesa: R\$ ([0-9,.]+)", r"💸 Despesa: *R$ \1*"),
            (r"Prioridade: alta", r"🔴 Prioridade: *alta*"),
            (r"Prioridade: média", r"🟡 Prioridade: *média*"),
            (r"Prioridade: baixa", r"🟢 Prioridade: *baixa*"),
            
            # Substitui números e "bulletpoints" por emojis numéricos
            (r"^(\d+)\. ", r"*\1.* "),
            
            # Melhora a visualização de listas
            (r"Comandos disponíveis:", r"*Comandos disponíveis:* 📝"),
        ]
        
        # Aplica as substituições
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.MULTILINE)
        
        return text
    
# Abaixo estão os métodos adicionais que devem ser incluídos na classe NLPUseCases

async def process_command_with_entities(self, user_id: UUID, command: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa um comando em linguagem natural usando entidades fornecidas diretamente.
    Útil para continuar processamento após confirmação do usuário.
    
    Args:
        user_id: ID do usuário
        command: Comando em linguagem natural (pode estar vazio se entidades forem fornecidas)
        entities: Dicionário de entidades já extraídas
        
    Returns:
        Resultado do processamento
    """
    # Se o comando não estiver vazio, tenta extrair entidades adicionais
    if command.strip():
        # Identifica a intenção e extrai entidades do comando
        intent, new_entities = await self.nlp_service.analyze(command)
        
        # Combina as novas entidades com as fornecidas (priorizando as fornecidas)
        for key, value in new_entities.items():
            if key not in entities:
                entities[key] = value
    else:
        # Determina a intenção com base nas entidades fornecidas
        intent = self._determine_intent_from_entities(entities)
    
    # Processa a intenção com as entidades combinadas
    return await self._process_intent(user_id, intent, entities)

def _determine_intent_from_entities(self, entities: Dict[str, Any]) -> str:
    """
    Determina a intenção com base nas entidades fornecidas.
    
    Args:
        entities: Dicionário de entidades
        
    Returns:
        Intenção determinada
    """
    # Lógica para determinar a intenção a partir das entidades
    if "amount" in entities:
        if "type" in entities and entities["type"] == "income":
            return "ADD_INCOME"
        elif "installment_info" in entities or "total_installments" in entities:
            return "ADD_INSTALLMENT"
        elif "recurrence" in entities or "frequency" in entities:
            return "ADD_RECURRING"
        else:
            return "ADD_EXPENSE"
    
    if "start_date" in entities and "end_date" in entities:
        return "LIST_TRANSACTIONS"
    
    if "transaction_id" in entities:
        if any(key.startswith("update_") for key in entities):
            return "UPDATE_TRANSACTION"
        else:
            return "DELETE_TRANSACTION"
    
    # Se não conseguir determinar, usa ADD_EXPENSE como fallback
    return "ADD_EXPENSE"

async def _process_intent(self, user_id: UUID, intent: str, entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa uma intenção específica com as entidades fornecidas.
    
    Args:
        user_id: ID do usuário
        intent: Intenção identificada
        entities: Dicionário de entidades extraídas
        
    Returns:
        Resultado do processamento
    """
    # Reusa a lógica existente, mas separada para facilitar o reuso
    if intent == "ADD_EXPENSE":
        return await self._handle_add_expense(user_id, entities)
    elif intent == "ADD_INCOME":
        return await self._handle_add_income(user_id, entities)
    elif intent == "ADD_RECURRING":
        return await self._handle_add_recurring(user_id, entities)
    elif intent == "ADD_INSTALLMENT":
        return await self._handle_add_installment(user_id, entities)
    elif intent == "LIST_TRANSACTIONS":
        return await self._handle_list_transactions(user_id, entities)
    elif intent == "LIST_RECURRING":
        return await self._handle_list_recurring(user_id, entities)
    elif intent == "LIST_INSTALLMENTS":
        return await self._handle_list_installments(user_id, entities)
    elif intent == "GET_BALANCE":
        return await self._handle_get_balance(user_id, entities)
    elif intent == "DELETE_TRANSACTION":
        return await self._handle_delete_transaction(user_id, entities)
    elif intent == "UPDATE_TRANSACTION":
        return await self._handle_update_transaction(user_id, entities)
    elif intent == "ADD_CATEGORY":
        return await self._handle_add_category(entities)
    elif intent == "LIST_CATEGORIES":
        return await self._handle_list_categories(entities)
    elif intent == "HELP":
        return self._get_help_message()
    else:
        return {"status": "error", "message": "Comando não reconhecido. Digite 'ajuda' para ver os comandos disponíveis."}

async def generate_report(self, user_id: UUID, report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Gera um relatório com base nos parâmetros fornecidos.
    
    Args:
        user_id: ID do usuário
        report_type: Tipo de relatório (mensal, categoria, tendência)
        params: Parâmetros específicos do relatório
        
    Returns:
        Dados do relatório
    """
    if not self.analytics_usecases:
        return {
            "status": "error",
            "message": "Funcionalidade de relatórios não disponível."
        }
    
    try:
        if report_type == "monthly":
            # Relatório mensal
            year = params.get("year", datetime.now().year)
            month = params.get("month", datetime.now().month)
            report = await self.analytics_usecases.generate_monthly_report(user_id, year, month)
            
            # Formata a saída para exibição amigável
            result = f"📊 *Relatório Mensal - {report['month']}*\n\n"
            result += f"💰 *Resumo*\n"
            result += f"Receitas: R$ {report['summary']['total_income']:.2f}\n"
            result += f"Despesas: R$ {report['summary']['total_expense']:.2f}\n"
            result += f"Saldo: R$ {report['summary']['balance']:.2f}\n"
            result += f"Taxa de economia: {report['summary']['save_rate']:.2f}%\n\n"
            
            result += f"📈 *Categorias Principais*\n"
            for i, (category, data) in enumerate(list(report['categories'].items())[:5]):
                result += f"{i+1}. {category}: R$ {data['expense']:.2f} ({data.get('expense_percentage', 0):.1f}%)\n"
            
            return {
                "status": "success",
                "message": result,
                "data": report
            }
            
        elif report_type == "category":
            # Relatório por categoria
            start_date = params.get("start_date")
            end_date = params.get("end_date")
            
            spending = await self.analytics_usecases.get_spending_by_category(user_id, start_date, end_date)
            
            period_desc = ""
            if start_date and end_date:
                period_desc = f" ({start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')})"
            
            result = f"📊 *Gastos por Categoria{period_desc}*\n\n"
            
            for i, category in enumerate(spending):
                result += f"{i+1}. {category['category']}: R$ {category['amount']:.2f} ({category['percentage']:.1f}%)\n"
            
            return {
                "status": "success",
                "message": result,
                "data": {"categories": spending}
            }
            
        elif report_type == "trends":
            # Relatório de tendências
            months = params.get("months", 6)
            trends = await self.analytics_usecases.identify_trends(user_id, months)
            
            result = f"📊 *Análise de Tendências - Últimos {months} meses*\n\n"
            
            result += "📈 *Tendências Gerais*\n"
            for trend_type, data in trends["trends"].items():
                direction = "↑" if data["direction"] == "up" else "↓" if data["direction"] == "down" else "→"
                result += f"{trend_type.capitalize()}: {direction} {data['percentage']:.1f}%\n"
            
            result += "\n📉 *Tendências por Categoria*\n"
            for i, category in enumerate(trends["category_trends"][:5]):
                direction = "↑" if category["direction"] == "up" else "↓"
                result += f"{i+1}. {category['category']}: {direction} {category['strength']:.1f}%\n"
            
            return {
                "status": "success",
                "message": result,
                "data": trends
            }
            
        elif report_type == "budget":
            # Sugestão de orçamento
            budget = await self.analytics_usecases.suggest_budget(user_id)
            
            result = f"💼 *Sugestão de Orçamento*\n\n"
            result += f"Renda Mensal: R$ {budget['monthly_income']:.2f}\n\n"
            
            result += "🎯 *Distribuição Ideal*\n"
            result += f"Essenciais: R$ {budget['ideal']['essential_expenses']:.2f} (50%)\n"
            result += f"Não-essenciais: R$ {budget['ideal']['non_essential_expenses']:.2f} (30%)\n"
            result += f"Economias: R$ {budget['ideal']['savings']:.2f} (20%)\n\n"
            
            result += "💸 *Sugestão por Categoria*\n"
            for i, (category, amount) in enumerate(list(budget['suggested_budget'].items())[:5]):
                result += f"{i+1}. {category}: R$ {amount:.2f}\n"
            
            result += f"\n💭 *Dica:* {budget['message']}"
            
            return {
                "status": "success",
                "message": result,
                "data": budget
            }
            
        else:
            return {
                "status": "error",
                "message": "Tipo de relatório não reconhecido."
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Erro ao gerar relatório: {str(e)}"
        }