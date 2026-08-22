"""Mapeamento HTTP → controller de Pedido. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")
    bp.add_url_rule("", "criar_pedido", controller.criar, methods=["POST"])
    bp.add_url_rule("", "listar_todos_pedidos", controller.listar_todos, methods=["GET"])
    bp.add_url_rule("/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                    controller.listar_por_usuario, methods=["GET"])
    bp.add_url_rule("/<int:pedido_id>/status", "atualizar_status_pedido",
                    controller.atualizar_status, methods=["PUT"])
    return bp
