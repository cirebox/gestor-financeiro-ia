# src/infrastructure/database/mongodb/connection.py
import motor.motor_asyncio
from pymongo import ASCENDING
from typing import Optional

from config import settings


class MongoDBConnection:
    """Gerencia a conexão com o MongoDB."""
    
    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[motor.motor_asyncio.AsyncIOMotorClient] = None
    _db: Optional[motor.motor_asyncio.AsyncIOMotorDatabase] = None
    
    def __new__(cls):
        """Implementa o padrão Singleton."""
        if cls._instance is None:
            cls._instance = super(MongoDBConnection, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializa a conexão com o MongoDB."""
        # Conexão com autenticação
        if settings.MONGODB_USERNAME and settings.MONGODB_PASSWORD:
            uri = f"mongodb://{settings.MONGODB_USERNAME}:{settings.MONGODB_PASSWORD}@{settings.MONGODB_HOST}:{settings.MONGODB_PORT}/{settings.MONGODB_DB}?authSource=admin"
            self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        else:
            # Conexão sem autenticação (para desenvolvimento)
            self._client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)
        
        self._db = self._client[settings.MONGODB_DB]
    
    @property
    def db(self) -> motor.motor_asyncio.AsyncIOMotorDatabase:
        """Retorna a instância do banco de dados."""
        if self._db is None:
            self._initialize()
        return self._db
    
    @property
    def client(self) -> motor.motor_asyncio.AsyncIOMotorClient:
        """Retorna o cliente MongoDB."""
        if self._client is None:
            self._initialize()
        return self._client
    
    async def create_indexes(self):
        """Cria índices para melhorar a performance das consultas."""
        # Índices para transações
        await self.db.transactions.create_index([("userId", ASCENDING), ("date", ASCENDING)])
        await self.db.transactions.create_index([("category", ASCENDING)])
        
        # Índices para categorias
        await self.db.categories.create_index([("name", ASCENDING)], unique=True)
        
        # Índices para usuários
        await self.db.users.create_index([("email", ASCENDING)], unique=True)