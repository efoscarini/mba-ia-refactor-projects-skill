"""Mapeamento HTTP -> controller de Usuário. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("users", __name__)
    # Sensível: lista todos os usuários da base.
    bp.add_url_rule("/users", "get_users", require_auth(controller.listar), methods=["GET"])
    # Sensíveis: leem e escrevem registro de terceiro.
    bp.add_url_rule(
        "/users/<int:user_id>", "get_user", require_auth(controller.obter), methods=["GET"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>", "update_user", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>", "delete_user", require_auth(controller.deletar), methods=["DELETE"]
    )
    bp.add_url_rule(
        "/users/<int:user_id>/tasks", "get_user_tasks",
        require_auth(controller.tasks), methods=["GET"],
    )
    # Abertas: auto-serviço — o próprio autor se identifica.
    bp.add_url_rule("/users", "create_user", controller.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
    return bp
