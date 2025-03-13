# src/infrastructure/whatsapp/session_manager.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import json
import asyncio
import os

class SessionManager:
    """Gerenciador de sessões para integração com WhatsApp."""
    
    # Tempo de expiração da sessão em minutos
    SESSION_EXPIRY_MINUTES = 60
    
    # Número máximo de mensagens para manter no histórico
    MAX_HISTORY_SIZE = 10
    
    # Diretório para armazenamento de sessões
    SESSIONS_DIR = "data/whatsapp_sessions"
    
    def __init__(self):
        """Inicializa o gerenciador de sessões."""
        # Cria o diretório para armazenamento de sessões se não existir
        os.makedirs(self.SESSIONS_DIR, exist_ok=True)
        
        # Cache de sessões em memória
        self.sessions = {}
        
        # Inicializa o limpador de sessões expiradas
        self._start_session_cleaner()
    
    def _get_session_file_path(self, phone_number: str) -> str:
        """
        Obtém o caminho do arquivo de sessão para um número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            Caminho completo do arquivo de sessão
        """
        # Remove caracteres inválidos para nome de arquivo
        safe_phone = phone_number.replace('+', '').replace(' ', '_')
        return os.path.join(self.SESSIONS_DIR, f"{safe_phone}.json")
    
    async def get_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Obtém a sessão para um número de telefone, carregando do cache ou do armazenamento.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            Sessão do usuário com histórico e estado
        """
        # Verifica se a sessão está no cache
        if phone_number in self.sessions:
            # Atualiza o timestamp de último acesso
            self.sessions[phone_number]["last_access"] = datetime.now().isoformat()
            return self.sessions[phone_number]
        
        # Carrega a sessão do arquivo, se existir
        session_file = self._get_session_file_path(phone_number)
        if os.path.exists(session_file):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    # Atualiza o timestamp de último acesso
                    session["last_access"] = datetime.now().isoformat()
                    # Salva no cache
                    self.sessions[phone_number] = session
                    return session
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erro ao carregar sessão para {phone_number}: {e}")
        
        # Se não existir, cria uma nova sessão
        return await self.create_session(phone_number)
    
    async def create_session(self, phone_number: str) -> Dict[str, Any]:
        """
        Cria uma nova sessão para um número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            
        Returns:
            Nova sessão do usuário
        """
        session = {
            "phone_number": phone_number,
            "user_id": None,  # Será preenchido quando o usuário for identificado
            "created_at": datetime.now().isoformat(),
            "last_access": datetime.now().isoformat(),
            "history": [],
            "context": {},
            "onboarding_complete": False,
            "onboarding_step": "welcome"
        }
        
        # Salva a sessão no cache
        self.sessions[phone_number] = session
        
        # Persiste a sessão
        await self.save_session(phone_number)
        
        return session
    
    async def update_session(self, phone_number: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Atualiza a sessão para um número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            data: Dados a serem atualizados na sessão
            
        Returns:
            Sessão atualizada
        """
        # Obtém a sessão atual
        session = await self.get_session(phone_number)
        
        # Atualiza os dados
        for key, value in data.items():
            session[key] = value
        
        # Atualiza o timestamp de último acesso
        session["last_access"] = datetime.now().isoformat()
        
        # Salva a sessão
        await self.save_session(phone_number)
        
        return session
    
    async def add_message_to_history(self, phone_number: str, role: str, content: str) -> None:
        """
        Adiciona uma mensagem ao histórico da sessão.
        
        Args:
            phone_number: Número de telefone do contato
            role: Papel da mensagem ('user' ou 'assistant')
            content: Conteúdo da mensagem
        """
        # Obtém a sessão atual
        session = await self.get_session(phone_number)
        
        # Adiciona a mensagem ao histórico
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        # Se o histórico não existir, cria um novo
        if "history" not in session:
            session["history"] = []
        
        # Adiciona a mensagem ao início do histórico (mais recente primeiro)
        session["history"].insert(0, message)
        
        # Limita o histórico ao tamanho máximo
        session["history"] = session["history"][:self.MAX_HISTORY_SIZE]
        
        # Atualiza o timestamp de último acesso
        session["last_access"] = datetime.now().isoformat()
        
        # Salva a sessão
        await self.save_session(phone_number)
    
    async def get_message_history(self, phone_number: str, limit: int = MAX_HISTORY_SIZE) -> List[Dict[str, Any]]:
        """
        Obtém o histórico de mensagens para um número de telefone.
        
        Args:
            phone_number: Número de telefone do contato
            limit: Número máximo de mensagens a retornar
            
        Returns:
            Lista de mensagens do histórico (mais recente primeiro)
        """
        # Obtém a sessão atual
        session = await self.get_session(phone_number)
        
        # Retorna o histórico limitado ao tamanho solicitado
        return session.get("history", [])[:limit]
    
    async def save_session(self, phone_number: str) -> None:
        """
        Salva a sessão para um número de telefone no armazenamento.
        
        Args:
            phone_number: Número de telefone do contato
        """
        # Verifica se a sessão está no cache
        if phone_number not in self.sessions:
            return
        
        # Obtém o caminho do arquivo de sessão
        session_file = self._get_session_file_path(phone_number)
        
        # Salva a sessão no arquivo
        try:
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions[phone_number], f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Erro ao salvar sessão para {phone_number}: {e}")
    
    async def clear_expired_sessions(self) -> None:
        """Remove sessões expiradas do cache e do armazenamento."""
        now = datetime.now()
        expired_phone_numbers = []
        
        # Identifica sessões expiradas no cache
        for phone_number, session in self.sessions.items():
            last_access = datetime.fromisoformat(session["last_access"])
            if (now - last_access) > timedelta(minutes=self.SESSION_EXPIRY_MINUTES):
                expired_phone_numbers.append(phone_number)
        
        # Remove sessões expiradas do cache
        for phone_number in expired_phone_numbers:
            del self.sessions[phone_number]
        
        # Identifica e remove arquivos de sessões expiradas
        for filename in os.listdir(self.SESSIONS_DIR):
            if not filename.endswith('.json'):
                continue
            
            filepath = os.path.join(self.SESSIONS_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    session = json.load(f)
                    last_access = datetime.fromisoformat(session["last_access"])
                    if (now - last_access) > timedelta(minutes=self.SESSION_EXPIRY_MINUTES):
                        os.remove(filepath)
            except (json.JSONDecodeError, IOError, KeyError) as e:
                print(f"Erro ao verificar sessão expirada {filename}: {e}")
    
    def _start_session_cleaner(self) -> None:
        """Inicia o limpador de sessões expiradas em segundo plano."""
        # Esta função seria mais adequada com um framework assíncrono como FastAPI,
        # mas por simplicidade, usamos uma abordagem mais básica
        async def cleaner_task():
            while True:
                await asyncio.sleep(3600)  # Executa a cada hora
                await self.clear_expired_sessions()
        
        # Em um ambiente real, você precisaria gerenciar este task adequadamente
        # dentro do ciclo de vida da aplicação
        asyncio.create_task(cleaner_task())