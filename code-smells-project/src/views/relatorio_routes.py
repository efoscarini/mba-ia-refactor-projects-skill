"""Mapeamento HTTP → controller de Relatório. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")
    bp.add_url_rule("/vendas", "relatorio_vendas", controller.vendas, methods=["GET"])
    return bp
