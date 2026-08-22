"""Casos de uso de Usuário e autenticação."""
from itsdangerous import URLSafeTimedSerializer

from src.middlewares.errors import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import format_date

TOKEN_SALT = "task-manager-auth"


class UserService:
    def __init__(self, settings):
        self._serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)

    # --- leitura ---

    def listar(self):
        """Contagem de tasks por usuário em 1 query agregada (antes: 1 por usuário)."""
        contagem = Task.count_by(Task.user_id)
        return [
            {**user.to_dict(), "task_count": contagem.get(user.id, 0)}
            for user in User.list_all()
        ]

    def obter(self, user_id):
        user = self._obter_ou_falhar(user_id)
        dados = user.to_dict()
        dados["tasks"] = [task.to_dict() for task in Task.list_by_user(user_id)]
        return dados

    def tasks_do_usuario(self, user_id):
        self._obter_ou_falhar(user_id)
        return [
            {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "status": task.status,
                "priority": task.priority,
                "created_at": str(task.created_at),
                "due_date": format_date(task.due_date),
                "overdue": task.is_overdue(),
            }
            for task in Task.list_by_user(user_id)
        ]

    # --- escrita ---

    def criar(self, dados):
        if User.get_by_email(dados["email"]) is not None:
            raise ConflictError("Email já cadastrado")

        user = User()
        user.name = dados["name"]
        user.email = dados["email"]
        user.set_password(dados["password"])
        user.role = dados.get("role", user.role)
        User.save(user)
        return user.to_dict()

    def atualizar(self, user_id, dados):
        user = self._obter_ou_falhar(user_id)

        if "email" in dados:
            existente = User.get_by_email(dados["email"])
            if existente is not None and existente.id != user_id:
                raise ConflictError("Email já cadastrado")
            user.email = dados["email"]

        if "name" in dados:
            user.name = dados["name"]
        if "password" in dados:
            user.set_password(dados["password"])
        if "role" in dados:
            user.role = dados["role"]
        if "active" in dados:
            user.active = dados["active"]

        User.commit()
        return user.to_dict()

    def deletar(self, user_id):
        user = self._obter_ou_falhar(user_id)
        for task in Task.list_by_user(user_id):
            Task.delete(task)
        User.delete(user)

    # --- autenticação ---

    def autenticar(self, email, password):
        user = User.get_by_email(email)
        if user is None or not user.check_password(password):
            raise UnauthorizedError("Credenciais inválidas")
        if not user.active:
            raise ForbiddenError("Usuário inativo")

        return {
            "message": "Login realizado com sucesso",
            "user": user.to_dict(),
            "token": self._serializer.dumps({"user_id": user.id}),
        }

    # --- apoio ---

    def _obter_ou_falhar(self, user_id):
        user = User.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")
        return user
