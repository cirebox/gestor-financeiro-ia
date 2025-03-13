# src/application/usecases/nlp_usecases.py
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
        elif intent == "LIST_TRANSACTIONS":
            return await self._handle_list_transactions(user_id, entities)
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
        try:
            transaction = await self.transaction_usecases.add_transaction(
                user_id=user_id,
                type="expense",
                amount=entities.get("amount", 0),
                category=entities.get("category", "Outros"),
                description=entities.get("description", "Despesa sem descrição"),
                date=entities.get("date")
            )
            return {
                "status": "success",
                "message": f"Despesa de R$ {transaction.amount.amount:.2f} em {transaction.category} registrada com sucesso!",
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
                date=entities.get("date")
            )
            return {
                "status": "success",
                "message": f"Receita de R$ {transaction.amount.amount:.2f} como {transaction.category} registrada com sucesso!",
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
                result += f"   ID: {tx.id}\n\n"
            
            return {"status": "success", "message": result, "data": {"count": len(transactions)}}
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
                pass
            
            balance = await self.transaction_usecases.get_balance(user_id, start_date, end_date)
            
            period_desc = ""
            if start_date and end_date:
                period_desc = f" ({start_date.strftime('%d/%m/%Y')} a {end_date.strftime('%d/%m/%Y')})"
            elif "month" in entities:
                period_desc = f" ({entities['month']})"
            
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
            
            deleted = await self.transaction_usecases.delete_transaction(transaction_id)
            
            if deleted:
                return {"status": "success", "message": f"Transação com ID {transaction_id} excluída com sucesso!"}
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
            
            if not update_data:
                return {"status": "error", "message": "Por favor, especifique pelo menos um campo para atualizar (valor, categoria, descrição ou data)."}
            
            updated_transaction = await self.transaction_usecases.update_transaction(transaction_id, update_data)
            
            if updated_transaction:
                return {"status": "success", "message": f"Transação com ID {transaction_id} atualizada com sucesso!"}
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

1. Adicionar despesa:
   "adicionar despesa de R$ 50 em Alimentação"
   "registrar gasto de 120,50 com descrição 'Mercado semanal'"

2. Adicionar receita:
   "adicionar receita de R$ 2000 como Salário"
   "registrar renda de 500 de Freelance descrição 'Projeto XYZ'"

3. Listar transações:
   "listar todas as transações"
   "mostrar despesas de janeiro"
   "exibir receitas de 01/01/2023 até 31/01/2023"

4. Verificar saldo:
   "saldo atual"
   "balanço de janeiro"
   "resumo de 01/01/2023 até 31/01/2023"

5. Gerenciar transações:
   "excluir transação id abc123"
   "atualizar transação id abc123 valor para 75,50"

6. Gerenciar categorias:
   "adicionar categoria Educação tipo despesa"
   "listar categorias de despesas"

Digite "ajuda" a qualquer momento para ver esta mensagem novamente."""
        
        return {"status": "info", "message": help_text}