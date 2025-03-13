# src/interfaces/api/app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.domain.exceptions.domain_exceptions import CategoryNotFoundException
from src.interfaces.api.error_handlers import category_not_found_exception_handler
from src.interfaces.api.routes import transaction_routes, category_routes, nlp_routes, analytics_routes, user_routes


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
    
    # Registra manipuladores de exceção
    app.add_exception_handler(CategoryNotFoundException, category_not_found_exception_handler)
    
    # Inclui rotas
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
    
    return app


app = create_app()