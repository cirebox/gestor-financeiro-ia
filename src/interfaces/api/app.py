# src/interfaces/api/app.py
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import time
from typing import Callable
import os
from jose import JWTError, jwt

from src.domain.exceptions.domain_exceptions import CategoryNotFoundException
from src.interfaces.api.error_handlers import category_not_found_exception_handler
from src.interfaces.api.routes import transaction_routes, category_routes, nlp_routes, analytics_routes, user_routes, auth_routes


# Rate limiting middleware simples
class RateLimitMiddleware:
    def __init__(
        self,
        app: FastAPI,
        requests_limit: int = 100,
        window_seconds: int = 60
    ):
        self.app = app
        self.requests_limit = requests_limit
        self.window_seconds = window_seconds
        self.requests = {}  # Dicionário para armazenar contadores por IP
    
    async def __call__(self, request: Request, call_next: Callable):
        # Obtém o IP do cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Verifica se o IP já está no dicionário
        current_time = time.time()
        if client_ip in self.requests:
            # Limpa requisições antigas (fora da janela de tempo)
            self.requests[client_ip] = [
                req_time for req_time in self.requests[client_ip]
                if current_time - req_time < self.window_seconds
            ]
            
            # Verifica se o limite foi atingido
            if len(self.requests[client_ip]) >= self.requests_limit:
                return Response(
                    content="Rate limit exceeded. Try again later.",
                    status_code=429
                )
            
            # Adiciona o tempo atual às requisições
            self.requests[client_ip].append(current_time)
        else:
            # Inicializa o contador para o IP
            self.requests[client_ip] = [current_time]
        
        # Processa a requisição normalmente
        return await call_next(request)


def create_app() -> FastAPI:
    """Cria e configura a aplicação FastAPI."""
    app = FastAPI(
        title="Financial Tracker API",
        description="API para gerenciamento financeiro pessoal com processamento de linguagem natural",
        version="1.0.0",
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json"
    )
    
    # Adiciona middleware CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Em produção, especifique as origens permitidas
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Adiciona middleware de rate limiting
    rate_limit_middleware = RateLimitMiddleware(
        app=app,
        requests_limit=100,  # 100 requisições por minuto por IP
        window_seconds=60
    )
    app.middleware("http")(rate_limit_middleware)
    
    # Registra manipuladores de exceção
    app.add_exception_handler(CategoryNotFoundException, category_not_found_exception_handler)
    
    # Inclui rotas
    app.include_router(auth_routes.router, prefix="/api/v1")  # Novas rotas de autenticação
    app.include_router(transaction_routes.router, prefix="/api/v1")
    app.include_router(category_routes.router, prefix="/api/v1")
    app.include_router(nlp_routes.router, prefix="/api/v1")
    app.include_router(analytics_routes.router, prefix="/api/v1")
    app.include_router(user_routes.router, prefix="/api/v1")  
    
    @app.get("/", tags=["root"])
    async def root():
        """Endpoint raiz da API."""
        return {
            "message": "Financial Tracker API está funcionando!",
            "documentation": "/api/docs"
        }
    
    @app.get("/api/health", tags=["health"])
    async def health_check():
        """Endpoint de verificação de saúde da API."""
        return {
            "status": "healthy",
            "version": "1.0.0"
        }
    
    return app


app = create_app()