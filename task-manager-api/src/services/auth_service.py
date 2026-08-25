"""Emissão e verificação do token de sessão (RF-15).

O projeto original devolvia `'fake-jwt-token-' + id` — previsível e sem
assinatura. Aqui o token é assinado com `itsdangerous` usando a `SECRET_KEY` do
ambiente e tem validade. O formato da resposta do login não muda: continua um
campo `token` do tipo string.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.middlewares.errors import UnauthorizedError

TOKEN_SALT = "task-manager-auth"


class AuthService:
    def __init__(self, settings):
        self._serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)
        self._max_age = settings.TOKEN_MAX_AGE

    def emitir(self, user_id):
        return self._serializer.dumps({"user_id": user_id})

    def verificar(self, token):
        try:
            dados = self._serializer.loads(token, max_age=self._max_age)
        except SignatureExpired as exc:
            raise UnauthorizedError("Token expirado") from exc
        except BadSignature as exc:
            raise UnauthorizedError("Token inválido") from exc
        return dados["user_id"]
