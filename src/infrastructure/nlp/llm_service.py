# src/infrastructure/nlp/llm_service.py
import openai
from typing import Dict, Any, Tuple
from src.application.interfaces.services.nlp_service_interface import NLPServiceInterface
from config import settings

class OpenAIService(NLPServiceInterface):
    """Serviço de processamento de linguagem natural usando OpenAI."""
    
    def __init__(self, api_key=None):
        """Inicializa o serviço com a chave da API."""
        self.api_key = api_key or settings.OPENAI_API_KEY
        openai.api_key = self.api_key
    
    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural usando a API da OpenAI.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        try:
            # Definir o sistema de classificação de intenções
            prompt = f"""
            Classifique o seguinte comando de finanças pessoais em uma das seguintes intenções:
            - ADD_EXPENSE: adicionar uma despesa
            - ADD_INCOME: adicionar uma receita
            - LIST_TRANSACTIONS: listar transações (gerais, receitas ou despesas)
            - GET_BALANCE: verificar saldo ou situação financeira
            - DELETE_TRANSACTION: excluir uma transação
            - UPDATE_TRANSACTION: atualizar uma transação
            - ADD_CATEGORY: adicionar categoria
            - LIST_CATEGORIES: listar categorias
            - HELP: pedido de ajuda

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
            import json
            parsed = json.loads(result)
            
            intent = parsed.get("intent", "UNKNOWN")
            entities = parsed.get("entities", {})
            
            return intent, entities
            
        except Exception as e:
            print(f"Erro ao processar comando com OpenAI: {e}")
            # Fallback para o reconhecedor de intenções padrão
            from src.infrastructure.nlp.intent_recognizer import IntentRecognizer
            recognizer = IntentRecognizer()
            return await recognizer.analyze(text)