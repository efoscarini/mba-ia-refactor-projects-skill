"""Mapeamento HTTP -> controller de Relatórios. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("reports", __name__, url_prefix="/reports")
    bp.add_url_rule("/summary", "summary_report", controller.resumo, methods=["GET"])
    bp.add_url_rule("/user/<int:user_id>", "user_report", controller.por_usuario, methods=["GET"])
    return bp
