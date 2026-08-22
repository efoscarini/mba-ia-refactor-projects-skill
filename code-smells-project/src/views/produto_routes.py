"""Mapeamento HTTP → controller de Produto. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("produtos", __name__, url_prefix="/produtos")
    bp.add_url_rule("", "listar_produtos", controller.listar, methods=["GET"])
    bp.add_url_rule("/busca", "buscar_produtos", controller.buscar, methods=["GET"])
    bp.add_url_rule("/<int:id>", "buscar_produto", controller.obter, methods=["GET"])
    bp.add_url_rule("", "criar_produto", controller.criar, methods=["POST"])
    bp.add_url_rule("/<int:id>", "atualizar_produto", controller.atualizar, methods=["PUT"])
    bp.add_url_rule("/<int:id>", "deletar_produto", controller.deletar, methods=["DELETE"])
    return bp
