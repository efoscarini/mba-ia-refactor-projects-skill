"""Tratamento de erro centralizado.

O projeto original repetia `try/except` em cada rota — vários deles com `except:`
sem tipo, que engole inclusive KeyboardInterrupt e erros de programação.
"""
import logging

from flask import jsonify

from src.middlewares.errors import AppError

logger = logging.getLogger(__name__)


def _resposta(mensagem, status):
    return jsonify({"error": mensagem}), status


def registrar_error_handlers(app):
    @app.errorhandler(AppError)
    def _erro_de_dominio(exc):
        logger.info("Erro de domínio (%s): %s", exc.status, exc.mensagem)
        return _resposta(exc.mensagem, exc.status)

    @app.errorhandler(404)
    def _rota_desconhecida(_):
        return _resposta("Recurso não encontrado", 404)

    @app.errorhandler(405)
    def _metodo_nao_permitido(_):
        return _resposta("Método não permitido", 405)

    @app.errorhandler(Exception)
    def _erro_inesperado(exc):
        # stack trace no log; o cliente recebe apenas a mensagem genérica
        logger.exception("Erro não tratado: %s", exc)
        return _resposta("Erro interno", 500)
