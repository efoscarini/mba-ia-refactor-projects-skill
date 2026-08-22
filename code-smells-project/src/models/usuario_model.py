"""Acesso a dados da entidade Usuário.

O hash de senha vive aqui e o campo `senha` nunca é serializado.
"""
from werkzeug.security import check_password_hash, generate_password_hash

from src.config.constants import TIPO_USUARIO_PADRAO
from src.middlewares.errors import NotFoundError

# `senha` deliberadamente fora da lista: não sai da camada de dados
CAMPOS_PUBLICOS = ("id", "nome", "email", "tipo", "criado_em")


def gerar_hash(senha):
    return generate_password_hash(senha)


def serializar(linha):
    return {campo: linha[campo] for campo in CAMPOS_PUBLICOS}


class UsuarioModel:
    def __init__(self, db):
        self._db = db

    def listar(self):
        linhas = self._db.consultar("SELECT * FROM usuarios")
        return [serializar(linha) for linha in linhas]

    def obter(self, usuario_id):
        linha = self._db.consultar_um("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        return serializar(linha) if linha else None

    def obter_ou_falhar(self, usuario_id):
        usuario = self.obter(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuário não encontrado")
        return usuario

    def existe(self, usuario_id):
        return self._db.valor_escalar(
            "SELECT COUNT(*) FROM usuarios WHERE id = ?", (usuario_id,), padrao=0
        ) > 0

    def criar(self, nome, email, senha, tipo=TIPO_USUARIO_PADRAO):
        return self._db.executar(
            "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
            (nome, email, gerar_hash(senha), tipo),
        )

    def autenticar(self, email, senha):
        """Busca pelo e-mail e compara o hash — a senha nunca entra na query."""
        linha = self._db.consultar_um("SELECT * FROM usuarios WHERE email = ?", (email,))
        if linha is None or not check_password_hash(linha["senha"], senha):
            return None
        return {campo: linha[campo] for campo in ("id", "nome", "email", "tipo")}

    def contar(self):
        return self._db.valor_escalar("SELECT COUNT(*) FROM usuarios", padrao=0)
