"""Endpoints de infraestrutura: index e health check.

O health check original devolvia SECRET_KEY, caminho do banco e flag de debug no
corpo da resposta — nada disso é exposto aqui.
"""
from flask import jsonify

from src.config.constants import API_VERSION


class SystemController:
    def __init__(self, produto_model, usuario_model, pedido_model):
        self._produtos = produto_model
        self._usuarios = usuario_model
        self._pedidos = pedido_model

    def index(self):
        return jsonify({
            "mensagem": "Bem-vindo à API da Loja",
            "versao": API_VERSION,
            "endpoints": {
                "produtos": "/produtos",
                "usuarios": "/usuarios",
                "pedidos": "/pedidos",
                "login": "/login",
                "relatorios": "/relatorios/vendas",
                "health": "/health",
            },
        })

    def health(self):
        return jsonify({
            "status": "ok",
            "database": "connected",
            "counts": {
                "produtos": self._produtos.contar(),
                "usuarios": self._usuarios.contar(),
                "pedidos": self._pedidos.contar(),
            },
            "versao": API_VERSION,
        }), 200
