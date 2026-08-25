"""Mapeamento HTTP -> controller de Categoria. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller, require_auth):
    bp = Blueprint("categories", __name__, url_prefix="/categories")
    # Aberta: taxonomia é leitura pública, como o catálogo.
    bp.add_url_rule("", "get_categories", controller.listar, methods=["GET"])
    # Sensíveis: escrita na taxonomia é operação administrativa.
    bp.add_url_rule("", "create_category", require_auth(controller.criar), methods=["POST"])
    bp.add_url_rule(
        "/<int:cat_id>", "update_category", require_auth(controller.atualizar), methods=["PUT"]
    )
    bp.add_url_rule(
        "/<int:cat_id>", "delete_category", require_auth(controller.deletar), methods=["DELETE"]
    )
    return bp
