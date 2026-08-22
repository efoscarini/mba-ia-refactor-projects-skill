"""Orquestração dos casos de uso de Pedido."""
from flask import jsonify, request

from src.middlewares.validators import validar_pedido, validar_status_pedido


class PedidoController:
    def __init__(self, pedido_service):
        self._pedidos = pedido_service

    def criar(self):
        dados = validar_pedido(request.get_json(silent=True))
        resultado = self._pedidos.criar(**dados)
        return jsonify({
            "dados": resultado,
            "sucesso": True,
            "mensagem": "Pedido criado com sucesso",
        }), 201

    def listar_todos(self):
        return jsonify({"dados": self._pedidos.listar_todos(), "sucesso": True}), 200

    def listar_por_usuario(self, usuario_id):
        pedidos = self._pedidos.listar_por_usuario(usuario_id)
        return jsonify({"dados": pedidos, "sucesso": True}), 200

    def atualizar_status(self, pedido_id):
        status = validar_status_pedido(request.get_json(silent=True))
        self._pedidos.atualizar_status(pedido_id, status)
        return jsonify({"sucesso": True, "mensagem": "Status atualizado"}), 200
