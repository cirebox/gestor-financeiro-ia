# src/application/security/token.py
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
import os
from uuid import UUID

# Configurações de segurança para tokens
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme_in_production_this_is_insecure")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7

def create_access_token(user_id: UUID, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um token de acesso JWT.
    
    Args:
        user_id: ID do usuário
        expires_delta: Tempo de expiração personalizado (opcional)
        
    Returns:
        Token JWT codificado
    """
    to_encode = {"sub": str(user_id)}
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(user_id: UUID) -> str:
    """
    Cria um token de atualização JWT com prazo de expiração mais longo.
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Token JWT de atualização codificado
    """
    to_encode = {"sub": str(user_id)}
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_token(token: str) -> Optional[str]:
    """
    Verifica um token JWT e retorna o ID do usuário.
    
    Args:
        token: Token JWT a ser verificado
        
    Returns:
        ID do usuário ou None se o token for inválido
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except jwt.JWTError:
        return None