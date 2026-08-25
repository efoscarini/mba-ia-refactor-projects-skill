"""Composition root: monta as dependências, registra rotas e devolve o app."""
import logging

from flask import Flask
from flask_cors import CORS

from src.config.settings import Settings, settings as settings_padrao
from src.controllers.category_controller import CategoryController
from src.controllers.report_controller import ReportController
from src.controllers.system_controller import SystemController
from src.controllers.task_controller import TaskController
from src.controllers.user_controller import UserController
from src.infra.database import db
from src.middlewares.auth import construir_require_auth
from src.middlewares.error_handler import registrar_error_handlers
from src.services.auth_service import AuthService
from src.services.category_service import CategoryService
from src.services.notification_service import NotificationService
from src.services.report_service import ReportService
from src.services.task_service import TaskService
from src.services.user_service import UserService
from src.views import (
    category_routes,
    report_routes,
    system_routes,
    task_routes,
    user_routes,
)


def configurar_logging(nivel):
    logging.basicConfig(
        level=getattr(logging, nivel.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )


def create_app(settings: Settings = None):
    settings = settings or settings_padrao
    configurar_logging(settings.LOG_LEVEL)

    app = Flask(__name__)
    app.config["SECRET_KEY"] = settings.SECRET_KEY
    app.config["DEBUG"] = settings.DEBUG
    app.config["SQLALCHEMY_DATABASE_URI"] = settings.SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = settings.SQLALCHEMY_TRACK_MODIFICATIONS
    CORS(app, origins=settings.CORS_ORIGINS)

    # --- infraestrutura ---
    db.init_app(app)
    # o import registra os mappers antes do create_all
    from src import models  # noqa: F401

    # --- services ---
    notification_service = NotificationService(settings)
    task_service = TaskService(notification_service)
    auth_service = AuthService(settings)
    user_service = UserService(auth_service)
    category_service = CategoryService()
    report_service = ReportService()

    # --- controllers ---
    task_controller = TaskController(task_service)
    user_controller = UserController(user_service)
    category_controller = CategoryController(category_service)
    report_controller = ReportController(report_service)
    system_controller = SystemController()

    # --- rotas ---
    require_auth = construir_require_auth(settings, auth_service)
    app.register_blueprint(task_routes.criar_blueprint(task_controller, require_auth))
    app.register_blueprint(user_routes.criar_blueprint(user_controller, require_auth))
    app.register_blueprint(category_routes.criar_blueprint(category_controller, require_auth))
    app.register_blueprint(report_routes.criar_blueprint(report_controller, require_auth))
    app.register_blueprint(system_routes.criar_blueprint(system_controller))

    # --- middlewares ---
    registrar_error_handlers(app)

    with app.app_context():
        db.create_all()

    return app
