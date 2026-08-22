"""Relatório de vendas — a regra de desconto sai do model e vira função pura."""
from src.config.constants import CASAS_DECIMAIS, FAIXAS_DESCONTO


def calcular_desconto(faturamento):
    for faturamento_minimo, percentual in FAIXAS_DESCONTO:
        if faturamento > faturamento_minimo:
            return round(faturamento * percentual, CASAS_DECIMAIS)
    return 0


class RelatorioService:
    def __init__(self, pedido_model):
        self._pedidos = pedido_model

    def vendas(self):
        dados = self._pedidos.agregados()
        faturamento = dados["faturamento"]
        total_pedidos = dados["total_pedidos"]
        desconto = calcular_desconto(faturamento)

        return {
            "total_pedidos": total_pedidos,
            "faturamento_bruto": round(faturamento, CASAS_DECIMAIS),
            "desconto_aplicavel": round(desconto, CASAS_DECIMAIS),
            "faturamento_liquido": round(faturamento - desconto, CASAS_DECIMAIS),
            "pedidos_pendentes": dados["pendentes"],
            "pedidos_aprovados": dados["aprovados"],
            "pedidos_cancelados": dados["cancelados"],
            "ticket_medio": round(faturamento / total_pedidos, CASAS_DECIMAIS) if total_pedidos else 0,
        }
