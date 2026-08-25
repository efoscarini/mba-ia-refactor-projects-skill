"""Emissão e verificação do token de sessão (RF-15).

O projeto original não emitia credencial nenhuma no `/login` — só respondia
"Login OK". Sem emissor não há o que o middleware verificar, então o token vem
antes da proteção das rotas. O campo `token` é **aditivo** na resposta do login:
`dados`, `sucesso` e `mensagem` continuam iguais para os clientes atuais.
"""
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from src.middlewares.errors import UnauthorizedError

TOKEN_SALT = "loja-auth"


class AuthService:
    def __init__(self, settings):
        self._serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)
        self._max_age = settings.TOKEN_MAX_AGE

    def emitir(self, usuario_id):
        return self._serializer.dumps({"usuario_id": usuario_id})

    def verificar(self, token):
        try:
            dados = self._serializer.loads(token, max_age=self._max_age)
        except SignatureExpired as exc:
            raise UnauthorizedError("Token expirado") from exc
        except BadSignature as exc:
            raise UnauthorizedError("Token inválido") from exc
        return dados["usuario_id"]
