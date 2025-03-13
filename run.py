# run.py
import os
import sys
import asyncio
import uvicorn
import logging
from pathlib import Path

# Configura logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

# Adiciona o diretório raiz ao path do Python
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from config import settings
from src.infrastructure.database.mongodb.connection import MongoDBConnection
from src.application.usecases.category_usecases import CategoryUseCases
from src.infrastructure.database.repositories.mongodb_category_repository import MongoDBCategoryRepository


async def init_db():
    """Inicializa o banco de dados."""
    try:
        print("Inicializando banco de dados...")
        connection = MongoDBConnection()
        await connection.create_indexes()
        
        # Inicializa categorias padrão
        category_repository = MongoDBCategoryRepository()
        category_usecases = CategoryUseCases(category_repository)
        await category_usecases.initialize_default_categories()
        
        print("Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        raise


def init_app():
    """Inicializa a aplicação."""
    # Executa a inicialização do banco de dados
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(init_db())
    except:
        print("Falha na inicialização do banco de dados.")


if __name__ == "__main__":
    try:
        # Inicializa a aplicação
        init_app()
        
        # Inicia o servidor
        print(f"Iniciando servidor na porta {settings.PORT}...")
        uvicorn.run(
            "src.interfaces.api.app:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level="debug"  # Adicione isso para ter mais detalhes de log
        )
    except KeyboardInterrupt:
        print("Servidor encerrado pelo usuário.")
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")