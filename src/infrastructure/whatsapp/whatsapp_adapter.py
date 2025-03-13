# src/infrastructure/whatsapp/whatsapp_adapter.py
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging
import re

from src.application.usecases.whatsapp_contact_usecases import WhatsAppContactUseCases
from src.application.usecases.nlp_usecases import NLPUseCases
from src.infrastructure.whatsapp.session_manager import SessionManager

logger = logging.getLogger(__name__)

class WhatsAppAdapter:
    """Adaptador para integração do WhatsApp com o sistema."""
    
    def __init__(
        self,
        whatsapp_contact_usecases: WhatsAppContactUseCases,
        nlp_usecases: NLPUseCases
    ):
        """
        Inicializa o adaptador do WhatsApp.
        
        Args:
            whatsapp_contact_usecases: Casos de uso de contatos do WhatsApp
            nlp_usecases: Casos de uso de processamento de linguagem natural
        """
        self.whatsapp_contact_usecases = whatsapp_contact_usecases
        self.nlp_usecases = nlp_usecases
        self.session_manager = SessionManager()
        
        # Comandos especiais que podem ser usados durante a conversação
        self.special_commands = {
            "ajuda": self._handle_help_command,
            "help": self._handle_help_command,
            "limpar": self._handle_clear_command,
            "clear": self._handle_clear_command,
            "reiniciar": self._handle_restart_command,
            "restart": self._handle_restart_command,
            "reset": self._handle_restart_command
        }
    
    async def process_message(
        self,
        phone_number: str,
        message_text: str,
        message_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Processa uma mensagem recebida pelo WhatsApp.
        
        Args:
            phone_number: Número de telefone do remetente
            message_text: Texto da mensagem
            message_data: Dados adicionais da mensagem (opcional)
            
        Returns:
            Resposta processada para enviar de volta
        """
        try:
            # Valida o número de telefone
            if not self._validate_phone_number(phone_number):
                logger.error(f"Número de telefone inválido: {phone_number}")
                return {
                    "status": "error",
                    "message": "Número de telefone inválido."
                }
            
            # Obtém ou cria a sessão para o contato
            session = await self.session_manager.get_session(phone_number)
            
            # Adiciona a mensagem do usuário ao histórico
            await self.session_manager.add_message_to_history(phone_number, "user", message_text)
            
            # Verifica se é um comando especial
            trimmed_text = message_text.strip().lower()
            if trimmed_text in self.special_commands:
                response = await self.special_commands[trimmed_text](phone_number, session)
                
                # Adiciona a resposta ao histórico
                await self.session_manager.add_message_to_history(phone_number, "assistant", response["message"])
                
                return response
            
            # Verifica se é uma continuação de uma conversa anterior
            context = session.get("context", {})
            
            # Se for uma continuação de uma solicitação anterior que precisa de confirmação
            if context.get("awaiting_confirmation"):
                response = await self._handle_confirmation_flow(phone_number, message_text, session)
                
                # Adiciona a resposta ao histórico
                await self.session_manager.add_message_to_history(phone_number, "assistant", response["message"])
                
                return response
            
            # Busca ou cria o contato e usuário associado
            contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
            
            if not contact:
                # Registra o novo contato
                contact = await self.whatsapp_contact_usecases.register_contact(phone_number)
                
            # Verifica se o onboarding foi concluído
            if not contact.onboarding_complete:
                # Processa o fluxo de onboarding
                onboarding_complete, response_message, updated_data = await self.whatsapp_contact_usecases.handle_onboarding_step(
                    phone_number=phone_number,
                    message=message_text
                )
                
                # Atualiza a sessão com o status de onboarding
                await self.session_manager.update_session(
                    phone_number,
                    {
                        "onboarding_complete": onboarding_complete,
                        "onboarding_step": updated_data.get("onboarding_step", "welcome")
                    }
                )
                
                # Se o onboarding não estiver completo, retorna a mensagem de onboarding
                if not onboarding_complete:
                    # Adiciona a resposta ao histórico
                    await self.session_manager.add_message_to_history(phone_number, "assistant", response_message)
                    
                    return {
                        "status": "onboarding",
                        "message": response_message,
                        "data": {
                            "step": updated_data.get("onboarding_step", "welcome")
                        }
                    }
            
            # Processa o comando usando o NLP
            user_id = contact.user_id
            
            # Atualiza o ID do usuário na sessão
            if session.get("user_id") != str(user_id):
                await self.session_manager.update_session(
                    phone_number,
                    {"user_id": str(user_id)}
                )
            
            # Obtém o histórico recente para dar contexto ao processamento
            history = await self.session_manager.get_message_history(phone_number, limit=5)
            context_messages = []
            
            # Formata o histórico para uso no processamento de linguagem natural
            for msg in reversed(history[1:]):  # Ignora a mensagem atual e inverte para ordem cronológica
                context_messages.append(f"{msg['role']}: {msg['content']}")
            
            # Adiciona o contexto ao comando, se houver mensagens anteriores
            command_with_context = message_text
            if context_messages:
                # Aqui você poderia formatar o contexto de uma maneira específica
                # para seu processador de linguagem natural, se necessário
                pass
            
            # Processar o comando NLP
            result = await self.nlp_usecases.process_command(user_id, command_with_context)
            
            # Verificar se o NLP solicita confirmação
            if result.get("status") == "confirmation":
                # Salva o contexto para continuação posterior
                await self.session_manager.update_session(
                    phone_number,
                    {
                        "context": {
                            "awaiting_confirmation": True,
                            "confirmation_type": "nlp",
                            "partial_entities": result.get("data", {}).get("partial_entities", {})
                        }
                    }
                )
            else:
                # Limpa qualquer contexto de confirmação anterior
                await self.session_manager.update_session(
                    phone_number,
                    {"context": {}}
                )
            
            # Adiciona a resposta ao histórico
            await self.session_manager.add_message_to_history(phone_number, "assistant", result["message"])
            
            return result
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}")
            error_message = "Desculpe, ocorreu um erro ao processar sua mensagem. Por favor, tente novamente."
            
            # Adiciona a mensagem de erro ao histórico
            await self.session_manager.add_message_to_history(phone_number, "assistant", error_message)
            
            return {
                "status": "error",
                "message": error_message
            }
    
    async def _handle_confirmation_flow(
        self,
        phone_number: str,
        message_text: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manipula o fluxo de confirmação para mensagens que requerem interação adicional.
        
        Args:
            phone_number: Número de telefone do contato
            message_text: Texto da mensagem
            session: Sessão atual do usuário
            
        Returns:
            Resposta processada para enviar de volta
        """
        context = session.get("context", {})
        confirmation_type = context.get("confirmation_type")
        
        if confirmation_type == "nlp":
            # Extrai as entidades parciais
            partial_entities = context.get("partial_entities", {})
            
            # Combina a resposta do usuário com as entidades parciais
            if "suggested_categories" in partial_entities:
                # Verifica se o usuário enviou um número correspondente a uma categoria sugerida
                categories = partial_entities["suggested_categories"]
                response = message_text.strip()
                
                try:
                    # Tenta interpretar como um número
                    index = int(response) - 1
                    if 0 <= index < len(categories):
                        # Seleciona a categoria correspondente
                        selected_category = categories[index]
                        
                        # Atualiza as entidades parciais
                        partial_entities["category"] = selected_category
                        del partial_entities["suggested_categories"]
                        
                        # Obtém o contato para processar o comando
                        contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
                        
                        # Limpa o contexto de confirmação
                        await self.session_manager.update_session(
                            phone_number,
                            {"context": {}}
                        )
                        
                        # Processa o comando com as entidades atualizadas
                        result = await self.nlp_usecases.process_command_with_entities(
                            contact.user_id,
                            "",  # Comando vazio, pois estamos fornecendo as entidades diretamente
                            partial_entities
                        )
                        
                        return result
                    else:
                        # Índice fora do intervalo
                        return {
                            "status": "confirmation",
                            "message": f"Por favor, selecione um número entre 1 e {len(categories)}."
                        }
                except ValueError:
                    # Não é um número, trata como nome de categoria
                    # Verifica se corresponde exatamente a uma das categorias sugeridas
                    for category in categories:
                        if response.lower() == category.lower():
                            # Atualiza as entidades parciais
                            partial_entities["category"] = category
                            del partial_entities["suggested_categories"]
                            
                            # Obtém o contato para processar o comando
                            contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
                            
                            # Limpa o contexto de confirmação
                            await self.session_manager.update_session(
                                phone_number,
                                {"context": {}}
                            )
                            
                            # Processa o comando com as entidades atualizadas
                            result = await self.nlp_usecases.process_command_with_entities(
                                contact.user_id,
                                "",  # Comando vazio, pois estamos fornecendo as entidades diretamente
                                partial_entities
                            )
                            
                            return result
                    
                    # Se chegou aqui, não encontrou correspondência
                    # Tenta usar a resposta como categoria diretamente
                    partial_entities["category"] = response
                    del partial_entities["suggested_categories"]
                    
                    # Obtém o contato para processar o comando
                    contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
                    
                    # Limpa o contexto de confirmação
                    await self.session_manager.update_session(
                        phone_number,
                        {"context": {}}
                    )
                    
                    # Processa o comando com as entidades atualizadas
                    result = await self.nlp_usecases.process_command_with_entities(
                        contact.user_id,
                        "",  # Comando vazio, pois estamos fornecendo as entidades diretamente
                        partial_entities
                    )
                    
                    return result
            
            elif "amount" not in partial_entities:
                # Tenta extrair um valor monetário
                try:
                    # Padroniza o formato (substitui vírgula por ponto)
                    amount_str = message_text.strip().replace(',', '.')
                    
                    # Remove "R$" ou outros caracteres não numéricos
                    amount_str = re.sub(r'[^\d.]', '', amount_str)
                    
                    amount = float(amount_str)
                    
                    # Atualiza as entidades parciais
                    partial_entities["amount"] = amount
                    
                    # Obtém o contato para processar o comando
                    contact = await self.whatsapp_contact_usecases.get_contact_by_phone(phone_number)
                    
                    # Limpa o contexto de confirmação
                    await self.session_manager.update_session(
                        phone_number,
                        {"context": {}}
                    )
                    
                    # Processa o comando com as entidades atualizadas
                    result = await self.nlp_usecases.process_command_with_entities(
                        contact.user_id,
                        "",  # Comando vazio, pois estamos fornecendo as entidades diretamente
                        partial_entities
                    )
                    
                    return result
                except ValueError:
                    # Não conseguiu extrair um valor
                    return {
                        "status": "confirmation",
                        "message": "Por favor, informe um valor numérico válido (ex: 50.00)."
                    }
            
        # Se chegou aqui, não foi possível processar a confirmação
        # Limpa o contexto de confirmação
        await self.session_manager.update_session(
            phone_number,
            {"context": {}}
        )
        
        return {
            "status": "error",
            "message": "Não consegui processar sua resposta. Por favor, tente fazer sua solicitação novamente."
        }
    
    async def _handle_help_command(
        self,
        phone_number: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manipula o comando de ajuda.
        
        Args:
            phone_number: Número de telefone do contato
            session: Sessão atual do usuário
            
        Returns:
            Mensagem de ajuda
        """
        help_message = """
📱 *Bem-vindo ao Financial Tracker via WhatsApp!*

Aqui estão alguns exemplos de comandos que você pode usar:

📝 *Registrar Transações*
- "_adicionar despesa de R$ 50 em Alimentação_"
- "_registrar receita de R$ 2000 como Salário_"
- "_adicionar despesa recorrente de R$ 99,90 em Assinaturas_"
- "_registrar gasto de 600 reais em 6 parcelas_"

📊 *Consultar Dados*
- "_mostrar saldo atual_"
- "_listar despesas de janeiro_"
- "_listar transações desta semana_"
- "_ver despesas recorrentes_"
- "_mostrar parcelas_"

🔄 *Gerenciar Transações*
- "_excluir transação id abc123_"
- "_atualizar transação id abc123 valor para 75,50_"

📋 *Categorias*
- "_listar categorias_"
- "_adicionar categoria Educação tipo despesa_"

⚙️ *Comandos Especiais*
- "_ajuda_" - mostra este menu
- "_limpar_" - limpa o histórico da conversa
- "_reiniciar_" - reinicia a conversa

Escreva seus comandos naturalmente, como se estivesse conversando com um assistente financeiro! 😊
"""
        
        return {
            "status": "success",
            "message": help_message
        }
    
    async def _handle_clear_command(
        self,
        phone_number: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manipula o comando para limpar o histórico.
        
        Args:
            phone_number: Número de telefone do contato
            session: Sessão atual do usuário
            
        Returns:
            Confirmação de limpeza
        """
        # Limpa o histórico de mensagens
        await self.session_manager.update_session(
            phone_number,
            {"history": []}
        )
        
        return {
            "status": "success",
            "message": "🧹 Histórico da conversa limpo com sucesso!"
        }
    
    async def _handle_restart_command(
        self,
        phone_number: str,
        session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manipula o comando para reiniciar a conversa.
        
        Args:
            phone_number: Número de telefone do contato
            session: Sessão atual do usuário
            
        Returns:
            Mensagem de boas-vindas para a nova conversa
        """
        # Preserva apenas o ID do usuário
        user_id = session.get("user_id")
        
        # Cria uma nova sessão
        await self.session_manager.create_session(phone_number)
        
        # Restaura o ID do usuário
        if user_id:
            await self.session_manager.update_session(
                phone_number,
                {"user_id": user_id}
            )
        
        # Mensagem de boas-vindas
        welcome_message = """
🔄 *Conversa reiniciada!*

Estou pronto para ajudar você a gerenciar suas finanças novamente. 
Digite "_ajuda_" para ver os comandos disponíveis.
"""
        
        return {
            "status": "success",
            "message": welcome_message
        }
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """
        Valida o formato do número de telefone.
        
        Args:
            phone_number: Número de telefone a ser validado
            
        Returns:
            True se o número for válido, False caso contrário
        """
        # Remove caracteres não numéricos exceto o símbolo +
        clean_number = re.sub(r'[^\d+]', '', phone_number)
        
        # Verifica se tem pelo menos 10 dígitos (mínimo para um número de telefone)
        if len(clean_number.lstrip('+')) < 10:
            return False
        
        # Aceita números com ou sem o prefixo +
        if clean_number.startswith('+'):
            # Formato internacional (começando com +)
            return bool(re.match(r'^\+\d{10,15}$', clean_number))
        else:
            # Formato local (sem +)
            return bool(re.match(r'^\d{10,15}$', clean_number))