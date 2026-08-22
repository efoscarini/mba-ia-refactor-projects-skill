"""Casos de uso de Task."""
from src.config.constants import STATUS_FECHADOS, VALID_STATUSES
from src.middlewares.errors import NotFoundError
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import utcnow
from src.utils.helpers import calculate_percentage


class TaskService:
    def __init__(self, notification_service=None):
        self._notificacoes = notification_service

    # --- leitura ---

    def listar(self):
        """Enriquecimento em 3 queries no total (antes: 1 + 2N)."""
        tasks = Task.list_all()
        nomes_usuario = {u.id: u.name for u in User.list_all()}
        nomes_categoria = {c.id: c.name for c in Category.list_all()}

        resultado = []
        for task in tasks:
            dados = task.to_dict()
            dados["overdue"] = task.is_overdue()
            dados["user_name"] = nomes_usuario.get(task.user_id)
            dados["category_name"] = nomes_categoria.get(task.category_id)
            resultado.append(dados)
        return resultado

    def obter(self, task_id):
        task = self._obter_ou_falhar(task_id)
        dados = task.to_dict()
        dados["overdue"] = task.is_overdue()
        return dados

    def buscar(self, filtros):
        return [task.to_dict() for task in Task.search(**filtros)]

    def estatisticas(self):
        por_status = Task.count_by(Task.status)
        total = Task.count()
        atrasadas = sum(1 for task in Task.list_all() if task.is_overdue())
        concluidas = por_status.get("done", 0)

        estatisticas = {status: por_status.get(status, 0) for status in VALID_STATUSES}
        estatisticas["total"] = total
        estatisticas["overdue"] = atrasadas
        estatisticas["completion_rate"] = calculate_percentage(concluidas, total)
        return estatisticas

    # --- escrita ---

    def criar(self, dados):
        self._validar_relacionamentos(dados)

        task = Task()
        for campo, valor in dados.items():
            setattr(task, campo, valor)
        Task.save(task)

        self._notificar_atribuicao(task)
        return task.to_dict()

    def atualizar(self, task_id, dados):
        task = self._obter_ou_falhar(task_id)
        self._validar_relacionamentos(dados)

        for campo, valor in dados.items():
            setattr(task, campo, valor)
        task.updated_at = utcnow()
        Task.commit()
        return task.to_dict()

    def deletar(self, task_id):
        Task.delete(self._obter_ou_falhar(task_id))

    # --- apoio ---

    def _obter_ou_falhar(self, task_id):
        task = Task.get(task_id)
        if task is None:
            raise NotFoundError("Task não encontrada")
        return task

    def _validar_relacionamentos(self, dados):
        if dados.get("user_id") and User.get(dados["user_id"]) is None:
            raise NotFoundError("Usuário não encontrado")
        if dados.get("category_id") and Category.get(dados["category_id"]) is None:
            raise NotFoundError("Categoria não encontrada")

    def _notificar_atribuicao(self, task):
        if not (self._notificacoes and task.user_id):
            return
        user = User.get(task.user_id)
        if user and task.status not in STATUS_FECHADOS:
            self._notificacoes.task_atribuida(user, task)
