"""Mapeamento HTTP → controller de infraestrutura. Sem lógica."""
from flask import Blueprint


def criar_blueprint(controller):
    bp = Blueprint("system", __name__)
    bp.add_url_rule("/", "index", controller.index, methods=["GET"])
    bp.add_url_rule("/health", "health_check", controller.health, methods=["GET"])
    return bp
