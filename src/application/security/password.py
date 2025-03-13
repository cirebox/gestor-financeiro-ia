# src/application/security/password.py
from passlib.context import CryptContext

# Configuração do contexto de criptografia
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifica se uma senha em texto plano corresponde a um hash.
    
    Args:
        plain_password: Senha em texto plano
        hashed_password: Hash da senha armazenada
        
    Returns:
        True se a senha corresponder ao hash, False caso contrário
    """
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """
    Gera um hash seguro para uma senha.
    
    Args:
        password: Senha em texto plano
        
    Returns:
        Hash da senha
    """
    return pwd_context.hash(password)