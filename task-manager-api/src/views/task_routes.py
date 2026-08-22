"""Mapeamento HTTP -> controller de Task. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("tasks", __name__, url_prefix="/tasks")
    bp.add_url_rule("", "get_tasks", controller.listar, methods=["GET"])
    bp.add_url_rule("", "create_task", controller.criar, methods=["POST"])
    bp.add_url_rule("/search", "search_tasks", controller.buscar, methods=["GET"])
    bp.add_url_rule("/stats", "task_stats", controller.estatisticas, methods=["GET"])
    bp.add_url_rule("/<int:task_id>", "get_task", controller.obter, methods=["GET"])
    bp.add_url_rule("/<int:task_id>", "update_task", controller.atualizar, methods=["PUT"])
    bp.add_url_rule("/<int:task_id>", "delete_task", controller.deletar, methods=["DELETE"])
    return bp
