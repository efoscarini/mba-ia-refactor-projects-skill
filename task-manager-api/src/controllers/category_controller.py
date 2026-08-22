"""Orquestração dos casos de uso de Categoria."""
from flask import jsonify, request

from src.middlewares.validators import validar_categoria


class CategoryController:
    def __init__(self, category_service):
        self._categories = category_service

    def listar(self):
        return jsonify(self._categories.listar()), 200

    def criar(self):
        dados = validar_categoria(request.get_json(silent=True))
        return jsonify(self._categories.criar(dados)), 201

    def atualizar(self, cat_id):
        dados = validar_categoria(request.get_json(silent=True), parcial=True)
        return jsonify(self._categories.atualizar(cat_id, dados)), 200

    def deletar(self, cat_id):
        self._categories.deletar(cat_id)
        return jsonify({"message": "Categoria deletada"}), 200
