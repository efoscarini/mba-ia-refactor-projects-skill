"""Entry point da aplicação — mantém `python app.py` funcionando."""
import logging

from src.app import create_app
from src.config.settings import settings

logger = logging.getLogger(__name__)

app = create_app(settings)

if __name__ == "__main__":
    logger.info("Servidor iniciado em http://%s:%s", settings.HOST, settings.PORT)
    app.run(host=settings.HOST, port=settings.PORT, debug=settings.DEBUG)
