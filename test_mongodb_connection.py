# test_mongodb_connection.py
import asyncio
import sys
from pathlib import Path

# Adiciona o diretório raiz ao path do Python
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.infrastructure.database.mongodb.connection import MongoDBConnection
from config import settings


async def test_mongodb_connection():
    try:
        print(f"Testando conexão com o MongoDB...")
        print(f"Host: {settings.MONGODB_HOST}")
        print(f"Port: {settings.MONGODB_PORT}")
        print(f"Database: {settings.MONGODB_DB}")
        print(f"Username: {settings.MONGODB_USERNAME}")
        print(f"Password: {'*' * len(settings.MONGODB_PASSWORD) if settings.MONGODB_PASSWORD else 'Não informado'}")
        
        connection = MongoDBConnection()
        
        # Tenta listar as coleções para verificar a conexão
        collections = await connection.db.list_collection_names()
        print(f"Conexão bem-sucedida!")
        print(f"Coleções no banco de dados: {collections}")
        
        # Testa a criação de índices
        await connection.create_indexes()
        
        return True
    except Exception as e:
        print(f"Erro ao conectar ao MongoDB: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(test_mongodb_connection())