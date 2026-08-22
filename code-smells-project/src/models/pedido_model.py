"""Acesso a dados da entidade Pedido e seus itens."""
from collections import defaultdict

from src.config.constants import STATUS_PEDIDO_PADRAO

CAMPOS = ("id", "usuario_id", "status", "total", "criado_em")


class PedidoModel:
    def __init__(self, db):
        self._db = db

    def _com_itens(self, pedidos):
        """Duas queries no total, independentemente da quantidade de pedidos."""
        if not pedidos:
            return []

        ids = [pedido["id"] for pedido in pedidos]
        placeholders = ",".join("?" * len(ids))
        itens = self._db.consultar(
            f"""
            SELECT i.pedido_id,
                   i.produto_id,
                   i.quantidade,
                   i.preco_unitario,
                   COALESCE(p.nome, 'Desconhecido') AS produto_nome
            FROM itens_pedido i
            LEFT JOIN produtos p ON p.id = i.produto_id
            WHERE i.pedido_id IN ({placeholders})
            """,
            tuple(ids),
        )

        agrupados = defaultdict(list)
        for item in itens:
            agrupados[item["pedido_id"]].append({
                "produto_id": item["produto_id"],
                "produto_nome": item["produto_nome"],
                "quantidade": item["quantidade"],
                "preco_unitario": item["preco_unitario"],
            })

        resultado = []
        for pedido in pedidos:
            registro = {campo: pedido[campo] for campo in CAMPOS}
            registro["itens"] = agrupados.get(pedido["id"], [])
            resultado.append(registro)
        return resultado

    def listar_todos(self):
        return self._com_itens(self._db.consultar("SELECT * FROM pedidos"))

    def listar_por_usuario(self, usuario_id):
        return self._com_itens(
            self._db.consultar("SELECT * FROM pedidos WHERE usuario_id = ?", (usuario_id,))
        )

    def criar(self, usuario_id, itens, produtos_por_id, total):
        """Cabeçalho, itens e baixa de estoque em uma única transação."""
        with self._db.transacao() as db:
            pedido_id = db.executar(
                "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, ?, ?)",
                (usuario_id, STATUS_PEDIDO_PADRAO, total),
            )
            for item in itens:
                produto = produtos_por_id[item["produto_id"]]
                db.executar(
                    "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) "
                    "VALUES (?, ?, ?, ?)",
                    (pedido_id, item["produto_id"], item["quantidade"], produto["preco"]),
                )
                db.executar(
                    "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
                    (item["quantidade"], item["produto_id"]),
                )
        return pedido_id

    def atualizar_status(self, pedido_id, status):
        self._db.executar("UPDATE pedidos SET status = ? WHERE id = ?", (status, pedido_id))

    def contar(self):
        return self._db.valor_escalar("SELECT COUNT(*) FROM pedidos", padrao=0)

    def agregados(self):
        """Totais calculados pelo banco, em uma query, em vez de cinco COUNTs."""
        linha = self._db.consultar_um(
            """
            SELECT COUNT(*)                                                AS total_pedidos,
                   COALESCE(SUM(total), 0)                                 AS faturamento,
                   SUM(CASE WHEN status = 'pendente'  THEN 1 ELSE 0 END)   AS pendentes,
                   SUM(CASE WHEN status = 'aprovado'  THEN 1 ELSE 0 END)   AS aprovados,
                   SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END)   AS cancelados
            FROM pedidos
            """
        )
        return {chave: (valor or 0) for chave, valor in linha.items()}
