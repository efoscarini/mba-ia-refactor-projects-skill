"""Mapeamento HTTP → controller de Relatório. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("relatorios", __name__, url_prefix="/relatorios")
    # Sensível: agrega faturamento bruto, líquido e desconto do negócio inteiro.
    bp.add_url_rule("/vendas", "relatorio_vendas", require_auth(controller.vendas), methods=["GET"])
    return bp
