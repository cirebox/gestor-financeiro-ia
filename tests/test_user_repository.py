# test_user_repository.py
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Adiciona o diretório raiz ao path do Python
current_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(current_dir))

from src.domain.entities.user import User
from src.infrastructure.database.repositories.mongodb_user_repository import MongoDBUserRepository


async def test_user_repository():
    try:
        print("Testando repositório de usuários...")
        
        # Cria uma instância do repositório
        repo = MongoDBUserRepository()
        
        # Cria um usuário de teste
        test_user = User.create(
            name="Usuário de Teste",
            email=f"teste_{uuid4()}@exemplo.com"
        )
        
        # Adiciona o usuário
        print("Adicionando usuário...")
        added_user = await repo.add(test_user)
        print(f"Usuário adicionado: {added_user.name} (ID: {added_user.id})")
        
        # Recupera o usuário pelo ID
        print("Recuperando usuário pelo ID...")
        user_by_id = await repo.get_by_id(added_user.id)
        if user_by_id:
            print(f"Usuário encontrado: {user_by_id.name} (ID: {user_by_id.id})")
        else:
            print("Usuário não encontrado pelo ID.")
        
        # Recupera o usuário pelo email
        print("Recuperando usuário pelo email...")
        user_by_email = await repo.get_by_email(added_user.email)
        if user_by_email:
            print(f"Usuário encontrado: {user_by_email.name} (Email: {user_by_email.email})")
        else:
            print("Usuário não encontrado pelo email.")
        
        # Exclui o usuário
        print("Excluindo usuário...")
        deleted = await repo.delete(added_user.id)
        print(f"Usuário excluído: {deleted}")
        
        print("Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"Erro durante o teste: {e}")


if __name__ == "__main__":
    asyncio.run(test_user_repository())