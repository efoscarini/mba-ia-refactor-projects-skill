"""Orquestração dos casos de uso de Usuário e autenticação."""
from flask import jsonify, request

from src.middlewares.errors import UnauthorizedError
from src.middlewares.validators import validar_login, validar_usuario


class UsuarioController:
    def __init__(self, usuario_model, auth_service):
        self._usuarios = usuario_model
        self._auth = auth_service

    def listar(self):
        return jsonify({"dados": self._usuarios.listar(), "sucesso": True}), 200

    def obter(self, id):
        usuario = self._usuarios.obter_ou_falhar(id)
        return jsonify({"dados": usuario, "sucesso": True}), 200

    def criar(self):
        dados = validar_usuario(request.get_json(silent=True))
        usuario_id = self._usuarios.criar(**dados)
        return jsonify({"dados": {"id": usuario_id}, "sucesso": True}), 201

    def login(self):
        credenciais = validar_login(request.get_json(silent=True))
        usuario = self._usuarios.autenticar(**credenciais)
        if usuario is None:
            raise UnauthorizedError("Email ou senha inválidos")
        return jsonify({
            "dados": usuario,
            "sucesso": True,
            "mensagem": "Login OK",
            # Aditivo (RF-15): o original não emitia credencial. Os campos acima
            # seguem idênticos para quem já consome a rota.
            "token": self._auth.emitir(usuario["id"]),
        }), 200
