# src/interfaces/cli/cli_app.py
import asyncio
import os
import sys
from uuid import UUID

# Adiciona o diretório raiz ao sys.path para importações relativas funcionarem
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))

from src.application.usecases.nlp_usecases import NLPUseCases
from src.application.usecases.transaction_usecases import TransactionUseCases
from src.application.usecases.category_usecases import CategoryUseCases
from src.application.usecases.analytics_usecases import AnalyticsUseCases
from src.infrastructure.database.repositories.mongodb_transaction_repository import MongoDBTransactionRepository
from src.infrastructure.database.repositories.mongodb_category_repository import MongoDBCategoryRepository
from src.infrastructure.analytics.analytics_service import AnalyticsService
from src.infrastructure.nlp.nlp_service import NLPService
from src.infrastructure.database.mongodb.connection import MongoDBConnection


class FinancialTrackerCLI:
    """Aplicação CLI para o Financial Tracker."""
    
    def __init__(self):
        """Inicializa a aplicação CLI."""
        # Repositórios
        self.transaction_repository = MongoDBTransactionRepository()
        self.category_repository = MongoDBCategoryRepository()
        
        # Serviços
        self.analytics_service = AnalyticsService()
        self.nlp_service = NLPService()
        
        # Casos de uso
        self.transaction_usecases = TransactionUseCases(self.transaction_repository, self.category_repository)
        self.category_usecases = CategoryUseCases(self.category_repository)
        self.analytics_usecases = AnalyticsUseCases(self.analytics_service, self.transaction_repository)
        
        # NLP
        self.nlp_usecases = NLPUseCases(
            self.nlp_service,
            self.transaction_usecases,
            self.category_usecases,
            self.analytics_usecases
        )
        
        # ID do usuário (para testes, usamos um ID fixo)
        self.user_id = UUID("00000000-0000-0000-0000-000000000001")
    
    async def initialize(self):
        """Inicializa as dependências da aplicação."""
        # Inicializa o banco de dados
        connection = MongoDBConnection()
        await connection.create_indexes()
        
        # Inicializa as categorias padrão
        await self.category_usecases.initialize_default_categories()
    
    async def run(self):
        """Executa o loop principal da aplicação CLI."""
        await self.initialize()
        
        print("=== Financial Tracker CLI ===")
        print("Digite 'ajuda' para ver os comandos disponíveis. Digite 'sair' para encerrar.")
        
        while True:
            try:
                command = input("\n> ")
                
                if command.lower() == "sair":
                    print("Encerrando a aplicação. Até mais!")
                    break
                
                result = await self.nlp_usecases.process_command(self.user_id, command)
                print(result["message"])
            except KeyboardInterrupt:
                print("\nEncerrando a aplicação. Até mais!")
                break
            except Exception as e:
                print(f"Erro: {str(e)}")


async def main():
    """Função principal da aplicação CLI."""
    app = FinancialTrackerCLI()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())