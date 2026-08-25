"""Configuração da aplicação — lida exclusivamente de variáveis de ambiente."""
import logging
import os
import secrets
from pathlib import Path

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[2]
INSTANCE_DIR = BASE_DIR / "instance"


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
        self.LOG_LEVEL = env.get("LOG_LEVEL", "INFO")
        self.CORS_ORIGINS = env.get("CORS_ORIGINS", "*")
        self.SQLALCHEMY_DATABASE_URI = env.get("DATABASE_URI") or self._uri_padrao()
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False
        self.SECRET_KEY = self._resolver_secret_key(env.get("SECRET_KEY", ""))

        # SMTP: o NotificationService original trazia host, usuário e senha fixos
        self.SMTP_HOST = env.get("SMTP_HOST", "")
        self.SMTP_PORT = int(env.get("SMTP_PORT", "587"))
        self.SMTP_USER = env.get("SMTP_USER", "")
        self.SMTP_PASSWORD = env.get("SMTP_PASSWORD", "")
        self.NOTIFICATIONS_ENABLED = _as_bool(env.get("NOTIFICATIONS_ENABLED"), default=False)

        # RF-15: o middleware de autorização é sempre montado; só a imposição é
        # opcional. Desligada por padrão para preservar o contrato das rotas.
        self.AUTH_ENFORCED = _as_bool(env.get("AUTH_ENFORCED"), default=True)
        self.TOKEN_MAX_AGE = int(env.get("AUTH_TOKEN_TTL", "3600"))

    @property
    def is_production(self):
        return self.APP_ENV.lower() in ("production", "prod")

    def _uri_padrao(self):
        INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{INSTANCE_DIR / 'tasks.db'}"

    def _resolver_secret_key(self, valor):
        if valor:
            return valor
        if self.is_production:
            raise RuntimeError(
                "SECRET_KEY não definida. Configure a variável de ambiente "
                "antes de subir em produção (veja .env.example)."
            )
        logger.warning(
            "SECRET_KEY ausente — gerando chave efêmera para desenvolvimento."
        )
        return secrets.token_urlsafe(32)


settings = Settings()
