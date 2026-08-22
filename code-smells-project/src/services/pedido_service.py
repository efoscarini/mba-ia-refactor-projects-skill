"""Regra de negócio do pedido: validação de estoque, cálculo do total e efeitos."""
from src.config.constants import CASAS_DECIMAIS, STATUS_APROVADO, STATUS_CANCELADO
from src.middlewares.errors import BusinessError


class PedidoService:
    def __init__(self, pedido_model, produto_model, notificacao_service):
        self._pedidos = pedido_model
        self._produtos = produto_model
        self._notificacoes = notificacao_service

    def criar(self, usuario_id, itens):
        produtos = self._produtos.obter_varios([item["produto_id"] for item in itens])
        total = self._calcular_total(itens, produtos)

        pedido_id = self._pedidos.criar(usuario_id, itens, produtos, total)
        self._notificacoes.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}

    def _calcular_total(self, itens, produtos_por_id):
        """Regra pura: testável sem banco e sem HTTP."""
        total = 0.0
        for item in itens:
            produto = produtos_por_id.get(item["produto_id"])
            if produto is None:
                raise BusinessError(f"Produto {item['produto_id']} não encontrado")
            if produto["estoque"] < item["quantidade"]:
                raise BusinessError(f"Estoque insuficiente para {produto['nome']}")
            total += produto["preco"] * item["quantidade"]
        return round(total, CASAS_DECIMAIS)

    def listar_todos(self):
        return self._pedidos.listar_todos()

    def listar_por_usuario(self, usuario_id):
        return self._pedidos.listar_por_usuario(usuario_id)

    def atualizar_status(self, pedido_id, status):
        self._pedidos.atualizar_status(pedido_id, status)
        if status in (STATUS_APROVADO, STATUS_CANCELADO):
            self._notificacoes.status_alterado(pedido_id, status)
