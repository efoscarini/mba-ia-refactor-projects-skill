"""Composition root: monta as dependências, registra rotas e devolve o app.

É o único ponto do projeto que instancia infraestrutura.
"""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, settings as settings_padrao
from src.controllers.pedido_controller import PedidoController
from src.controllers.produto_controller import ProdutoController
from src.controllers.relatorio_controller import RelatorioController
from src.controllers.system_controller import SystemController
from src.controllers.usuario_controller import UsuarioController
from src.infra.database import Database
from src.infra.schema import criar_schema, popular_dados_iniciais
from src.middlewares.auth import construir_require_auth
from src.middlewares.error_handler import registrar_error_handlers
from src.models.pedido_model import PedidoModel
from src.models.produto_model import ProdutoModel
from src.models.usuario_model import UsuarioModel, gerar_hash
from src.services.auth_service import AuthService
from src.services.notificacao_service import NotificacaoService
from src.services.pedido_service import PedidoService
from src.services.relatorio_service import RelatorioService
from src.views import (
    pedido_routes,
    produto_routes,
    relatorio_routes,
    system_routes,
    usuario_routes,
)


def configurar_logging(nivel):
    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )


def create_app(settings: Settings = None, db: Database = None):
    settings = settings or settings_padrao
    configurar_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    CORS(app, origins=settings.CORS_ORIGINS)

    # --- infraestrutura ---
    db = db or Database(settings.DATABASE_PATH)
    criar_schema(db)
    popular_dados_iniciais(db, gerar_hash, settings.SEED_ADMIN_PASSWORD)

    # --- models ---
    produto_model = ProdutoModel(db)
    usuario_model = UsuarioModel(db)
    pedido_model = PedidoModel(db)

    # --- services ---
    auth_service = AuthService(settings)
    notificacao_service = NotificacaoService()
    pedido_service = PedidoService(pedido_model, produto_model, notificacao_service)
    relatorio_service = RelatorioService(pedido_model)

    # --- controllers ---
    produto_controller = ProdutoController(produto_model)
    usuario_controller = UsuarioController(usuario_model, auth_service)
    pedido_controller = PedidoController(pedido_service)
    relatorio_controller = RelatorioController(relatorio_service)
    system_controller = SystemController(produto_model, usuario_model, pedido_model)

    # --- rotas ---
    require_auth = construir_require_auth(settings, auth_service)
    app.register_blueprint(produto_routes.criar_blueprint(produto_controller, require_auth))
    app.register_blueprint(usuario_routes.criar_blueprint(usuario_controller, require_auth))
    app.register_blueprint(pedido_routes.criar_blueprint(pedido_controller, require_auth))
    app.register_blueprint(relatorio_routes.criar_blueprint(relatorio_controller, require_auth))
    app.register_blueprint(system_routes.criar_blueprint(system_controller))

    # --- middlewares ---
    registrar_error_handlers(app)

    app.extensions["database"] = db
    return app
