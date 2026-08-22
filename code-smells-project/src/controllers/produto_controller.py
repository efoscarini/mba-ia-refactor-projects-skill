"""Orquestração dos casos de uso de Produto.

Sem SQL, sem regra de negócio e sem `try/except`: o erro sobe para o error handler.
"""
from flask import jsonify, request

from src.middlewares.validators import validar_filtros_produto, validar_produto


class ProdutoController:
    def __init__(self, produto_model):
        self._produtos = produto_model

    def listar(self):
        return jsonify({"dados": self._produtos.listar(), "sucesso": True}), 200

    def buscar(self):
        filtros = validar_filtros_produto(request.args)
        resultados = self._produtos.buscar(**filtros)
        return jsonify({"dados": resultados, "total": len(resultados), "sucesso": True}), 200

    def obter(self, id):
        produto = self._produtos.obter_ou_falhar(id)
        return jsonify({"dados": produto, "sucesso": True}), 200

    def criar(self):
        dados = validar_produto(request.get_json(silent=True))
        produto_id = self._produtos.criar(**dados)
        return jsonify({
            "dados": {"id": produto_id},
            "sucesso": True,
            "mensagem": "Produto criado",
        }), 201

    def atualizar(self, id):
        self._produtos.obter_ou_falhar(id)
        dados = validar_produto(request.get_json(silent=True))
        self._produtos.atualizar(id, **dados)
        return jsonify({"sucesso": True, "mensagem": "Produto atualizado"}), 200

    def deletar(self, id):
        self._produtos.obter_ou_falhar(id)
        self._produtos.deletar(id)
        return jsonify({"sucesso": True, "mensagem": "Produto deletado"}), 200
