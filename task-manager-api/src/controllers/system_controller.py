"""Endpoints de infraestrutura: index e health check."""
from flask import jsonify

from src.config.constants import API_VERSION
from src.utils.datetime_utils import utcnow


class SystemController:
    def index(self):
        return jsonify({"message": "Task Manager API", "version": API_VERSION}), 200

    def health(self):
        return jsonify({"status": "ok", "timestamp": str(utcnow())}), 200
