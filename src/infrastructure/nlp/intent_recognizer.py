# src/infrastructure/nlp/intent_recognizer.py
import re
from datetime import datetime
from typing import Dict, Any, Tuple
from config import settings

from src.application.interfaces.services.nlp_service_interface import NLPServiceInterface


class IntentRecognizer(NLPServiceInterface):
    """Implementação do serviço de processamento de linguagem natural."""
    
    def __init__(self):
        """Inicializa o reconhecedor de intenções com padrões regex predefinidos."""
        # Definição dos padrões regex para reconhecimento de intenções
        self.intent_patterns = {
            "ADD_EXPENSE": r"^(adicionar|registrar|inserir|nova|novo|cadastrar)\s+(despesa|gasto|custo)",
            "ADD_INCOME": r"^(adicionar|registrar|inserir|nova|novo|cadastrar)\s+(receita|renda|ganho)",
            "ADD_RECURRING": r"^(adicionar|registrar|inserir|nova|novo|cadastrar)\s+(despesa|gasto|receita|renda)\s+(recorrente|fixa|mensal|periód)",
            "ADD_INSTALLMENT": r"^(adicionar|registrar|inserir|nova|novo|cadastrar)\s+(despesa|gasto)\s+(parcelad|em parcelas|a prazo)",
            "LIST_TRANSACTIONS": r"^(listar|mostrar|exibir|ver|consultar|todas|todos)\s+(transações|despesas|gastos|receitas|rendas)|quanto\s+(gastei|recebi|ganhei)",
            "LIST_RECURRING": r"^(listar|mostrar|exibir|ver|consultar)\s+(despesas|gastos|receitas|rendas)\s+(recorrentes|fixas|fixos|mensais)",
            "LIST_INSTALLMENTS": r"^(listar|mostrar|exibir|ver|consultar)\s+(despesas|gastos)\s+(parcelad|parcelas|a prazo)",
            "GET_BALANCE": r"^(saldo|balanço|quanto\s+tenho|resumo|situação|resultado|total)|quanto\s+(gastei|recebi|resta|sobrou)",
            "DELETE_TRANSACTION": r"^(excluir|apagar|deletar|remover)\s+(transação|despesa|receita)",
            "UPDATE_TRANSACTION": r"^(atualizar|editar|modificar|alterar|mudar)\s+(transação|despesa|receita)",
            "ADD_CATEGORY": r"^(adicionar|nova|novo|criar)\s+categoria",
            "LIST_CATEGORIES": r"^(listar|mostrar|exibir|ver|todas|todos)\s+categorias",
            "HELP": r"^(ajuda|como\s+usar|o\s+que\s+posso\s+fazer|comandos)"
        }
        
        # Definição dos padrões regex para extração de entidades
        self.entity_patterns = {
            "amount": r"(?:R\$\s?)?(\d+[,.]\d+|\d+)",
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
            "installments": r"(?:em|de)\s+(\d+)\s+(?:parcelas|vezes|prestações)",
            "tag": r"(?:tag|marcador|etiqueta)s?\s+([a-zA-ZÀ-ÿ,\s]+)"
        }
        
        # Mapeamento de meses em português para números
        self.month_map = {
            "janeiro": 1, "fevereiro": 2, "março": 3, "abril": 4,
            "maio": 5, "junho": 6, "julho": 7, "agosto": 8,
            "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12
        }
    
    async def analyze(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Analisa um texto em linguagem natural para identificar intenções e entidades.
        
        Args:
            text: Texto a ser analisado
            
        Returns:
            Uma tupla contendo a intenção identificada e um dicionário de entidades extraídas
        """
        # Identifica a intenção
        intent = self._identify_intent(text)
        
        # Se não identificou com confiança e a configuração existe
        if intent == "UNKNOWN" and hasattr(settings, 'USE_LLM_FALLBACK') and settings.USE_LLM_FALLBACK:
            try:
                from src.infrastructure.nlp.llm_service import OpenAIService
                llm_service = OpenAIService()
                return await llm_service.analyze(text)
            except Exception as e:
                print(f"Erro ao usar serviço LLM: {e}")
        
        # Extrai entidades relevantes para a intenção
        entities = self._extract_entities(intent, text)
        
        return intent, entities
        
    def _normalize_text(self, text: str) -> str:
        """Normaliza o texto para facilitar o reconhecimento."""
        # Remove espaços extras
        normalized = re.sub(r'\s+', ' ', text.strip())
        # Converte para minúsculas
        normalized = normalized.lower()
        return normalized
    
    def _preprocess_text(self, text: str) -> str:
        """Pré-processa o texto para normalização."""
        # Normaliza o texto (remove espaços extras, converte para minúsculas)
        normalized = re.sub(r'\s+', ' ', text.strip().lower())
        
        # Mapeia frases comuns para comandos reconhecidos
        mappings = {
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
            "prestações": "listar despesas parceladas"
        }
        
        for pattern, replacement in mappings.items():
            if pattern in normalized:
                return replacement
        
        return normalized
    
    def _identify_intent(self, text: str) -> str:
        """Identifica a intenção do usuário a partir do texto."""
        # Pré-processa o texto para melhorar a detecção
        text = self._preprocess_text(text)
        
        # Pontua cada intenção com base na correspondência com os padrões
        scores = {}
        for intent, pattern in self.intent_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            scores[intent] = len(matches)
        
        # Seleciona a intenção com maior pontuação
        if any(scores.values()):
            return max(scores.items(), key=lambda x: x[1])[0]
        
        # Se mencionou mês, provavelmente é uma consulta de saldo
        if re.search(r'(Janeiro|Fevereiro|Março|Abril|Maio|Junho|Julho|Agosto|Setembro|Outubro|Novembro|Dezembro|mês)', text, re.IGNORECASE):
            if re.search(r'(gasto|despesa)', text, re.IGNORECASE):
                return "LIST_TRANSACTIONS"
            return "GET_BALANCE"
        
        # Detecção para despesas recorrentes sem padrão claro
        if "recorrente" in text or "fixa" in text or "mensal" in text:
            if "adicionar" in text or "registrar" in text or "nova" in text:
                return "ADD_RECURRING"
            elif "listar" in text or "mostrar" in text or "exibir" in text:
                return "LIST_RECURRING"
        
        # Detecção para despesas parceladas sem padrão claro
        if "parcela" in text or "a prazo" in text or "parcelado" in text or "prestação" in text:
            if "adicionar" in text or "registrar" in text or "nova" in text:
                return "ADD_INSTALLMENT"
            elif "listar" in text or "mostrar" in text or "exibir" in text:
                return "LIST_INSTALLMENTS"
        
        # Se não encontrou nenhuma intenção clara
        return "UNKNOWN"
    
    def _extract_entities(self, intent: str, text: str) -> Dict[str, Any]:
        """Extrai entidades relevantes com base na intenção identificada."""
        entities = {}
        
        # Extração comum para várias intenções
        if intent in ["ADD_EXPENSE", "ADD_INCOME", "ADD_RECURRING", "ADD_INSTALLMENT"]:
            # Extrai valor
            amount_match = re.search(self.entity_patterns["amount"], text)
            if amount_match:
                amount_str = amount_match.group(1).replace(',', '.')
                entities["amount"] = float(amount_str)
            
            # Extrai categoria
            if intent in ["ADD_EXPENSE", "ADD_RECURRING", "ADD_INSTALLMENT"]:
                category_match = (
                    re.search(self.entity_patterns["category_explicit"], text) or 
                    re.search(self.entity_patterns["category_expense"], text)
                )
            else:  # ADD_INCOME
                category_match = (
                    re.search(self.entity_patterns["category_explicit"], text) or 
                    re.search(self.entity_patterns["category_income"], text)
                )
            
            if category_match:
                entities["category"] = category_match.group(1).strip()
            
            # Extrai descrição (formato específico)
            description_match = re.search(self.entity_patterns["description"], text)
            if description_match:
                # Pode estar no grupo 1 ou 2, dependendo de qual regex correspondeu
                entities["description"] = description_match.group(1) if description_match.group(1) else description_match.group(2)
            else:
                # Tenta extrair descrição de forma mais natural
                # Primeiro extrai texto entre "com" e valor numérico
                description_natural_match = None
                
                # Na versão melhorada, tentamos extrair a descrição de maneira mais natural
                # Padrão: se o texto contém "com [algo]" e esse algo não foi identificado como categoria
                com_pattern = r"(?:com|de)\s+([a-zA-ZÀ-ÿ\s]+)(?=\s+\d|\s+R\$|\s*$)"
                description_natural_match = re.search(com_pattern, text)
                
                if description_natural_match:
                    possible_description = description_natural_match.group(1).strip()
                    
                    # Verifica se a descrição extraída não é a mesma que a categoria
                    if "category" not in entities or possible_description != entities["category"]:
                        entities["description"] = possible_description
                
                # Se não encontrou descrição com o padrão anterior, tenta outro enfoque
                if "description" not in entities:
                    # Extrai texto após a categoria e valor, assumindo que pode ser uma descrição
                    if "category" in entities and "amount" in entities:
                        parts = text.split()
                        
                        # Encontra a posição do valor
                        amount_str = str(entities["amount"]).replace('.', ',')
                        amount_positions = [i for i, part in enumerate(parts) if amount_str in part or part.isdigit()]
                        
                        if amount_positions:
                            # Assume que tudo após o valor é uma descrição
                            # a menos que sejam palavras-chave específicas
                            last_amount_pos = amount_positions[-1]
                            if last_amount_pos + 1 < len(parts):
                                remaining_text = ' '.join(parts[last_amount_pos + 1:])
                                
                                # Ignora palavras-chave que podem não ser parte da descrição
                                ignore_keywords = [
                                    "descrição", "categoria", "em", "como", "de", "para", 
                                    "data", "dia", "prioridade", "frequência", "recorrente", 
                                    "parcela", "parcelas", "vezes", "prestação", "prestações", 
                                    "tag", "tags", "mensal", "semanal", "anual"
                                ]
                                if not any(keyword in remaining_text.lower() for keyword in ignore_keywords):
                                    entities["description"] = remaining_text.strip()
            
            # Extrai data
            date_match = re.search(self.entity_patterns["date"], text)
            if date_match:
                entities["date"] = self._parse_date(date_match.group(1))
                
            # Extrai prioridade
            priority_match = re.search(self.entity_patterns["priority"], text)
            if priority_match:
                entities["priority"] = priority_match.group(1).lower()
                
            # Extrai tags
            tag_match = re.search(self.entity_patterns["tag"], text)
            if tag_match:
                tag_text = tag_match.group(1)
                # Divide as tags pela vírgula e remove espaços
                entities["tags"] = [tag.strip() for tag in tag_text.split(',')]
                
            # Extrai informações específicas para transações recorrentes
            if intent == "ADD_RECURRING":
                # Extrai frequência
                frequency_match = re.search(self.entity_patterns["frequency"], text)
                if frequency_match:
                    entities["frequency"] = frequency_match.group(1).lower()
                else:
                    # Se não especificou, assume mensal
                    entities["frequency"] = "mensal"
                    
                # Para transações recorrentes, já forma o objeto de recorrência
                entities["recurrence"] = {
                    "frequency": entities.get("frequency", "mensal"),
                    "end_date": None,
                    "occurrences": None
                }
                
            # Extrai informações específicas para transações parceladas
            if intent == "ADD_INSTALLMENT":
                # Extrai número de parcelas
                installments_match = re.search(self.entity_patterns["installments"], text)
                if installments_match:
                    entities["total_installments"] = int(installments_match.group(1))
                else:
                    # Busca diretamente por números seguidos de "parcelas", "vezes" ou "prestações"
                    alternate_pattern = r"(\d+)\s+(?:parcelas|vezes|prestações)"
                    alternate_match = re.search(alternate_pattern, text)
                    if alternate_match:
                        entities["total_installments"] = int(alternate_match.group(1))
                    else:
                        # Valor padrão (2 parcelas)
                        entities["total_installments"] = 2
                        
                # Para transações parceladas, já forma o objeto de parcelamento
                entities["installment_info"] = {
                    "total": entities.get("total_installments", 2),
                    "current": 1
                }
        
        elif intent in ["LIST_TRANSACTIONS", "GET_BALANCE", "LIST_RECURRING", "LIST_INSTALLMENTS"]:
            # Extrai período (intervalo de datas)
            period_match = re.search(self.entity_patterns["period"], text)
            if period_match:
                entities["start_date"] = self._parse_date(period_match.group(1))
                entities["end_date"] = self._parse_date(period_match.group(2))
            
            # Extrai mês
            month_match = re.search(self.entity_patterns["month"], text)
            if month_match:
                month_name = month_match.group(1).lower()
                month_num = self.month_map.get(month_name)
                if month_num:
                    current_year = datetime.now().year
                    entities["month"] = datetime(current_year, month_num, 1)
            
            # Para LIST_TRANSACTIONS e LIST_RECURRING, extrai também tipo e categoria
            if intent in ["LIST_TRANSACTIONS", "LIST_RECURRING"]:
                if "despesas" in text or "gastos" in text:
                    entities["type"] = "expense"
                elif "receitas" in text or "rendas" in text or "ganhos" in text:
                    entities["type"] = "income"
                
                category_match = re.search(self.entity_patterns["category_explicit"], text)
                if category_match:
                    entities["category"] = category_match.group(1).strip()
                    
            # Para LIST_RECURRING, adiciona flag específica
            if intent == "LIST_RECURRING":
                entities["is_recurring"] = True
                
            # Para LIST_INSTALLMENTS, adiciona flag específica
            if intent == "LIST_INSTALLMENTS":
                entities["is_installment"] = True
                
            # Extrai prioridade para filtros
            priority_match = re.search(self.entity_patterns["priority"], text)
            if priority_match:
                entities["priority"] = priority_match.group(1).lower()
                
            # Extrai tags para filtros
            tag_match = re.search(self.entity_patterns["tag"], text)
            if tag_match:
                tag_text = tag_match.group(1)
                entities["tags"] = [tag.strip() for tag in tag_text.split(',')]
        
        elif intent in ["DELETE_TRANSACTION", "UPDATE_TRANSACTION"]:
            # Extrai ID da transação
            transaction_id_match = re.search(self.entity_patterns["transaction_id"], text)
            if transaction_id_match:
                entities["transaction_id"] = transaction_id_match.group(1)
            
            # Para UPDATE_TRANSACTION, extrai campos a serem atualizados
            if intent == "UPDATE_TRANSACTION":
                update_amount_match = re.search(self.entity_patterns["update_amount"], text)
                if update_amount_match:
                    amount_str = update_amount_match.group(1).replace(',', '.')
                    entities["amount"] = float(amount_str)
                
                update_category_match = re.search(self.entity_patterns["update_category"], text)
                if update_category_match:
                    entities["category"] = update_category_match.group(1).strip()
                
                update_description_match = re.search(self.entity_patterns["update_description"], text)
                if update_description_match:
                    entities["description"] = update_description_match.group(1)
                
                update_date_match = re.search(self.entity_patterns["update_date"], text)
                if update_date_match:
                    entities["date"] = self._parse_date(update_date_match.group(1))
                    
                # Extrai prioridade
                priority_match = re.search(self.entity_patterns["priority"], text)
                if priority_match:
                    entities["priority"] = priority_match.group(1).lower()
                    
                # Extrai tags
                tag_match = re.search(self.entity_patterns["tag"], text)
                if tag_match:
                    tag_text = tag_match.group(1)
                    entities["tags"] = [tag.strip() for tag in tag_text.split(',')]
        
        elif intent == "ADD_CATEGORY":
            # Extrai nome da categoria
            category_match = re.search(self.entity_patterns["category_explicit"], text)
            if category_match:
                entities["name"] = category_match.group(1).strip()
            
            # Extrai tipo da categoria
            category_type_match = re.search(self.entity_patterns["category_type"], text)
            if category_type_match:
                type_str = category_type_match.group(1).lower()
                entities["type"] = "income" if type_str == "receita" else "expense"
        
        elif intent == "LIST_CATEGORIES":
            # Extrai tipo de categoria a ser listada
            if "despesas" in text:
                entities["type"] = "expense"
            elif "receitas" in text:
                entities["type"] = "income"
        
        # Se não encontrarmos categoria mas for uma despesa, usamos uma fallback
        if intent in ["ADD_EXPENSE", "ADD_RECURRING", "ADD_INSTALLMENT"] and "category" not in entities:
            # Caso especial para detecção de categorias comuns
            common_categories = {
                "alimenta": "Alimentação",
                "comida": "Alimentação",
                "restaurante": "Alimentação",
                "lanche": "Alimentação",
                "café": "Alimentação",
                "mercado": "Alimentação",
                "supermercado": "Alimentação",
                "farmácia": "Saúde",
                "médico": "Saúde",
                "remédio": "Saúde",
                "transporte": "Transporte",
                "uber": "Transporte",
                "táxi": "Transporte",
                "combustível": "Transporte",
                "gasolina": "Transporte",
                "escola": "Educação",
                "curso": "Educação",
                "faculdade": "Educação",
                "aluguel": "Moradia",
                "condomínio": "Moradia",
                "água": "Moradia",
                "luz": "Moradia",
                "internet": "Moradia",
                "cinema": "Lazer",
                "show": "Lazer",
                "jogo": "Lazer",
                "streaming": "Lazer",
                "netflix": "Lazer",
                "spotify": "Lazer",
                "assinatura": "Lazer"
            }
            
            # Tenta encontrar palavras-chave no texto que indiquem a categoria
            text_normalized = text.lower()
            for keyword, category in common_categories.items():
                if keyword in text_normalized:
                    entities["category"] = category
                    break
            
            # Se ainda não temos categoria, estabelecemos um valor padrão
            if "category" not in entities:
                entities["category"] = "Outros"
        
        return entities
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Converte uma string de data para um objeto datetime.
        
        Args:
            date_str: String de data no formato DD/MM/YYYY ou DD/MM
            
        Returns:
            Objeto datetime correspondente à data
        """
        parts = date_str.split('/')
        
        if len(parts) == 3:
            day, month, year = map(int, parts)
            # Se o ano tem apenas 2 dígitos, assume o século atual
            if year < 100:
                year += 2000
        elif len(parts) == 2:
            day, month = map(int, parts)
            year = datetime.now().year
        else:
            # Caso de formato de data inválido, usa a data atual
            return datetime.now()
        
        # Valida e ajusta a data se necessário
        if month < 1 or month > 12:
            month = datetime.now().month
        
        max_days = [31, 29 if self._is_leap_year(year) else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        if day < 1 or day > max_days[month - 1]:
            day = 1
        
        return datetime(year, month, day)
    
    def _is_leap_year(self, year: int) -> bool:
        """Verifica se um ano é bissexto."""
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)