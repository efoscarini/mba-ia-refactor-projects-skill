"""Mapeamento HTTP → controller de Pedido. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")
    # Todas sensíveis: pedido é dado de usuário. `criar` recebe `usuario_id` no
    # corpo sem provar quem chama — escreve registro de terceiro.
    bp.add_url_rule("", "criar_pedido", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "", "listar_todos_pedidos", require_auth(controller.listar_todos), methods=["GET"]
    )
    bp.add_url_rule("/usuario/<int:usuario_id>", "listar_pedidos_usuario",
                    require_auth(controller.listar_por_usuario), methods=["GET"])
    bp.add_url_rule("/<int:pedido_id>/status", "atualizar_status_pedido",
                    require_auth(controller.atualizar_status), methods=["PUT"])
    return bp
