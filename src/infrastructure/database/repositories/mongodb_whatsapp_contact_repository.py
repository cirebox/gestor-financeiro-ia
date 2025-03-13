# src/infrastructure/database/repositories/mongodb_whatsapp_contact_repository.py
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from src.application.interfaces.repositories.whatsapp_contact_repository_interface import WhatsAppContactRepositoryInterface
from src.domain.entities.whatsapp_contact import WhatsAppContact
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.infrastructure.database.mongodb.models.whatsapp_contact_model import WhatsAppContactModel


class MongoDBWhatsAppContactRepository(WhatsAppContactRepositoryInterface):
    """Implementação do repositório de contatos de WhatsApp usando MongoDB."""
    
    def __init__(self):
        """Inicializa o repositório com a conexão MongoDB."""
        self.connection = MongoDBConnection()
        self.collection = self.connection.db.whatsapp_contacts
    
    async def add(self, contact: WhatsAppContact) -> WhatsAppContact:
        """
        Adiciona um novo contato.
        
        Args:
            contact: O contato a ser adicionado
            
        Returns:
            O contato adicionado com ID atualizado
        """
        contact_dict = WhatsAppContactModel.to_dict(contact)
        await self.collection.insert_one(contact_dict)
        return contact
    
    async def get_by_id(self, contact_id: UUID) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo ID.
        
        Args:
            contact_id: ID do contato
            
        Returns:
            O contato encontrado ou None
        """
        data = await self.collection.find_one({"_id": str(contact_id)})
        return WhatsAppContactModel.from_dict(data)
    
    async def get_by_phone_number(self, phone_number: str) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            O contato encontrado ou None
        """
        data = await self.collection.find_one({"phoneNumber": phone_number})
        return WhatsAppContactModel.from_dict(data)
    
    async def get_by_user_id(self, user_id: UUID) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo ID do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O contato encontrado ou None
        """
        data = await self.collection.find_one({"userId": str(user_id)})
        return WhatsAppContactModel.from_dict(data)
    
    async def update(self, contact_id: UUID, data: dict) -> Optional[WhatsAppContact]:
        """
        Atualiza um contato.
        
        Args:
            contact_id: ID do contato a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        # Converte as chaves para o formato do MongoDB
        update_data = {}
        key_map = {
            "phone_number": "phoneNumber",
            "user_id": "userId",
            "name": "name",
            "last_interaction": "lastInteraction",
            "onboarding_complete": "onboardingComplete",
            "onboarding_step": "onboardingStep"
        }
        
        for key, value in data.items():
            if key in key_map:
                update_data[key_map[key]] = value
            else:
                update_data[key] = value
                
        # Se atualizando o user_id, converte para string
        if "userId" in update_data and isinstance(update_data["userId"], UUID):
            update_data["userId"] = str(update_data["userId"])
        
        result = await self.collection.update_one(
            {"_id": str(contact_id)},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_by_id(contact_id)
    
    async def update_by_phone_number(self, phone_number: str, data: dict) -> Optional[WhatsAppContact]:
        """
        Atualiza um contato pelo número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            data: Dados a serem atualizados
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        # Converte as chaves para o formato do MongoDB
        update_data = {}
        key_map = {
            "phone_number": "phoneNumber",
            "user_id": "userId",
            "name": "name",
            "last_interaction": "lastInteraction",
            "onboarding_complete": "onboardingComplete",
            "onboarding_step": "onboardingStep"
        }
        
        for key, value in data.items():
            if key in key_map:
                update_data[key_map[key]] = value
            else:
                update_data[key] = value
                
        # Se atualizando o user_id, converte para string
        if "userId" in update_data and isinstance(update_data["userId"], UUID):
            update_data["userId"] = str(update_data["userId"])
        
        # Sempre atualiza last_interaction ao modificar o contato
        update_data["lastInteraction"] = datetime.now()
        
        result = await self.collection.update_one(
            {"phoneNumber": phone_number},
            {"$set": update_data}
        )
        
        if result.modified_count == 0:
            return None
        
        return await self.get_by_phone_number(phone_number)
    
    async def delete(self, contact_id: UUID) -> bool:
        """
        Remove um contato.
        
        Args:
            contact_id: ID do contato a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        result = await self.collection.delete_one({"_id": str(contact_id)})
        return result.deleted_count > 0
    
    async def initialize_indexes(self):
        """Inicializa os índices necessários."""
        # Índices para busca rápida
        await self.collection.create_index("phoneNumber", unique=True)
        await self.collection.create_index("userId", unique=True)