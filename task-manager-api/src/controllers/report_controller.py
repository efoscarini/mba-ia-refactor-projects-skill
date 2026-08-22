"""Orquestração dos relatórios."""
from flask import jsonify


class ReportController:
    def __init__(self, report_service):
        self._reports = report_service

    def resumo(self):
        return jsonify(self._reports.resumo()), 200

    def por_usuario(self, user_id):
        return jsonify(self._reports.por_usuario(user_id)), 200
