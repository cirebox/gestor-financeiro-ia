# src/interfaces/api/bootstrap.py
"""
Módulo de inicialização da aplicação, responsável por configurar
as dependências e evitar problemas de importação circular.
"""

def setup_dependencies():
    """Configura as dependências da aplicação."""
    try:
        # Importamos aqui para evitar circular imports
        from src.interfaces.api.dependencies import get_user_usecases
        from src.application.security.auth import set_user_usecases_getter
        
        # Configura a função para obter os casos de uso de usuários
        set_user_usecases_getter(get_user_usecases)
    except ImportError as e:
        # Em alguns casos, pode ser que estejamos importando módulos em uma ordem inválida
        # durante o desenvolvimento. Permitimos falhar silenciosamente nesses casos.
        print(f"Aviso: Não foi possível configurar algumas dependências: {e}")
        print("Isso pode ser normal durante o desenvolvimento ou testes.")