# src/infrastructure/nlp/llm_service.py
import openai
import json
from typing import Dict, Any, Tuple, List
from src.application.interfaces.services.nlp_service_interface import NLPServiceInterface
from config import settings
import re
from datetime import datetime, timedelta

class OpenAIService(NLPServiceInterface):
    """Serviço de processamento de linguagem natural usando OpenAI."""
    
    def __init__(self, api_key=None):
        """Inicializa o serviço com a chave da API."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        openai.api_key = self.api_key
        
        # Mapeamentos conhecidos para auxiliar na interpretação
        self.intent_mappings = {
            "listar_transacoes": "LIST_TRANSACTIONS",
            "listar_despesas": "LIST_TRANSACTIONS",
            "mostrar_despesas": "LIST_TRANSACTIONS",
            "ver_despesas": "LIST_TRANSACTIONS",
            "exibir_despesas": "LIST_TRANSACTIONS",
            "mostrar_receitas": "LIST_TRANSACTIONS",
            "listar_receitas": "LIST_TRANSACTIONS",
            "ver_receitas": "LIST_TRANSACTIONS",
            "remover_transacoes": "DELETE_TRANSACTION",
            "excluir_transacoes": "DELETE_TRANSACTION",
            "deletar_transacoes": "DELETE_TRANSACTION",
            "remover_todas": "DELETE_TRANSACTION",
            "excluir_todas": "DELETE_TRANSACTION",
            "deletar_todas": "DELETE_TRANSACTION",
            "apagar_todas": "DELETE_TRANSACTION",
            "limpar_transacoes": "DELETE_TRANSACTION"
        }
        
        # Expressões de tempo relativas
        self.time_expressions = {
            "hora": timedelta(hours=1),
            "horas": timedelta(hours=1),
            "dia": timedelta(days=1),
            "dias": timedelta(days=1),
            "semana": timedelta(weeks=1),
            "semanas": timedelta(weeks=1),
            "mês": timedelta(days=30),
            "meses": timedelta(days=30),
            "ano": timedelta(days=365),
            "anos": timedelta(days=365)
        }

    def _extract_time_entities(self, text: str) -> Dict[str, Any]:
        """Extrai entidades de tempo relativas do texto."""
        # Padrão para "N [horas|dias|semanas|meses|anos] atrás"
        time_pattern = r"(\d+)\s+(hora|horas|dia|dias|semana|semanas|mês|meses|ano|anos)\s+atrás"
        match = re.search(time_pattern, text.lower())
        
        if match:
            quantity = int(match.group(1))
            unit = match.group(2)
            
            # Calcula as datas
            now = datetime.now()
            time_delta = self.time_expressions.get(unit, timedelta(days=1)) * quantity
            start_date = now - time_delta
            
            # Determina o tipo de transação (despesa ou receita)
            type_val = "expense" if "despesa" in text.lower() else None
            if "receita" in text.lower():
                type_val = "income"
            
            return {
                "start_date": start_date,
                "end_date": now,
                "type": type_val
            }
        
        # Verifica "última/semana/mês/ano"
        period_pattern = r"(última|último|ultim[ao])\s+(hora|horas|dia|dias|semana|semanas|mês|meses|ano|anos)"
        match = re.search(period_pattern, text.lower())
        
        if match:
            unit = match.group(2)
            
            # Calcula as datas
            now = datetime.now()
            time_delta = self.time_expressions.get(unit, timedelta(days=1))
            start_date = now - time_delta
            
            # Determina o tipo de transação (despesa ou receita)
            type_val = "expense" if "despesa" in text.lower() else None
            if "receita" in text.lower():
                type_val = "income"
            
            return {
                "start_date": start_date,
                "end_date": now,
                "type": type_val
            }
        
        # Verifica "hoje", "ontem", "esta semana", etc.
        if "hoje" in text.lower():
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow = today + timedelta(days=1)
            
            # Determina o tipo de transação
            type_val = "expense" if "despesa" in text.lower() else None
            if "receita" in text.lower():
                type_val = "income"
                
            return {
                "start_date": today,
                "end_date": tomorrow - timedelta(microseconds=1),
                "type": type_val
            }
        
        if "ontem" in text.lower():
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday = today - timedelta(days=1)
            
            # Determina o tipo de transação
            type_val = "expense" if "despesa" in text.lower() else None
            if "receita" in text.lower():
                type_val = "income"
                
            return {
                "start_date": yesterday,
                "end_date": today - timedelta(microseconds=1),
                "type": type_val
            }
        
        # Não encontrou padrões de tempo reconhecíveis
        return {}
    
    def _is_delete_all_command(self, text: str) -> bool:
        """Verifica se o comando é para excluir todas as transações."""
        text_lower = text.lower()
        
        delete_words = ["remover", "excluir", "deletar", "apagar", "limpar"]
        all_words = ["todas", "todos", "tudo", "todas as", "todos os"]
        
        has_delete_word = any(word in text_lower for word in delete_words)
        has_all_word = any(word in text_lower for word in all_words)
        
        # Verifica se menciona despesas, receitas ou transações
        target_words = ["despesa", "despesas", "gasto", "gastos", 
                         "receita", "receitas", "transação", "transações"]
        has_target = any(word in text_lower for word in target_words)
        
        return has_delete_word and (has_all_word or has_target)
    
    def _parse_relative_date(self, date_str: str) -> datetime:
        """Converte uma string de data relativa para um objeto datetime."""
        now = datetime.now()
        
        date_str = date_str.lower()
        
        if date_str == "hoje":
            return now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if date_str == "ontem":
            return (now - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        
        if "semana passada" in date_str:
            start_of_week = now - timedelta(days=now.weekday() + 7)
            return start_of_week.replace(hour=0, minute=0, second=0, microsecond=0)
        
        if "mês passado" in date_str:
            if now.month == 1:
                return datetime(now.year - 1, 12, 1, 0, 0, 0)
            else:
                return datetime(now.year, now.month - 1, 1, 0, 0, 0)
        
        # Failsafe: retorna a data atual se não conseguir interpretar
        return now    

    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural usando a API da OpenAI.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        # Tenta interpretar comandos temporais relativos antes de enviar para o GPT
        time_entities = self._extract_time_entities(text)
        if time_entities and "type" in time_entities:
            # Se identificamos um comando temporal, retornamos diretamente
            return "LIST_TRANSACTIONS", time_entities
        
        # Tenta verificar se é um comando para remover todas as transações
        if self._is_delete_all_command(text):
            return "LIST_TRANSACTIONS", {"type": "expense", "soft_delete": True}
        
        try:
            # Definir o sistema de classificação de intenções
            prompt = f"""
            Você é um assistente financeiro especializado em interpretar comandos em linguagem natural.
            
            Classifique o seguinte comando de finanças pessoais em uma das seguintes intenções:
            - ADD_EXPENSE: adicionar uma despesa
            - ADD_INCOME: adicionar uma receita
            - ADD_RECURRING: adicionar despesa ou receita recorrente
            - ADD_INSTALLMENT: adicionar despesa parcelada
            - LIST_TRANSACTIONS: listar transações (gerais, receitas ou despesas)
            - LIST_RECURRING: listar transações recorrentes
            - LIST_INSTALLMENTS: listar transações parceladas
            - GET_BALANCE: verificar saldo ou situação financeira
            - DELETE_TRANSACTION: excluir uma transação
            - UPDATE_TRANSACTION: atualizar uma transação
            - ADD_CATEGORY: adicionar categoria
            - LIST_CATEGORIES: listar categorias
            - HELP: pedido de ajuda
            - UNKNOWN: se o comando não estiver claro, use esta intenção
            - CONFIRM_NEEDED: se for necessário pedir mais informações ao usuário
            
            Ao analisar o comando, use seu contexto e conhecimento de categoria para determinar se é uma despesa ou receita.
            
            Para categorias, use uma das seguintes quando for claro a partir do contexto:
            - Alimentação: para comida, restaurantes, mercado, supermercado, etc.
            - Transporte: para gastos com transporte, combustível, Uber, táxi, etc.
            - Moradia: para aluguel, condomínio, luz, água, internet, etc.
            - Saúde: para despesas médicas, remédios, consultas, etc.
            - Educação: para cursos, livros, material escolar, etc.
            - Lazer: para cinema, teatro, viagens, streaming, etc.
            - Vestuário: para roupas, calçados, acessórios, etc.
            - Trabalho: para material de escritório, serviços prestados a clientes, etc.
            
            Se a categoria não estiver clara ou não corresponder a uma das acima, defina entities.need_confirmation = true
            e sugira categorias prováveis em entities.suggested_categories.
            
            Se estiver interpretando uma receita por serviço prestado ou venda, marque como ADD_INCOME e
            use categoria "Trabalho" ou "Vendas".

            E extraia as seguintes entidades, quando aplicável:
            - amount: valor monetário
            - category: categoria da transação
            - description: descrição da transação
            - date: data da transação
            - start_date: data inicial para relatórios
            - end_date: data final para relatórios
            - month: mês para relatórios
            - transaction_id: ID de alguma transação
            - type: tipo de transação (income/expense)
            - priority: prioridade da transação (alta, média, baixa)
            - frequency: frequência da transação recorrente (diária, semanal, mensal, etc.)
            - tags: tags da transação
            - total_installments: número total de parcelas
            - is_recurring: se a transação é recorrente
            - is_installment: se a transação é parcelada
            - soft_delete: se deve realizar exclusão lógica (não física)
            - need_confirmation: se precisa de confirmação do usuário
            - suggested_categories: lista de categorias prováveis quando não for claro
            - confirmation_message: mensagem sugerida para pedir confirmação
            
            Exemplos específicos de interpretação:
            1. "Fiz um serviço de 150 manutenção de pc" => ADD_INCOME, amount=150, description="manutenção de pc", category="Trabalho", type="income" 
            (este é claramente um SERVIÇO PRESTADO, então é uma RECEITA, não uma despesa)
            
            2. "Gastei 50 com açaí" => ADD_EXPENSE, amount=50, description="açaí", category="Alimentação", type="expense"
            
            3. "Comprei material de escritório por 80" => ADD_EXPENSE, amount=80, description="material de escritório", category="Trabalho", type="expense"
            
            4. "Vendi meu celular velho por 300" => ADD_INCOME, amount=300, description="venda de celular usado", category="Vendas", type="income"
            
            5. "Paguei 200 no mecânico" => ADD_EXPENSE, amount=200, description="mecânico", category="Transporte", type="expense" (contexto indica reparo de veículo)
            
            Comando: {text}
            
            Responda apenas em formato JSON com as chaves 'intent' e 'entities'.
            """
            
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": prompt}
                ],
                temperature=0.1
            )
            
            result = response.choices[0].message.content
            
            # Converte a resposta de texto para um objeto Python
            try:
                parsed = json.loads(result)
                
                intent = parsed.get("intent", "UNKNOWN")
                entities = parsed.get("entities", {})
                
                # Se o modelo indicar que precisamos de confirmação
                if intent == "CONFIRM_NEEDED" or entities.get("need_confirmation", False):
                    confirmation_message = entities.get("confirmation_message", 
                        "Não entendi completamente. Você pode fornecer mais detalhes?")
                    
                    suggested_categories = entities.get("suggested_categories", [])
                    if suggested_categories:
                        category_options = ", ".join(suggested_categories)
                        confirmation_message = f"Não tenho certeza sobre a categoria. Poderia ser uma destas: {category_options}. Você pode confirmar?"
                    
                    return "CONFIRM_NEEDED", {
                        "confirmation_message": confirmation_message,
                        "partial_entities": entities
                    }
                
                # Se parece ser um serviço prestado mas está marcado como despesa, corrige para receita
                if "serviço" in text.lower() and "fiz" in text.lower() and intent == "ADD_EXPENSE":
                    intent = "ADD_INCOME"
                    entities["type"] = "income"
                    if "category" in entities and entities["category"] in ["Alimentação", "Outros"]:
                        entities["category"] = "Trabalho"
                
                # Processa datas relativas
                if "start_date" in entities and isinstance(entities["start_date"], str):
                    entities["start_date"] = self._parse_relative_date(entities["start_date"])
                    
                if "end_date" in entities and isinstance(entities["end_date"], str):
                    entities["end_date"] = self._parse_relative_date(entities["end_date"])
                
                # Mapeia intenções, se necessário
                if intent in self.intent_mappings:
                    intent = self.intent_mappings[intent]
                
                # Log da interpretação de comando não reconhecido (poderia ser salvo em banco de dados para análise)
                print(f"[LLM] Comando interpretado: '{text}' -> {intent}, {entities}")
                
                return intent, entities
            except json.JSONDecodeError:
                # Falha ao analisar resposta JSON
                print(f"[LLM] Falha ao analisar resposta JSON: {result}")
                
                # Tenta extrair intent e entities do texto
                intent_match = re.search(r"'intent':\s*['\"]([A-Z_]+)['\"]", result)
                intent = intent_match.group(1) if intent_match else "UNKNOWN"
                
                # Fallback para interpretação simples
                return self._basic_fallback_analysis(text)
                
        except Exception as e:
            print(f"Erro ao processar comando com OpenAI: {e}")
            
            # Fallback para o reconhecedor de intenções padrão
            return self._basic_fallback_analysis(text)