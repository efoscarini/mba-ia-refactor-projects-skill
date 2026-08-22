"""Constantes de domínio — elimina magic numbers e listas literais espalhadas."""

API_VERSION = "1.0.0"

CATEGORIAS_VALIDAS = ("informatica", "moveis", "vestuario", "geral", "eletronicos", "livros")
CATEGORIA_PADRAO = "geral"

NOME_PRODUTO_MIN = 2
NOME_PRODUTO_MAX = 200

STATUS_PEDIDO_VALIDOS = ("pendente", "aprovado", "enviado", "entregue", "cancelado")
STATUS_PEDIDO_PADRAO = "pendente"
STATUS_APROVADO = "aprovado"
STATUS_CANCELADO = "cancelado"

TIPO_USUARIO_PADRAO = "cliente"

# (faturamento mínimo, percentual de desconto) — avaliado da faixa maior para a menor
FAIXAS_DESCONTO = ((10_000.0, 0.10), (5_000.0, 0.05), (1_000.0, 0.02))

CASAS_DECIMAIS = 2
