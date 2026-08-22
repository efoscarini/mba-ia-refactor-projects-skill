"""Mapeamento HTTP -> controller de Categoria. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("categories", __name__, url_prefix="/categories")
    bp.add_url_rule("", "get_categories", controller.listar, methods=["GET"])
    bp.add_url_rule("", "create_category", controller.criar, methods=["POST"])
    bp.add_url_rule("/<int:cat_id>", "update_category", controller.atualizar, methods=["PUT"])
    bp.add_url_rule("/<int:cat_id>", "delete_category", controller.deletar, methods=["DELETE"])
    return bp
