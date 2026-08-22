"""Notificações do domínio.

Substitui os `print("ENVIANDO EMAIL...")` espalhados pelo controller. Fica atrás
de uma interface para que o canal real (e-mail, SMS, fila) seja trocado sem tocar
em controller ou model.
"""
import logging

logger = logging.getLogger(__name__)


class NotificacaoService:
    CANAIS = ("email", "sms", "push")

    def pedido_criado(self, pedido_id, usuario_id):
        for canal in self.CANAIS:
            logger.info("Notificação [%s]: pedido %s criado para o usuário %s",
                        canal, pedido_id, usuario_id)

    def status_alterado(self, pedido_id, status):
        logger.info("Notificação [email]: pedido %s mudou para o status '%s'",
                    pedido_id, status)
