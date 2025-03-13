# src/application/usecases/whatsapp_contact_usecases.py
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from uuid import UUID

from src.application.interfaces.repositories.whatsapp_contact_repository_interface import WhatsAppContactRepositoryInterface
from src.domain.entities.whatsapp_contact import WhatsAppContact


class WhatsAppContactUseCases:
    """Casos de uso relacionados a contatos de WhatsApp."""
    
    def __init__(self, whatsapp_contact_repository: WhatsAppContactRepositoryInterface):
        """
        Inicializa os casos de uso de contato de WhatsApp.
        
        Args:
            whatsapp_contact_repository: Implementação do repositório de contatos de WhatsApp
        """
        self.whatsapp_contact_repository = whatsapp_contact_repository
    
    async def register_contact(self, phone_number: str, name: Optional[str] = None) -> WhatsAppContact:
        """
        Registra um novo contato de WhatsApp.
        
        Args:
            phone_number: Número de telefone do contato
            name: Nome do contato (opcional)
            
        Returns:
            O contato registrado
        """
        # Verifica se já existe um contato com o mesmo número
        existing_contact = await self.whatsapp_contact_repository.get_by_phone_number(phone_number)
        if existing_contact:
            # Atualiza last_interaction e retorna o contato existente
            await self.update_last_interaction(phone_number)
            return existing_contact
        
        # Cria um novo contato
        contact = WhatsAppContact.create(
            phone_number=phone_number,
            name=name
        )
        
        # Adiciona o contato ao repositório
        return await self.whatsapp_contact_repository.add(contact)
    
    async def get_contact_by_phone(self, phone_number: str) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            O contato encontrado ou None
        """
        contact = await self.whatsapp_contact_repository.get_by_phone_number(phone_number)
        if contact:
            # Atualiza last_interaction
            await self.update_last_interaction(phone_number)
        return contact
    
    async def get_contact_by_user_id(self, user_id: UUID) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo ID do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O contato encontrado ou None
        """
        return await self.whatsapp_contact_repository.get_by_user_id(user_id)
    
    async def update_last_interaction(self, phone_number: str) -> Optional[WhatsAppContact]:
        """
        Atualiza o timestamp da última interação de um contato.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        return await self.whatsapp_contact_repository.update_by_phone_number(
            phone_number=phone_number,
            data={"last_interaction": datetime.now()}
        )
    
    async def update_onboarding_status(self, phone_number: str, complete: bool, step: Optional[str] = None) -> Optional[WhatsAppContact]:
        """
        Atualiza o status de onboarding de um contato.
        
        Args:
            phone_number: Número de telefone do contato
            complete: Se o onboarding está completo
            step: Etapa atual do onboarding (opcional)
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        update_data = {"onboarding_complete": complete}
        if step:
            update_data["onboarding_step"] = step
            
        return await self.whatsapp_contact_repository.update_by_phone_number(
            phone_number=phone_number,
            data=update_data
        )
    
    async def update_contact_name(self, phone_number: str, name: str) -> Optional[WhatsAppContact]:
        """
        Atualiza o nome de um contato.
        
        Args:
            phone_number: Número de telefone do contato
            name: Novo nome
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        return await self.whatsapp_contact_repository.update_by_phone_number(
            phone_number=phone_number,
            data={"name": name}
        )
    
    async def handle_onboarding_step(self, phone_number: str, message: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Manipula uma etapa do processo de onboarding.
        
        Args:
            phone_number: Número de telefone do contato
            message: Mensagem enviada pelo contato
            
        Returns:
            Tupla (onboarding_complete, response_message, updated_data)
            - onboarding_complete: Se o onboarding foi concluído
            - response_message: Mensagem de resposta ao contato
            - updated_data: Dados atualizados do contato
        """
        contact = await self.get_contact_by_phone(phone_number)
        
        if not contact:
            # Se o contato não existir, registra e inicia o onboarding
            contact = await self.register_contact(phone_number)
            welcome_message = (
                "👋 *Olá! Bem-vindo ao Financial Tracker!*\n\n"
                "Eu sou seu assistente financeiro pessoal. Vou ajudar você a gerenciar suas finanças de forma simples e prática.\n\n"
                "Para começarmos, como posso chamar você?"
            )
            return False, welcome_message, {"onboarding_step": "name"}
        
        # Se o onboarding já estiver completo, retorna
        if contact.onboarding_complete:
            return True, "", {}
            
        current_step = contact.onboarding_step or "welcome"
        updated_data = {}
        
        if current_step == "welcome":
            # Inicia o processo de onboarding
            welcome_message = (
                "👋 *Olá! Bem-vindo ao Financial Tracker!*\n\n"
                "Eu sou seu assistente financeiro pessoal. Vou ajudar você a gerenciar suas finanças de forma simples e prática.\n\n"
                "Para começarmos, como posso chamar você?"
            )
            updated_data["onboarding_step"] = "name"
            return False, welcome_message, updated_data
            
        elif current_step == "name":
            # Salva o nome do usuário
            if len(message.strip()) < 2:
                return False, "Por favor, digite um nome válido.", {}
                
            name = message.strip()
            updated_data["name"] = name
            updated_data["onboarding_step"] = "introduction"
            
            intro_message = (
                f"🎉 *Prazer em conhecer você, {name}!*\n\n"
                f"Agora que nos conhecemos, deixa eu te contar rapidamente como posso te ajudar:\n\n"
                f"✅ Registrar suas despesas e receitas\n"
                f"✅ Categorizar suas transações\n"
                f"✅ Mostrar seu saldo atual\n"
                f"✅ Gerar relatórios financeiros\n"
                f"✅ Identificar seus padrões de gasto\n\n"
                f"Você pode me enviar mensagens como:\n\n"
                f"_\"Registrar gasto de 50 reais com almoço\"_\n"
                f"_\"Recebi 2000 de salário hoje\"_\n"
                f"_\"Qual meu saldo atual?\"_\n\n"
                f"Quer ver um exemplo prático de como registrar uma despesa?"
            )
            return False, intro_message, updated_data
            
        elif current_step == "introduction":
            # Mostra um exemplo prático
            updated_data["onboarding_step"] = "example"
            
            example_message = (
                "💡 *Exemplo prático:*\n\n"
                "Para registrar uma despesa, você pode dizer algo como:\n\n"
                "\"_Gastei 25 reais com transporte hoje_\"\n\n"
                "E eu vou organizar essa informação para você e confirmar o registro:\n\n"
                "✅ Despesa de R$ 25,00 em Transporte registrada com sucesso!\n\n"
                "Vamos tentar? Registre uma despesa ou receita real sua agora!"
            )
            return False, example_message, updated_data
            
        elif current_step == "example":
            # O usuário deve tentar registrar uma transação
            # Não validamos o conteúdo aqui, apenas marcamos como concluído
            # O NLP vai processar a mensagem normalmente
            updated_data["onboarding_step"] = "completed"
            updated_data["onboarding_complete"] = True
            
            completion_message = (
                "🎉 *Pronto! Você já sabe como usar o Financial Tracker!*\n\n"
                "A partir de agora, pode me enviar mensagens quando quiser para:\n\n"
                "📝 Registrar transações\n"
                "📊 Ver seu saldo e relatórios\n"
                "❓ Obter ajuda (basta digitar \"ajuda\")\n\n"
                "Estou aqui para facilitar o controle das suas finanças. Conte comigo!"
            )
            return True, completion_message, updated_data
            
        # Default - finaliza o onboarding
        updated_data["onboarding_step"] = "completed"
        updated_data["onboarding_complete"] = True
        return True, "Onboarding concluído!", updated_data