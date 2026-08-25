"""Autorização em rota sensível (RF-15, resolve AP-11).

A imposição nasce **ligada**: rota sensível sem credencial responde 401. É uma
mudança intencional de contrato, declarada no relatório de auditoria.

`AUTH_ENFORCED=false` é a válvula de escape para uma janela de migração —
restaura o contrato original e transforma cada acesso anônimo a rota sensível em
log de aviso, para o buraco ficar visível em vez de silencioso.
"""
import logging
from functools import wraps

from flask import g, request

from src.middlewares.errors import UnauthorizedError

logger = logging.getLogger(__name__)


def _extrair_bearer(header):
    valor = (header or "").strip()
    if valor.lower().startswith("bearer "):
        return valor[7:].strip()
    return valor


def construir_require_auth(settings, auth_service):
    """Devolve o decorator que protege uma view."""

    def require_auth(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = _extrair_bearer(request.headers.get("Authorization"))

            if not settings.AUTH_ENFORCED:
                if not token:
                    logger.warning(
                        "Rota sensível acessada sem credencial: %s %s "
                        "(AUTH_ENFORCED=false — imposição desligada por configuração)",
                        request.method,
                        request.path,
                    )
                return view(*args, **kwargs)

            if not token:
                raise UnauthorizedError("Credencial ausente")
            g.user_id = auth_service.verificar(token)
            return view(*args, **kwargs)

        return wrapper

    return require_auth
