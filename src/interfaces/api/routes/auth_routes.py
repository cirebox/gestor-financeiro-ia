# src/interfaces/api/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from src.application.usecases.user_usecases import UserUseCases
from src.application.security.auth import get_current_active_user
from src.application.security.password_reset import PasswordResetService
from src.domain.entities.user import User
from src.interfaces.api.dependencies import get_user_usecases
from src.infrastructure.email.email_service import EmailService
from config import settings


router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    """Esquema de token de acesso."""
    
    access_token: str
    refresh_token: str
    token_type: str


class RefreshToken(BaseModel):
    """Esquema para refresh token."""
    
    refresh_token: str


class UserRegister(BaseModel):
    """Esquema para registro de usuário."""
    
    name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Esquema para resposta de usuário."""
    
    id: str
    name: str
    email: str
    is_active: bool
    is_admin: bool


class PasswordResetRequest(BaseModel):
    """Esquema para solicitação de redefinição de senha."""
    
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Esquema para confirmação de redefinição de senha."""
    
    token: str
    new_password: str = Field(..., min_length=8)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Registra um novo usuário.
    
    Args:
        user_data: Dados do usuário a ser registrado
        
    Returns:
        Dados do usuário registrado
    """
    try:
        user = await user_usecases.create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Obtém um token de acesso para um usuário.
    
    Args:
        form_data: Dados do formulário de login
        
    Returns:
        Token de acesso
    """
    authenticated, user = await user_usecases.authenticate_user(
        email=form_data.username,  # OAuth2 usa 'username', mas aqui é um email
        password=form_data.password
    )
    
    if not authenticated or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = await user_usecases.generate_tokens(user)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token_data: RefreshToken,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Atualiza o token de acesso usando um token de atualização.
    
    Args:
        refresh_token_data: Token de atualização
        
    Returns:
        Novo token de acesso
    """
    from src.application.security.token import verify_token
    
    user_id = verify_token(refresh_token_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        from uuid import UUID
        user = await user_usecases.get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        tokens = await user_usecases.generate_tokens(user)
        return tokens
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém os dados do usuário atualmente autenticado.
    
    Returns:
        Dados do usuário autenticado
    """
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Altera a senha do usuário atual.
    
    Args:
        current_password: Senha atual
        new_password: Nova senha
    """
    try:
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova senha deve ter pelo menos 8 caracteres"
            )
        
        success = await user_usecases.change_password(
            user_id=current_user.id,
            current_password=current_password,
            new_password=new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível alterar a senha"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/password-reset/request", status_code=status.HTTP_202_ACCEPTED)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Solicita a redefinição de senha para um usuário.
    
    Args:
        reset_request: Dados da solicitação de redefinição de senha
    """
    # Verifica se o usuário existe
    user = await user_usecases.get_user_by_email(reset_request.email)
    
    # Por segurança, não informamos se o email existe ou não
    if not user:
        return {"message": "Se o email existir, você receberá instruções para redefinir sua senha."}
    
    # Cria um token de redefinição de senha
    token = PasswordResetService.create_token(str(user.id))
    
    # Gera o link de redefinição de senha
    reset_link = f"{settings.BASE_URL}/reset-password?token={token.token}"
    
    # Envia o email
    email_service = EmailService()
    email_sent = email_service.send_password_reset_email(user.email, reset_link)
    
    if not email_sent and not settings.DEBUG:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Não foi possível enviar o email de redefinição de senha"
        )
    
    return {"message": "Se o email existir, você receberá instruções para redefinir sua senha."}


@router.post("/password-reset/confirm", status_code=status.HTTP_200_OK)
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Confirma a redefinição de senha para um usuário.
    
    Args:
        reset_confirm: Dados de confirmação de redefinição de senha
    """
    # Valida o tamanho da senha
    if len(reset_confirm.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A nova senha deve ter pelo menos 8 caracteres"
        )
    
    # Processa a redefinição de senha
    success = await PasswordResetService.process_password_reset(
        reset_confirm.token,
        reset_confirm.new_password,
        user_usecases.user_repository
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido ou expirado"
        )
    
    return {"message": "Senha redefinida com sucesso"}
# src/interfaces/api/routes/auth_routes.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field

from src.application.usecases.user_usecases import UserUseCases
from src.application.security.auth import get_current_active_user
from src.domain.entities.user import User
from src.interfaces.api.dependencies import get_user_usecases


router = APIRouter(prefix="/auth", tags=["authentication"])


class Token(BaseModel):
    """Esquema de token de acesso."""
    
    access_token: str
    refresh_token: str
    token_type: str


class RefreshToken(BaseModel):
    """Esquema para refresh token."""
    
    refresh_token: str


class UserRegister(BaseModel):
    """Esquema para registro de usuário."""
    
    name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """Esquema para resposta de usuário."""
    
    id: str
    name: str
    email: str
    is_active: bool
    is_admin: bool


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserRegister,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Registra um novo usuário.
    
    Args:
        user_data: Dados do usuário a ser registrado
        
    Returns:
        Dados do usuário registrado
    """
    try:
        user = await user_usecases.create_user(
            name=user_data.name,
            email=user_data.email,
            password=user_data.password
        )
        
        return UserResponse(
            id=str(user.id),
            name=user.name,
            email=user.email,
            is_active=user.is_active,
            is_admin=user.is_admin
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Obtém um token de acesso para um usuário.
    
    Args:
        form_data: Dados do formulário de login
        
    Returns:
        Token de acesso
    """
    authenticated, user = await user_usecases.authenticate_user(
        email=form_data.username,  # OAuth2 usa 'username', mas aqui é um email
        password=form_data.password
    )
    
    if not authenticated or not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    tokens = await user_usecases.generate_tokens(user)
    return tokens


@router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token_data: RefreshToken,
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Atualiza o token de acesso usando um token de atualização.
    
    Args:
        refresh_token_data: Token de atualização
        
    Returns:
        Novo token de acesso
    """
    from src.application.security.token import verify_token
    
    user_id = verify_token(refresh_token_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        from uuid import UUID
        user = await user_usecases.get_user_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Usuário inválido ou inativo",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        tokens = await user_usecases.generate_tokens(user)
        return tokens
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de atualização inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def read_users_me(
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtém os dados do usuário atualmente autenticado.
    
    Returns:
        Dados do usuário autenticado
    """
    return UserResponse(
        id=str(current_user.id),
        name=current_user.name,
        email=current_user.email,
        is_active=current_user.is_active,
        is_admin=current_user.is_admin
    )


@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    user_usecases: UserUseCases = Depends(get_user_usecases)
):
    """
    Altera a senha do usuário atual.
    
    Args:
        current_password: Senha atual
        new_password: Nova senha
    """
    try:
        if len(new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A nova senha deve ter pelo menos 8 caracteres"
            )
        
        success = await user_usecases.change_password(
            user_id=current_user.id,
            current_password=current_password,
            new_password=new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não foi possível alterar a senha"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )