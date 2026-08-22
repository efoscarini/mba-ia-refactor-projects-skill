"""Notificações de task.

O serviço original trazia host, usuário e senha de SMTP fixos no construtor e
acumulava as notificações numa lista em memória — estado global que se perdia a
cada restart. Aqui a configuração é injetada, o envio é opcional e o registro vai
para o log.
"""
import logging
import smtplib

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, settings):
        self._settings = settings

    @property
    def habilitado(self):
        s = self._settings
        return bool(s.NOTIFICATIONS_ENABLED and s.SMTP_HOST and s.SMTP_USER)

    def task_atribuida(self, user, task):
        assunto = f"Nova task atribuída: {task.title}"
        corpo = (
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}"
        )
        self._notificar("task_assigned", user, assunto, corpo)

    def task_atrasada(self, user, task):
        assunto = f"Task atrasada: {task.title}"
        corpo = (
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n\n"
            f"Data limite: {task.due_date}"
        )
        self._notificar("task_overdue", user, assunto, corpo)

    def _notificar(self, tipo, user, assunto, corpo):
        logger.info("Notificação '%s' para o usuário %s (task)", tipo, user.id)
        if not self.habilitado:
            return
        self._enviar_email(user.email, assunto, corpo)

    def _enviar_email(self, destinatario, assunto, corpo):
        s = self._settings
        try:
            with smtplib.SMTP(s.SMTP_HOST, s.SMTP_PORT) as servidor:
                servidor.starttls()
                servidor.login(s.SMTP_USER, s.SMTP_PASSWORD)
                servidor.sendmail(s.SMTP_USER, destinatario, f"Subject: {assunto}\n\n{corpo}")
        except smtplib.SMTPException as exc:
            # falha de e-mail não pode derrubar a operação de negócio
            logger.warning("Falha ao enviar e-mail: %s", exc)
