# src/application/interfaces/repositories/whatsapp_contact_repository_interface.py
from abc import ABC, abstractmethod
from typing import List, Optional
from uuid import UUID

from src.domain.entities.whatsapp_contact import WhatsAppContact


class WhatsAppContactRepositoryInterface(ABC):
    """Interface para repositório de contatos de WhatsApp."""
    
    @abstractmethod
    async def add(self, contact: WhatsAppContact) -> WhatsAppContact:
        """
        Adiciona um novo contato.
        
        Args:
            contact: O contato a ser adicionado
            
        Returns:
            O contato adicionado com ID atualizado
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, contact_id: UUID) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo ID.
        
        Args:
            contact_id: ID do contato
            
        Returns:
            O contato encontrado ou None
        """
        pass
    
    @abstractmethod
    async def get_by_phone_number(self, phone_number: str) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            O contato encontrado ou None
        """
        pass
    
    @abstractmethod
    async def get_by_user_id(self, user_id: UUID) -> Optional[WhatsAppContact]:
        """
        Recupera um contato pelo ID do usuário.
        
        Args:
            user_id: ID do usuário
            
        Returns:
            O contato encontrado ou None
        """
        pass
    
    @abstractmethod
    async def update(self, contact_id: UUID, data: dict) -> Optional[WhatsAppContact]:
        """
        Atualiza um contato.
        
        Args:
            contact_id: ID do contato a ser atualizado
            data: Dados a serem atualizados
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def update_by_phone_number(self, phone_number: str, data: dict) -> Optional[WhatsAppContact]:
        """
        Atualiza um contato pelo número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            data: Dados a serem atualizados
            
        Returns:
            O contato atualizado ou None se não encontrado
        """
        pass
    
    @abstractmethod
    async def delete(self, contact_id: UUID) -> bool:
        """
        Remove um contato.
        
        Args:
            contact_id: ID do contato a ser removido
            
        Returns:
            True se removido com sucesso, False caso contrário
        """
        pass