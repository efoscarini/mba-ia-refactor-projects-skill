"""Mapeamento HTTP → controller de Produto. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("produtos", __name__, url_prefix="/produtos")
    # Abertas: catálogo é leitura pública.
    bp.add_url_rule("", "listar_produtos", controller.listar, methods=["GET"])
    bp.add_url_rule("/busca", "buscar_produtos", controller.buscar, methods=["GET"])
    bp.add_url_rule("/<int:id>", "buscar_produto", controller.obter, methods=["GET"])
    # Sensíveis: escrita no catálogo é operação administrativa.
    bp.add_url_rule("", "criar_produto", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "/<int:id>", "atualizar_produto", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/<int:id>", "deletar_produto", require_auth(controller.deletar), methods=["DELETE"]
    )
    return bp
