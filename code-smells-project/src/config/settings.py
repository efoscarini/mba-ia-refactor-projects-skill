"""Configuração da aplicação — lida exclusivamente de variáveis de ambiente."""
import logging
import os
import secrets

logger = logging.getLogger(__name__)


def _as_bool(raw, default=False):
    if raw is None:
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


class Settings:
    """Nenhum segredo é literal aqui: tudo vem do ambiente."""

    def __init__(self, env=None):
        env = env if env is not None else os.environ

        self.APP_ENV = env.get("APP_ENV", "development")
        self.DEBUG = _as_bool(env.get("FLASK_DEBUG"), default=False)
        self.HOST = env.get("HOST", "127.0.0.1")
        self.PORT = int(env.get("PORT", "5000"))
        self.DATABASE_PATH = env.get("DATABASE_PATH", "loja.db")
        self.CORS_ORIGINS = env.get("CORS_ORIGINS", "*")
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO")
        self.SEED_ADMIN_PASSWORD = env.get("SEED_ADMIN_PASSWORD", "")
        self.SECRET_KEY = self._resolver_secret_key(env.get("SECRET_KEY", ""))

    @property
    def is_production(self):
        return self.APP_ENV.lower() in ("production", "prod")

    def _resolver_secret_key(self, valor):
        if valor:
            return valor
        if self.is_production:
            raise RuntimeError(
                "SECRET_KEY não definida. Configure a variável de ambiente "
                "antes de subir em produção (veja .env.example)."
            )
        logger.warning(
            "SECRET_KEY ausente — gerando chave efêmera para desenvolvimento. "
            "As sessões são invalidadas a cada restart."
        )
        return secrets.token_urlsafe(32)


settings = Settings()
