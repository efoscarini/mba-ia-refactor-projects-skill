"""Instância única do SQLAlchemy, inicializada pelo composition root."""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
