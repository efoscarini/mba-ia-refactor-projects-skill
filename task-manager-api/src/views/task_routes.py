"""Mapeamento HTTP -> controller de Task. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("tasks", __name__, url_prefix="/tasks")
    # Todas sensíveis: task tem `user_id` — listar, buscar e agregar expõem
    # dado de outro usuário; escrever e apagar mexem em registro de terceiro.
    bp.add_url_rule("", "get_tasks", require_auth(controller.listar), methods=["GET"])
    bp.add_url_rule("", "create_task", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule("/search", "search_tasks", require_auth(controller.buscar), methods=["GET"])
    bp.add_url_rule(
        "/stats", "task_stats", require_auth(controller.estatisticas), methods=["GET"]
    )
    bp.add_url_rule(
        "/<int:task_id>", "get_task", require_auth(controller.obter), methods=["GET"]
    )
    bp.add_url_rule(
        "/<int:task_id>", "update_task", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/<int:task_id>", "delete_task", require_auth(controller.deletar), methods=["DELETE"]
    )
    return bp
