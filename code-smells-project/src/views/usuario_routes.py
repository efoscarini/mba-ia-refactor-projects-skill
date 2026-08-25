"""Mapeamento HTTP → controller de Usuário. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("usuarios", __name__)
    # Sensíveis: expõem a base de usuários (era aqui que vazava a senha).
    bp.add_url_rule("/usuarios", "listar_usuarios", require_auth(controller.listar), methods=["GET"])
    bp.add_url_rule(
        "/usuarios/<int:id>", "buscar_usuario", require_auth(controller.obter), methods=["GET"]
    )
    # Abertas: auto-serviço — o próprio autor se identifica.
    bp.add_url_rule("/usuarios", "criar_usuario", controller.criar, methods=["POST"])
    bp.add_url_rule("/login", "login", controller.login, methods=["POST"])
    return bp
