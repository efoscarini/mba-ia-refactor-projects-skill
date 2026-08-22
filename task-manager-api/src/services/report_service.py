"""Relatórios agregados.

O `summary_report` original tinha 90 linhas dentro do handler de rota, com 14
queries de COUNT e mais uma por usuário.
"""
from datetime import timedelta

from src.config.constants import (
    HIGH_PRIORITY_THRESHOLD,
    PRIORITY_LABELS,
    RECENT_ACTIVITY_DAYS,
    STATUS_DONE,
    VALID_STATUSES,
)
from src.middlewares.errors import NotFoundError
from src.models.category import Category
from src.models.task import Task
from src.models.user import User
from src.utils.datetime_utils import utcnow
from src.utils.helpers import calculate_percentage


class ReportService:
    def resumo(self):
        tasks = Task.list_all()
        agora = utcnow()
        corte_recente = agora - timedelta(days=RECENT_ACTIVITY_DAYS)

        por_status = Task.count_by(Task.status)
        por_prioridade = Task.count_by(Task.priority)

        atrasadas = [task for task in tasks if task.is_overdue()]

        return {
            "generated_at": str(agora),
            "overview": {
                "total_tasks": Task.count(),
                "total_users": User.count(),
                "total_categories": Category.count(),
            },
            "tasks_by_status": {
                status: por_status.get(status, 0) for status in VALID_STATUSES
            },
            "tasks_by_priority": {
                rotulo: por_prioridade.get(prioridade, 0)
                for prioridade, rotulo in PRIORITY_LABELS.items()
            },
            "overdue": {
                "count": len(atrasadas),
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "due_date": str(task.due_date),
                        "days_overdue": (agora - task.due_date).days,
                    }
                    for task in atrasadas
                ],
            },
            "recent_activity": {
                "tasks_created_last_7_days": Task.count_created_since(corte_recente),
                "tasks_completed_last_7_days": Task.count_done_since(corte_recente),
            },
            "user_productivity": self._produtividade(tasks),
        }

    def por_usuario(self, user_id):
        user = User.get(user_id)
        if user is None:
            raise NotFoundError("Usuário não encontrado")

        tasks = Task.list_by_user(user_id)
        contagem = {status: 0 for status in VALID_STATUSES}
        atrasadas = 0
        alta_prioridade = 0

        for task in tasks:
            if task.status in contagem:
                contagem[task.status] += 1
            if task.priority <= HIGH_PRIORITY_THRESHOLD:
                alta_prioridade += 1
            if task.is_overdue():
                atrasadas += 1

        total = len(tasks)
        return {
            "user": {"id": user.id, "name": user.name, "email": user.email},
            "statistics": {
                "total_tasks": total,
                **contagem,
                "overdue": atrasadas,
                "high_priority": alta_prioridade,
                "completion_rate": calculate_percentage(contagem[STATUS_DONE], total),
            },
        }

    def _produtividade(self, tasks):
        """Agrupa em memória a partir da lista já carregada — sem query por usuário."""
        por_usuario = {}
        for task in tasks:
            if task.user_id is None:
                continue
            registro = por_usuario.setdefault(task.user_id, {"total": 0, "done": 0})
            registro["total"] += 1
            if task.status == STATUS_DONE:
                registro["done"] += 1

        resultado = []
        for user in User.list_all():
            registro = por_usuario.get(user.id, {"total": 0, "done": 0})
            resultado.append({
                "user_id": user.id,
                "user_name": user.name,
                "total_tasks": registro["total"],
                "completed_tasks": registro["done"],
                "completion_rate": calculate_percentage(registro["done"], registro["total"]),
            })
        return resultado
