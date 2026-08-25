"""Mapeamento HTTP -> controller de Relatórios. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("reports", __name__, url_prefix="/reports")
    # Ambas sensíveis: agregam dados de toda a base / de um usuário específico.
    bp.add_url_rule("/summary", "summary_report", require_auth(controller.resumo), methods=["GET"])
    bp.add_url_rule(
        "/user/<int:user_id>", "user_report", require_auth(controller.por_usuario), methods=["GET"]
    )
    return bp
