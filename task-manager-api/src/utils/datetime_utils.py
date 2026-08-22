"""Utilitários de data.

`datetime.utcnow()` está deprecated a partir do Python 3.12. A substituição
recomendada (`datetime.now(timezone.utc)`) devolve um datetime *aware*, que não
pode ser comparado com os valores *naive* já gravados nas colunas `DateTime`.
O helper abaixo usa a API nova e normaliza o resultado para naive-UTC, mantendo
a compatibilidade com o schema existente.
"""
from datetime import datetime, timezone

from src.config.constants import DATE_FORMAT


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def parse_date(valor, formatos=(DATE_FORMAT,)):
    """Converte string em datetime. Devolve None se nenhum formato casar.

    O default é apenas YYYY-MM-DD, que é o formato aceito pelas rotas de task no
    projeto original — o fallback DD/MM/YYYY existia em `utils/helpers.py`, mas
    era código morto e aceitá-lo aqui afrouxaria a validação.
    """
    if not valor:
        return None
    for formato in formatos:
        try:
            return datetime.strptime(valor, formato)
        except (TypeError, ValueError):
            continue
    return None


def format_date(valor):
    return str(valor) if valor else None
