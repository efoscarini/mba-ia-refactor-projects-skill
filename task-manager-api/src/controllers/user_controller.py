"""Orquestração dos casos de uso de Usuário e login."""
from flask import jsonify, request

from src.middlewares.validators import validar_login, validar_usuario


class UserController:
    def __init__(self, user_service):
        self._users = user_service

    def listar(self):
        return jsonify(self._users.listar()), 200

    def obter(self, user_id):
        return jsonify(self._users.obter(user_id)), 200

    def tasks(self, user_id):
        return jsonify(self._users.tasks_do_usuario(user_id)), 200

    def criar(self):
        dados = validar_usuario(request.get_json(silent=True))
        return jsonify(self._users.criar(dados)), 201

    def atualizar(self, user_id):
        dados = validar_usuario(request.get_json(silent=True), parcial=True)
        return jsonify(self._users.atualizar(user_id, dados)), 200

    def deletar(self, user_id):
        self._users.deletar(user_id)
        return jsonify({"message": "Usuário deletado com sucesso"}), 200

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        return jsonify(self._users.autenticar(**credenciais)), 200
