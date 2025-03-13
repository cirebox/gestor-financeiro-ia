# src/interfaces/api/dependencies.py - Versão reorganizada

from fastapi import Depends, Header, HTTPException
from uuid import UUID

from src.application.usecases.transaction_usecases import TransactionUseCases
from src.application.usecases.category_usecases import CategoryUseCases
from src.application.usecases.analytics_usecases import AnalyticsUseCases
from src.application.usecases.nlp_usecases import NLPUseCases
from src.application.usecases.user_usecases import UserUseCases
from src.application.usecases.whatsapp_contact_usecases import WhatsAppContactUseCases

from src.infrastructure.database.repositories.mongodb_transaction_repository import MongoDBTransactionRepository
from src.infrastructure.database.repositories.mongodb_category_repository import MongoDBCategoryRepository
from src.infrastructure.database.repositories.mongodb_user_repository import MongoDBUserRepository
from src.infrastructure.database.repositories.mongodb_whatsapp_contact_repository import MongoDBWhatsAppContactRepository

from src.infrastructure.analytics.analytics_service import AnalyticsService
from src.infrastructure.nlp.nlp_service import NLPService
from src.infrastructure.nlp.llm_service import OpenAIService

from src.domain.entities.user import User
from config import settings


# Dependências para repositórios
def get_transaction_repository():
    """Obtém uma instância do repositório de transações."""
    return MongoDBTransactionRepository()


def get_category_repository():
    """Obtém uma instância do repositório de categorias."""
    return MongoDBCategoryRepository()


def get_user_repository():
    """Obtém uma instância do repositório de usuários."""
    return MongoDBUserRepository()


def get_whatsapp_contact_repository():
    """Obtém uma instância do repositório de contatos de WhatsApp."""
    return MongoDBWhatsAppContactRepository()


# Dependências para serviços
def get_analytics_service():
    """Obtém uma instância do serviço de análises."""
    return AnalyticsService()


def get_nlp_service():
    """Obtém uma instância do serviço de NLP."""
    # Se a configuração USE_LLM_FALLBACK está ativada, usa o serviço OpenAI como principal
    # Caso contrário, usa o serviço NLP padrão com fallback para OpenAI
    if hasattr(settings, 'USE_LLM_FALLBACK') and settings.USE_LLM_FALLBACK:
        return OpenAIService()
    return NLPService()


# Dependências para casos de uso
def get_transaction_usecases(
    transaction_repository=Depends(get_transaction_repository),
    category_repository=Depends(get_category_repository)
):
    """Obtém uma instância dos casos de uso de transações."""
    return TransactionUseCases(transaction_repository, category_repository)


def get_category_usecases(
    category_repository=Depends(get_category_repository)
):
    """Obtém uma instância dos casos de uso de categorias."""
    return CategoryUseCases(category_repository)


def get_user_usecases(
    user_repository=Depends(get_user_repository)
):
    """Obtém uma instância dos casos de uso de usuários."""
    return UserUseCases(user_repository)


def get_whatsapp_contact_usecases(
    whatsapp_contact_repository=Depends(get_whatsapp_contact_repository)
):
    """Obtém uma instância dos casos de uso de contatos de WhatsApp."""
    return WhatsAppContactUseCases(whatsapp_contact_repository)


def get_analytics_usecases(
    analytics_service=Depends(get_analytics_service),
    transaction_repository=Depends(get_transaction_repository)
):
    """Obtém uma instância dos casos de uso de análises."""
    return AnalyticsUseCases(analytics_service, transaction_repository)


def get_nlp_usecases(
    nlp_service=Depends(get_nlp_service),
    transaction_usecases=Depends(get_transaction_usecases),
    category_usecases=Depends(get_category_usecases),
    analytics_usecases=Depends(get_analytics_usecases)
):
    """Obtém uma instância dos casos de uso de NLP."""
    return NLPUseCases(nlp_service, transaction_usecases, category_usecases, analytics_usecases)


# Função auxiliar para obtenção de ID do usuário a partir do objeto User
def get_user_id_from_user(user: User) -> UUID:
    """
    Obtém o ID do usuário a partir do objeto User.
    
    Args:
        user: Objeto User
        
    Returns:
        ID do usuário
    """
    return user.id


# Este método é para compatibilidade com o código existente
# Será substituído pelo sistema de autenticação JWT
async def get_current_user_id(x_user_id: str = Header(...)):
    """
    Obtém o ID do usuário atual a partir do cabeçalho.
    
    Args:
        x_user_id: ID do usuário no cabeçalho X-User-ID
        
    Returns:
        UUID do usuário
    
    Raises:
        HTTPException: Se o ID do usuário for inválido
    """
    try:
        return UUID(x_user_id)
    except ValueError:
        raise HTTPException(status_code=401, detail="ID de usuário inválido")