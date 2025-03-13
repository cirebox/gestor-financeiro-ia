# src/application/security/auth.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from uuid import UUID

from src.application.security.token import verify_token
from src.application.usecases.user_usecases import UserUseCases
from src.domain.entities.user import User
from src.interfaces.api.dependencies import get_user_usecases

# Configuração do OAuth2
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_usecases: UserUseCases = Depends(get_user_usecases)
) -> User:
    """
    Obtém o usuário atual com base no token JWT.
    
    Args:
        token: Token JWT de autenticação
        user_usecases: Caso de uso para usuários
        
    Returns:
        Usuário autenticado
        
    Raises:
        HTTPException: Se o token for inválido ou o usuário não for encontrado
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciais inválidas",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verifica o token
    user_id = verify_token(token)
    if not user_id:
        raise credentials_exception
    
    # Obtém o usuário pelo ID
    try:
        user = await user_usecases.get_user_by_id(UUID(user_id))
        if user is None:
            raise credentials_exception
        
        # Verifica se o usuário está ativo
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Usuário inativo"
            )
            
        return user
    except ValueError:
        raise credentials_exception

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtém o usuário atual e verifica se está ativo.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Usuário ativo
        
    Raises:
        HTTPException: Se o usuário estiver inativo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    return current_user

async def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Obtém o usuário atual e verifica se é administrador.
    
    Args:
        current_user: Usuário atual
        
    Returns:
        Usuário administrador
        
    Raises:
        HTTPException: Se o usuário não for administrador
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso de administrador necessário"
        )
    return current_user