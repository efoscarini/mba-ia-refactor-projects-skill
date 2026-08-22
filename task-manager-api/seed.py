"""Script para popular o banco com dados iniciais.

As senhas de exemplo são gravadas com hash (`set_password`), não mais em MD5.
"""
import logging
from datetime import timedelta

from src.app import create_app
from src.infra.database import db
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import utcnow

logger = logging.getLogger(__name__)

USUARIOS = (
    ("João Silva", "joao@email.com", "1234", "admin"),
    ("Maria Santos", "maria@email.com", "abcd", "user"),
    ("Pedro Oliveira", "pedro@email.com", "pass", "manager"),
)

CATEGORIAS = (
    ("Backend", "Tarefas de backend", "#3498db"),
    ("Frontend", "Tarefas de frontend", "#2ecc71"),
    ("DevOps", "Tarefas de infraestrutura", "#e74c3c"),
    ("Bug", "Correção de bugs", "#e67e22"),
)

# (título, descrição, status, prioridade, índice do usuário, índice da categoria,
#  dias até o vencimento ou None, tags ou None)
TASKS = (
    ("Implementar autenticação JWT", "Adicionar autenticação real com JWT", "pending", 1, 0, 0, -3, None),
    ("Criar tela de login", "Tela de login responsiva", "in_progress", 2, 1, 1, 5, None),
    ("Configurar CI/CD", "Pipeline com GitHub Actions", "done", 2, 2, 2, None, "devops,ci,github"),
    ("Corrigir bug no filtro de busca", "Filtro não funciona com caracteres especiais", "pending", 1, 0, 3, -1, None),
    ("Adicionar paginação na API", "Endpoints retornam todos os registros", "pending", 3, 0, 0, 10, None),
    ("Escrever testes unitários", "Cobertura mínima de 80%", "pending", 2, 1, 0, None, None),
    ("Documentar API com Swagger", "Gerar documentação automática", "cancelled", 4, 2, 0, None, None),
    ("Refatorar models", "Melhorar organização dos models", "in_progress", 3, 1, 0, None, "refactor,tech-debt"),
    ("Configurar monitoramento", "Prometheus + Grafana", "pending", 4, 2, 2, 20, None),
    ("Melhorar validações de input", "Usar marshmallow ou pydantic", "pending", 3, 0, 0, None, "improvement,validation"),
)


def seed_data():
    app = create_app()
    with app.app_context():
        for modelo in (Task, User, Category):
            db.session.execute(db.delete(modelo))
        db.session.commit()

        usuarios = []
        for nome, email, senha, papel in USUARIOS:
            user = User()
            user.name, user.email, user.role = nome, email, papel
            user.set_password(senha)
            db.session.add(user)
            usuarios.append(user)

        categorias = []
        for nome, descricao, cor in CATEGORIAS:
            categoria = Category()
            categoria.name, categoria.description, categoria.color = nome, descricao, cor
            db.session.add(categoria)
            categorias.append(categoria)

        db.session.commit()

        agora = utcnow()
        for titulo, descricao, status, prioridade, iu, ic, dias, tags in TASKS:
            task = Task()
            task.title, task.description = titulo, descricao
            task.status, task.priority = status, prioridade
            task.user_id = usuarios[iu].id
            task.category_id = categorias[ic].id
            if dias is not None:
                task.due_date = agora + timedelta(days=dias)
            if tags:
                task.tags = tags
            db.session.add(task)

        db.session.commit()

        print("Seed concluído com sucesso!")
        print(f"  {User.count()} usuários")
        print(f"  {Category.count()} categorias")
        print(f"  {Task.count()} tasks")


if __name__ == "__main__":
    seed_data()
