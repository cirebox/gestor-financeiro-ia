# src/infrastructure/nlp/whatsapp_interaction_manager.py
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
from concurrent.futures import ThreadPoolExecutor

import openai
from config import settings


class WhatsAppInteractionManager:
    """
    Gerencia as interações de múltiplos usuários de WhatsApp com processamento assíncrono.
    """
    
    def __init__(self, nlp_middleware, max_workers=10):
        """
        Inicializa o gerenciador de interações de WhatsApp.
        
        Args:
            nlp_middleware: Middleware de processamento NLP para WhatsApp
            max_workers: Número máximo de threads simultâneas
        """
        self.nlp_middleware = nlp_middleware
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.user_conversations = {}
    
    async def process_message(self, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Processa uma mensagem de WhatsApp de forma assíncrona para um usuário específico.
        
        Args:
            phone_number: Número de telefone do usuário (no formato 552111111111111@c.us)
            message: Mensagem enviada pelo usuário
            
        Returns:
            Resultado do processamento da mensagem
        """
        # Extrai o número de telefone sem o @c.us
        clean_phone_number = phone_number.split('@')[0]
        
        # Verifica se já existe uma conversa para este usuário
        if clean_phone_number not in self.user_conversations:
            # Cria uma nova fila de conversa para o usuário
            self.user_conversations[clean_phone_number] = asyncio.Queue()
        
        # Coloca a mensagem na fila do usuário
        await self.user_conversations[clean_phone_number].put(message)
        
        # Processa as mensagens em sequência para este usuário
        return await self._process_user_messages(clean_phone_number)
    
    async def _process_user_messages(self, phone_number: str) -> Dict[str, Any]:
        """
        Processa todas as mensagens na fila de um usuário sequencialmente.
        
        Args:
            phone_number: Número de telefone do usuário
            
        Returns:
            Resultado do processamento da última mensagem
        """
        conversation_queue = self.user_conversations[phone_number]
        
        # Processamento sequencial das mensagens da fila
        result = None
        while not conversation_queue.empty():
            message = await conversation_queue.get()
            
            try:
                # Processa a mensagem usando o middleware NLP
                result = await self.nlp_middleware.process_whatsapp_message(phone_number, message)
                
                # Se for um comando de confirmação, mantém a mensagem na fila
                if result.get('status') == 'confirmation':
                    await conversation_queue.put(message)
                    break
                
            except Exception as e:
                # Trata erros no processamento da mensagem
                result = {
                    'status': 'error',
                    'message': f'Erro ao processar mensagem: {str(e)}'
                }
            
            # Marca a tarefa como concluída
            conversation_queue.task_done()
        
        return result
    
    def stop(self):
        """
        Encerra o gerenciador de interações.
        """
        self.executor.shutdown(wait=False)


# Função auxiliar para criar o gerenciador de interações como singleton
_interaction_manager = None

def get_whatsapp_interaction_manager(nlp_middleware):
    """
    Obtém uma instância singleton do gerenciador de interações de WhatsApp.
    
    Args:
        nlp_middleware: Middleware de processamento NLP para WhatsApp
        
    Returns:
        Instância do WhatsAppInteractionManager
    """
    global _interaction_manager
    if _interaction_manager is None:
        _interaction_manager = WhatsAppInteractionManager(nlp_middleware)
    return _interaction_manager