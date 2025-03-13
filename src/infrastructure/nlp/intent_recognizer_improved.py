# src/infrastructure/nlp/intent_recognizer_improved.py
import re
import difflib
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple, List, Optional, Set
import unicodedata
from config import settings


class ImprovedIntentRecognizer:
    """Implementação aprimorada do serviço de processamento de linguagem natural."""
    
    def __init__(self, language='pt-BR'):
        """Inicializa o reconhecedor de intenções com padrões regex predefinidos e suporte a idiomas."""
        # Idioma atual
        self.language = language
        
        # Carrega os padrões para o idioma escolhido
        self.load_language_patterns(language)
        
        # Mapeamento de meses em português para números
        self.month_map = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
        
        # Mapeamento de meses em inglês para números
        self.month_map_en = {
            "january": 1, "february": 2, "march": 3, "april": 4,
            "may": 5, "june": 6, "july": 7, "august": 8,
            "september": 9, "october": 10, "november": 11, "december": 12
        }
        
        # Palavras e frases comumente digitadas com erro
        self.common_misspellings = {
            # Português
            "adcionar": "adicionar",
            "dispesa": "despesa",
            "despeza": "despesa",
            "receta": "receita",
            "sálario": "salário",
            "sálario": "salário",
            "transferencia": "transferência",
            "registar": "registrar",
            "lançar": "registrar",
            "lancar": "registrar",
            "colocar": "registrar",
            "apagar": "excluir",
            "deletar": "excluir",
            "remover": "excluir",
            "saldo": "balanço",
            "dinhero": "dinheiro",
            "calculo": "cálculo",
            "gastos": "despesas",
            "ganhos": "receitas",
            "grana": "dinheiro",
            "gasto": "despesa",
            "ganhei": "recebi",
            "gastei": "paguei",
            "paguei": "gastei",
            # Inglês
            "expence": "expense",
            "expanse": "expense",
            "exspense": "expense",
            "recieve": "receive",
            "recieved": "received",
            "recept": "receipt",
            "ballance": "balance",
            "mony": "money",
            "chek": "check",
            "cheque": "check",
            "calculate": "calculate",
            "salery": "salary",
            "pament": "payment"
        }
        
        # Dicionário para armazenar comandos populares e suas descrições
        self.popular_commands = {
            "pt-BR": {
                "adicionar despesa": "Exemplo: adicionar despesa de R$ 50 em Alimentação",
                "registrar receita": "Exemplo: registrar receita de R$ 2000 como Salário",
                "mostrar saldo": "Exemplo: mostrar meu saldo atual",
                "listar transações": "Exemplo: listar transações do mês atual",
                "ver despesas": "Exemplo: ver despesas de janeiro",
                "excluir transação": "Exemplo: excluir transação id 123abc",
                "ajuda": "Lista todos os comandos disponíveis"
            },
            "en-US": {
                "add expense": "Example: add expense of $50 for Food",
                "record income": "Example: record income of $2000 as Salary",
                "show balance": "Example: show my current balance",
                "list transactions": "Example: list transactions for current month",
                "view expenses": "Example: view expenses for January",
                "delete transaction": "Example: delete transaction id 123abc",
                "help": "Lists all available commands"
            }
        }
        
        # Categorias padrão e suas alternativas
        self.category_synonyms = {
            "pt-BR": {
                "Alimentação": ["comida", "refeição", "restaurante", "supermercado", "mercado", "lanche", "almoço", "jantar", "café", "padaria", "feira"],
                "Transporte": ["uber", "táxi", "ônibus", "metrô", "combustível", "gasolina", "passagem", "estacionamento", "pedágio", "carro", "moto"],
                "Moradia": ["aluguel", "condomínio", "água", "luz", "energia", "gás", "internet", "telefone", "iptu", "reforma", "manutenção", "casa"],
                "Saúde": ["médico", "hospital", "farmácia", "remédio", "consulta", "exame", "plano de saúde", "dentista", "psicólogo", "terapia"],
                "Educação": ["escola", "faculdade", "curso", "livro", "material escolar", "mensalidade", "matrícula", "universidade", "aula", "estudo"],
                "Lazer": ["cinema", "teatro", "show", "viagem", "passeio", "restaurante", "bar", "festa", "academia", "assinatura", "streaming", "netflix"],
                "Trabalho": ["material de escritório", "equipamento", "serviço", "cliente", "freelance", "projeto"],
                "Salário": ["pagamento", "contracheque", "salário", "remuneração", "ordenado", "vencimento", "pró-labore", "renda"],
                "Investimentos": ["aplicação", "rendimento", "dividendo", "juros", "ação", "bolsa", "fundo", "tesouro", "renda fixa", "renda variável"],
                "Outros": ["diversos", "geral", "indefinido", "variado", "pessoal", "outros gastos"]
            },
            "en-US": {
                "Food": ["meal", "restaurant", "supermarket", "grocery", "snack", "lunch", "dinner", "breakfast", "bakery", "fast food"],
                "Transportation": ["uber", "taxi", "bus", "subway", "fuel", "gas", "fare", "parking", "toll", "car", "motorcycle"],
                "Housing": ["rent", "mortgage", "condo", "water", "electricity", "power", "gas", "internet", "phone", "maintenance", "house"],
                "Health": ["doctor", "hospital", "pharmacy", "medicine", "drug", "consultation", "exam", "health insurance", "dentist", "psychologist", "therapy"],
                "Education": ["school", "college", "university", "course", "book", "tuition", "enrollment", "class", "study", "student"],
                "Entertainment": ["cinema", "theater", "concert", "travel", "trip", "restaurant", "bar", "party", "gym", "subscription", "streaming", "netflix"],
                "Work": ["office supply", "equipment", "service", "client", "freelance", "project"],
                "Salary": ["payment", "paycheck", "salary", "compensation", "wage", "income", "earnings"],
                "Investments": ["application", "yield", "dividend", "interest", "stock", "fund", "treasury", "fixed income", "variable income"],
                "Others": ["miscellaneous", "general", "undefined", "varied", "personal", "other expenses"]
            }
        }
        
        # Expressões de tempo relativas
        self.time_expressions = {
            "pt-BR": {
                "hoje": self._get_today,
                "ontem": lambda: datetime.now() - timedelta(days=1),
                "anteontem": lambda: datetime.now() - timedelta(days=2),
                "esta semana": lambda: datetime.now() - timedelta(days=datetime.now().weekday()),
                "semana passada": lambda: datetime.now() - timedelta(days=datetime.now().weekday() + 7),
                "este mês": lambda: datetime(datetime.now().year, datetime.now().month, 1),
                "mês passado": self._get_last_month,
                "último mês": self._get_last_month,
                "mês anterior": self._get_last_month
            },
            "en-US": {
                "today": self._get_today,
                "yesterday": lambda: datetime.now() - timedelta(days=1),
                "day before yesterday": lambda: datetime.now() - timedelta(days=2),
                "this week": lambda: datetime.now() - timedelta(days=datetime.now().weekday()),
                "last week": lambda: datetime.now() - timedelta(days=datetime.now().weekday() + 7),
                "this month": lambda: datetime(datetime.now().year, datetime.now().month, 1),
                "last month": self._get_last_month,
                "previous month": self._get_last_month
            }
        }
    
    def load_language_patterns(self, language):
        """Carrega os padrões regex para o idioma escolhido."""
        if language == 'pt-BR':
            self._load_portuguese_patterns()
        elif language == 'en-US':
            self._load_english_patterns()
        else:
            # Padrão para português caso não reconheça o idioma
            self._load_portuguese_patterns()
    
    def _load_portuguese_patterns(self):
        """Carrega os padrões regex para português."""
        # Definição dos padrões regex para reconhecimento de intenções
        self.intent_patterns = {
            "ADD_EXPENSE": r"^(adicionar|registrar|inserir|nova|novo|cadastrar|lançar|colocar)\s+(despesa|gasto|custo|pagamento|compra|conta)",
            "ADD_INCOME": r"^(adicionar|registrar|inserir|nova|novo|cadastrar|recebi|ganhei|entrou)\s+(receita|renda|ganho|salário|dinheiro|pagamento)",
            "ADD_RECURRING": r"^(adicionar|registrar|inserir|nova|novo|cadastrar)\s+(despesa|gasto|receita|renda)\s+(recorrente|fixa|mensal|periódica|repetida)",
            "ADD_INSTALLMENT": r"^(adicionar|registrar|inserir|nova|novo|cadastrar|comprei)\s+(despesa|gasto|compra)\s+(parcelad|em parcelas|a prazo|em vezes|dividid|prestações)",
            "LIST_TRANSACTIONS": r"^(listar|mostrar|exibir|ver|consultar|todas|todos|quais)\s+(transações|despesas|gastos|receitas|rendas|movimentações)|quanto\s+(gastei|recebi|ganhei|entrou|saiu|paguei)",
            "LIST_RECURRING": r"^(listar|mostrar|exibir|ver|consultar|quais)\s+(despesas|gastos|receitas|rendas)\s+(recorrentes|fixas|fixos|mensais|periódicas|repetidas)",
            "LIST_INSTALLMENTS": r"^(listar|mostrar|exibir|ver|consultar|quais)\s+(despesas|gastos|compras)\s+(parcelad|parcelas|a prazo|em vezes|prestações)",
            "GET_BALANCE": r"^(saldo|balanço|quanto\s+tenho|resumo|situação|resultado|total|posição|extrato|quanto\s+sobrou|como\s+estou|status)|quanto\s+(gastei|recebi|resta|sobrou|tenho|possuo|disponível)",
            "DELETE_TRANSACTION": r"^(excluir|apagar|deletar|remover|cancelar|desfazer|eliminar)\s+(transação|despesa|receita|gasto|movimentação|lançamento)",
            "UPDATE_TRANSACTION": r"^(atualizar|editar|modificar|alterar|mudar|corrigir|ajustar)\s+(transação|despesa|receita|gasto|movimentação|lançamento)",
            "ADD_CATEGORY": r"^(adicionar|nova|novo|criar|cadastrar|inserir)\s+categoria",
            "LIST_CATEGORIES": r"^(listar|mostrar|exibir|ver|todas|todos|quais)\s+categorias",
            "HELP": r"^(ajuda|como\s+usar|o\s+que\s+posso\s+fazer|comandos|instruções|manual|socorro|suporte|tutorial)"
        }
        
        # Definição dos padrões regex para extração de entidades
        self.entity_patterns = {
            "amount": r"(?:R\$\s?)?(\d+[,.]\d+|\d+)(?:\s+reais|\s+pila|\s+conto|\s+pau|\s+mangos)?",
            "category_expense": r"(?:em|para|com|na|no|categoria)\s+([a-zA-ZÀ-ÿ\s]+?)(?:\s+(?:de|com|no valor|valor|descrição|R\$|\d|\"|\')|$)",
            "category_income": r"(?:de|como|categoria)\s+([a-zA-ZÀ-ÿ\s]+?)(?:\s+(?:de|com|no valor|valor|descrição|R\$|\d|\"|\')|$)",
            "category_explicit": r"categoria\s+([a-zA-ZÀ-ÿ\s]+?)(?:\s+(?:de|com|no valor|valor|descrição|R\$|\d|\"|\')|$)",
            "description": r"descrição\s+[\"'](.+?)[\"']|[\"'](.+?)[\"']",
            "description_natural": r"(?:com|de|para)\s+([a-zA-ZÀ-ÿ\s]+?)(?:\s+(?:no valor|de R\$|R\$)|$)",
            "date": r"(?:em|dia|data)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "transaction_id": r"id\s+([a-f0-9-]+)",
            "period": r"(?:de|em|no)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\s+(?:a|até|ao)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "month": r"(?:em|no|de)\s+(janeiro|fevereiro|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro)",
            "category_type": r"tipo\s+(despesa|receita)",
            "update_amount": r"valor\s+(?:para\s+)?(?:R\$\s?)?(\d+[,.]\d+|\d+)",
            "update_category": r"categoria\s+(?:para\s+)?([a-zA-ZÀ-ÿ\s]+)",
            "update_description": r"descrição\s+(?:para\s+)?[\"'](.+?)[\"']",
            "update_date": r"data\s+(?:para\s+)?(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "priority": r"(?:prioridade|urgência|importância)\s+(alta|média|baixa)",
            "frequency": r"(?:frequência|periodicidade)\s+(diária|semanal|quinzenal|mensal|bimestral|trimestral|semestral|anual)",
            "installments": r"(?:em|de)\s+(\d+)\s+(?:parcelas|vezes|prestações|x)",
            "tag": r"(?:tag|marcador|etiqueta)s?\s+([a-zA-ZÀ-ÿ,\s]+)",
            "time_period": r"(hoje|ontem|anteontem|esta semana|semana passada|este mês|mês passado|último mês|mês anterior)"
        }
        
        # Padrões para correção de erros comuns
        self.common_errors = {
            r"\b(\d+),(\d+)": r"\1.\2",  # Substituir vírgula por ponto em valores numéricos
            r"u?m\s+mil\s+": "1000",     # Converter expressões como "um mil reais" para números
            r"(\d+)\s+mil\s+": r"\1000", # Converter expressões como "2 mil reais" para números
        }
    
    def _load_english_patterns(self):
        """Carrega os padrões regex para inglês."""
        # Definição dos padrões regex para reconhecimento de intenções em inglês
        self.intent_patterns = {
            "ADD_EXPENSE": r"^(add|register|insert|new|create|record|input|log|spent|bought|paid|pay)\s+(expense|spending|cost|payment|bill|purchase)",
            "ADD_INCOME": r"^(add|register|insert|new|create|record|input|log|received|earned|got)\s+(income|revenue|earning|salary|money|payment)",
            "ADD_RECURRING": r"^(add|register|insert|new|create)\s+(expense|spending|income|revenue)\s+(recurring|fixed|monthly|periodic|repeating)",
            "ADD_INSTALLMENT": r"^(add|register|insert|new|create|bought)\s+(expense|spending|purchase)\s+(installment|partial|divided|payments)",
            "LIST_TRANSACTIONS": r"^(list|show|display|view|all|get|what)\s+(transactions|expenses|spending|income|revenue|movements)|how\s+much\s+(spent|received|earned|in|out|paid)",
            "LIST_RECURRING": r"^(list|show|display|view|get|what)\s+(expenses|spending|income|revenue)\s+(recurring|fixed|monthly|periodic|repeating)",
            "LIST_INSTALLMENTS": r"^(list|show|display|view|get|what)\s+(expenses|spending|purchases)\s+(installments|partial|payments)",
            "GET_BALANCE": r"^(balance|how\s+much|summary|status|result|total|statement|position|how\s+much\s+left|how\s+am\s+i|status)|how\s+much\s+(spent|received|left|have|available)",
            "DELETE_TRANSACTION": r"^(delete|remove|cancel|undo|eliminate)\s+(transaction|expense|income|spending|movement|entry)",
            "UPDATE_TRANSACTION": r"^(update|edit|modify|change|correct|adjust)\s+(transaction|expense|income|spending|movement|entry)",
            "ADD_CATEGORY": r"^(add|new|create|register|insert)\s+category",
            "LIST_CATEGORIES": r"^(list|show|display|view|all|get|what)\s+categories",
            "HELP": r"^(help|how\s+to\s+use|what\s+can\s+i\s+do|commands|instructions|manual|support|tutorial)"
        }
        
        # Definição dos padrões regex para extração de entidades em inglês
        self.entity_patterns = {
            "amount": r"(?:\$\s?)?(\d+[,.]\d+|\d+)(?:\s+dollars|\s+bucks)?",
            "category_expense": r"(?:for|on|in|with|category)\s+([a-zA-Z\s]+?)(?:\s+(?:of|with|value|amount|description|\$|\d|\"|\')|$)",
            "category_income": r"(?:from|as|category)\s+([a-zA-Z\s]+?)(?:\s+(?:of|with|value|amount|description|\$|\d|\"|\')|$)",
            "category_explicit": r"category\s+([a-zA-Z\s]+?)(?:\s+(?:of|with|value|amount|description|\$|\d|\"|\')|$)",
            "description": r"description\s+[\"'](.+?)[\"']|[\"'](.+?)[\"']",
            "description_natural": r"(?:for|from|of)\s+([a-zA-Z\s]+?)(?:\s+(?:value|amount|\$|\d)|$)",
            "date": r"(?:on|date)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "transaction_id": r"id\s+([a-f0-9-]+)",
            "period": r"(?:from|between)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)\s+(?:to|until|through)\s+(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "month": r"(?:in|for|of)\s+(january|february|march|april|may|june|july|august|september|october|november|december)",
            "category_type": r"type\s+(expense|income)",
            "update_amount": r"amount\s+(?:to\s+)?(?:\$\s?)?(\d+[,.]\d+|\d+)",
            "update_category": r"category\s+(?:to\s+)?([a-zA-Z\s]+)",
            "update_description": r"description\s+(?:to\s+)?[\"'](.+?)[\"']",
            "update_date": r"date\s+(?:to\s+)?(\d{1,2}\/\d{1,2}(?:\/\d{2,4})?)",
            "priority": r"(?:priority|importance)\s+(high|medium|low)",
            "frequency": r"(?:frequency|periodicity)\s+(daily|weekly|biweekly|monthly|bimonthly|quarterly|semiannual|annual)",
            "installments": r"(?:in|of)\s+(\d+)\s+(?:installments|payments|parts|x)",
            "tag": r"(?:tag|label|marker)s?\s+([a-zA-Z,\s]+)",
            "time_period": r"(today|yesterday|day before yesterday|this week|last week|this month|last month|previous month)"
        }
        
        # Padrões para correção de erros comuns em inglês
        self.common_errors = {
            r"\b(\d+),(\d+)": r"\1.\2",  # Substituir vírgula por ponto em valores numéricos (pode ocorrer em entradas em inglês também)
            r"one\s+thousand\s+": "1000",     # Converter expressões como "one thousand dollars" para números
            r"(\d+)\s+thousand\s+": r"\1000", # Converter expressões como "2 thousand dollars" para números
        }
    
    def set_language(self, language):
        """
        Define o idioma para processamento.
        
        Args:
            language: Código do idioma (ex: 'pt-BR', 'en-US')
        """
        self.language = language
        self.load_language_patterns(language)
    
    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural para identificar intenções e entidades.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        # Pré-processa o texto (corrige erros comuns e normaliza)
        corrected_text = self._preprocess_text(text)
        
        # Log da correção (útil para depuração)
        if corrected_text != text:
            print(f"Texto corrigido: '{text}' -> '{corrected_text}'")
        
        # Identifica a intenção
        intent = self._identify_intent(corrected_text)
        
        # Se a intenção não for reconhecida, tenta sugerir um comando similar
        if intent == "UNKNOWN":
            suggestion = self._suggest_similar_command(corrected_text)
            if suggestion:
                return "CONFIRM_NEEDED", {
                    "confirmation_message": f"Não entendi exatamente o que você quis dizer. Você quis dizer '{suggestion}'?",
                    "partial_entities": {"suggestion": suggestion}
                }
            
            # Se não conseguir sugerir, tenta usar o LLM se configurado
            if hasattr(settings, 'USE_LLM_FALLBACK') and settings.USE_LLM_FALLBACK:
                try:
                    from src.infrastructure.nlp.llm_service import OpenAIService
                    llm_service = OpenAIService()
                    return await llm_service.analyze(corrected_text)
                except Exception as e:
                    print(f"Erro ao usar serviço LLM: {e}")
        
        # Extrai entidades relevantes para a intenção
        entities = self._extract_entities(intent, corrected_text)
        
        # Se não conseguir extrair certas entidades, pede confirmação
        if intent in ["ADD_EXPENSE", "ADD_INCOME"] and "amount" not in entities:
            return "CONFIRM_NEEDED", {
                "confirmation_message": "Não consegui identificar o valor. Qual é o valor da transação?",
                "partial_entities": entities
            }
        
        if intent in ["ADD_EXPENSE", "ADD_INCOME"] and "category" not in entities:
            # Sugere algumas categorias comuns
            suggested_categories = []
            if intent == "ADD_EXPENSE":
                suggested_categories = list(self.category_synonyms[self.language].keys())[:5]
            else:
                suggested_categories = ["Salário", "Investimentos", "Freelance"]
                
            return "CONFIRM_NEEDED", {
                "confirmation_message": "Não consegui identificar a categoria. Em qual categoria você gostaria de classificar esta transação?",
                "partial_entities": {
                    **entities,
                    "suggested_categories": suggested_categories
                }
            }
            
        # Adiciona feedback quando necessário
        if "feedback" in entities:
            entities["feedback"] = self._generate_feedback(intent, entities)
        
        return intent, entities
        
    def _normalize_text(self, text: str) -> str:
        """Normaliza o texto para facilitar o reconhecimento."""
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', text.strip())
        # Converte para minúsculas
        normalized = normalized.lower()
        # Remove acentos
        normalized = ''.join(c for c in unicodedata.normalize('NFD', normalized)
                            if unicodedata.category(c) != 'Mn')
        return normalized
    
    def _correct_misspellings(self, text: str) -> str:
        """Corrige erros comuns de digitação usando um dicionário de correções."""
        words = text.split()
        corrected_words = []
        
        for word in words:
            # Verifica se a palavra está no dicionário de erros comuns
            normalized_word = self._normalize_text(word)
            if normalized_word in self.common_misspellings:
                corrected_words.append(self.common_misspellings[normalized_word])
            else:
                corrected_words.append(word)
        
        return ' '.join(corrected_words)
    
    def _apply_common_error_corrections(self, text: str) -> str:
        """Aplica correções para padrões de erro comuns usando regex."""
        corrected = text
        for pattern, replacement in self.common_errors.items():
            corrected = re.sub(pattern, replacement, corrected)
        return corrected
    
    def _preprocess_text(self, text: str) -> str:
    """
    Pré-processa o texto para normalização e correção de erros comuns.
    
    Args:
        text: Texto original
        
    Returns:
        Texto corrigido e normalizado
    """
    # Aplica correções para erros comuns de digitação
    corrected = self._correct_misspellings(text)
    
    # Aplica correções para padrões de erro comuns
    corrected = self._apply_common_error_corrections(corrected)
    
    # Define os mapeamentos de linguagem (pode ser expandido para suportar múltiplos idiomas)
    mappings = {
        "pt-BR": {
            "todas as despesas": "listar despesas",
            "todos os gastos": "listar despesas",
            "todas as receitas": "listar receitas",
            "todos os ganhos": "listar receitas",
            "todas as transações": "listar transações",
            "todos os movimentos": "listar transações",
            "quanto gastei": "listar despesas",
            "quanto recebi": "listar receitas",
            "qual meu saldo": "saldo",
            "como estão minhas finanças": "saldo",
            "minhas despesas": "listar despesas",
            "meus gastos": "listar gastos",
            "minhas receitas": "listar receitas",
            "meus ganhos": "listar receitas",
            "despesas recorrentes": "listar despesas recorrentes",
            "assinaturas": "listar despesas recorrentes",
            "despesas fixas": "listar despesas recorrentes",
            "despesas mensais": "listar despesas recorrentes",
            "despesas parceladas": "listar despesas parceladas",
            "parcelas": "listar despesas parceladas",
            "prestações": "listar despesas parceladas",
            "comprei": "adicionar despesa",
            "gastei": "adicionar despesa",
            "paguei": "adicionar despesa",
            "recebi": "adicionar receita",
            "ganhei": "adicionar receita"
        },
        "en-US": {
            "all expenses": "list expenses",
            "total expenses": "list expenses", 
            "all incomes": "list income",
            "total income": "list income",
            "all transactions": "list transactions",
            "how much i spent": "list expenses", 
            "how much i received": "list income",
            "my balance": "balance",
            "financial status": "balance",
            "my expenses": "list expenses",
            "my incomes": "list income",
            "recurring expenses": "list recurring expenses",
            "subscriptions": "list recurring expenses",
            "installment expenses": "list installments",
            "bought": "add expense",
            "spent": "add expense", 
            "paid": "add expense",
            "received": "add income",
            "earned": "add income"
        }
    }
    
    # Normaliza o texto (converte para minúsculas e remove acentos)
    normalized = self._normalize_text(corrected)
    
    # Aplica mapeamentos de comandos comuns
    language_mappings = mappings.get(self.language, mappings["pt-BR"])
    
    for phrase, replacement in language_mappings.items():
        if phrase in normalized:
            return replacement
    
    return corrected