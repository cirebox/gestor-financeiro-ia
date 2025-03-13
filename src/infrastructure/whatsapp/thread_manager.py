# src/infrastructure/whatsapp/thread_manager.py
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WhatsAppThreadManager:
    """
    Gerenciador de threads individuais para cada usuário do WhatsApp.
    Garante que mensagens do mesmo usuário sejam processadas em sequência
    para manter o contexto da conversa.
    """
    
    def __init__(self, cleanup_interval_minutes: int = 60):
        """
        Inicializa o gerenciador de threads.
        
        Args:
            cleanup_interval_minutes: Intervalo em minutos para limpar threads inativas
        """
        self.user_threads: Dict[str, asyncio.Queue] = {}
        self.last_activity: Dict[str, datetime] = {}
        self.cleanup_interval = timedelta(minutes=cleanup_interval_minutes)
        self.lock = asyncio.Lock()
        
        # Inicia a tarefa de limpeza
        self._start_cleanup_task()
    
    async def get_user_queue(self, phone_number: str) -> asyncio.Queue:
        """
        Obtém ou cria uma fila para o usuário.
        
        Args:
            phone_number: Número de telefone do usuário
            
        Returns:
            Fila assíncrona para o usuário
        """
        async with self.lock:
            if phone_number not in self.user_threads:
                self.user_threads[phone_number] = asyncio.Queue()
                self.last_activity[phone_number] = datetime.now()
            else:
                # Atualiza o horário da última atividade
                self.last_activity[phone_number] = datetime.now()
            
            return self.user_threads[phone_number]
    
    async def process_message(self, phone_number: str, processor_func, *args, **kwargs) -> Any:
        """
        Processa uma mensagem na thread específica do usuário.
        
        Args:
            phone_number: Número de telefone do usuário
            processor_func: Função que processa a mensagem
            *args, **kwargs: Argumentos para a função de processamento
            
        Returns:
            Resultado do processamento
        """
        # Obtém a fila do usuário
        queue = await self.get_user_queue(phone_number)
        
        # Cria uma futura para armazenar o resultado
        result_future = asyncio.Future()
        
        # Define a tarefa de processamento
        async def process_task():
            try:
                # Chama a função de processamento
                result = await processor_func(*args, **kwargs)
                # Define o resultado na futura
                result_future.set_result(result)
            except Exception as e:
                # Propaga a exceção para quem chamou
                result_future.set_exception(e)
        
        # Coloca a tarefa na fila
        await queue.put(process_task())
        
        # Processa a fila se ainda não estiver sendo processada
        if queue.qsize() == 1:
            asyncio.create_task(self._process_queue(phone_number, queue))
        
        # Aguarda e retorna o resultado
        return await result_future
    
    async def _process_queue(self, phone_number: str, queue: asyncio.Queue):
        """
        Processa tarefas na fila de um usuário.
        
        Args:
            phone_number: Número de telefone do usuário
            queue: Fila de tarefas do usuário
        """
        # Processa as tarefas enquanto houver na fila
        while not queue.empty():
            # Obtém a próxima tarefa
            task = await queue.get()
            
            try:
                # Executa a tarefa
                await task
            except Exception as e:
                logger.error(f"Erro ao processar tarefa para {phone_number}: {str(e)}")
            finally:
                # Marca a tarefa como concluída
                queue.task_done()
                
                # Atualiza o horário da última atividade
                self.last_activity[phone_number] = datetime.now()
    
    async def _cleanup_inactive_threads(self):
        """Remove threads inativas para economizar recursos."""
        try:
            async with self.lock:
                now = datetime.now()
                inactive_users = []
                
                # Identifica usuários inativos
                for phone_number, last_activity in self.last_activity.items():
                    if now - last_activity > self.cleanup_interval:
                        inactive_users.append(phone_number)
                
                # Remove as threads inativas
                for phone_number in inactive_users:
                    # Verifica se a fila está vazia antes de remover
                    if self.user_threads[phone_number].empty():
                        del self.user_threads[phone_number]
                        del self.last_activity[phone_number]
                        logger.info(f"Thread inativa removida para {phone_number}")
        except Exception as e:
            logger.error(f"Erro durante limpeza de threads: {str(e)}")
    
    def _start_cleanup_task(self):
        """Inicia a tarefa periódica de limpeza de threads inativas."""
        async def cleanup_loop():
            while True:
                await asyncio.sleep(self.cleanup_interval.total_seconds())
                await self._cleanup_inactive_threads()
        
        # Cria e inicia a tarefa de limpeza
        asyncio.create_task(cleanup_loop())


# Singleton para ser utilizado em toda a aplicação
_thread_manager: Optional[WhatsAppThreadManager] = None

def get_thread_manager() -> WhatsAppThreadManager:
    """
    Obtém a instância singleton do gerenciador de threads.
    
    Returns:
        Instância do WhatsAppThreadManager
    """
    global _thread_manager
    if _thread_manager is None:
        _thread_manager = WhatsAppThreadManager()
    return _thread_manager