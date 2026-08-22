"""Orquestração dos casos de uso de Task. Sem ORM, sem regra, sem try/except."""
from flask import jsonify, request

from src.middlewares.validators import filtros_de_busca, validar_task


class TaskController:
    def __init__(self, task_service):
        self._tasks = task_service

    def listar(self):
        return jsonify(self._tasks.listar()), 200

    def obter(self, task_id):
        return jsonify(self._tasks.obter(task_id)), 200

    def buscar(self):
        return jsonify(self._tasks.buscar(filtros_de_busca(request.args))), 200

    def estatisticas(self):
        return jsonify(self._tasks.estatisticas()), 200

    def criar(self):
        dados = validar_task(request.get_json(silent=True))
        return jsonify(self._tasks.criar(dados)), 201

    def atualizar(self, task_id):
        dados = validar_task(request.get_json(silent=True), parcial=True)
        return jsonify(self._tasks.atualizar(task_id, dados)), 200

    def deletar(self, task_id):
        self._tasks.deletar(task_id)
        return jsonify({"message": "Task deletada com sucesso"}), 200
