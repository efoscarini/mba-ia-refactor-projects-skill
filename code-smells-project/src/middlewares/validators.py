"""Validação de entrada — uma função por caso de uso, reutilizada por POST e PUT.

No projeto original a mesma sequência de `if` estava duplicada entre criação e
atualização, com divergências entre as duas.
"""
from src.config.constants import (
    CATEGORIAS_VALIDAS,
    CATEGORIA_PADRAO,
    NOME_PRODUTO_MAX,
    NOME_PRODUTO_MIN,
    STATUS_PEDIDO_VALIDOS,
)
from src.middlewares.errors import ValidationError


def _corpo(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    return dados


def _numero(valor, rotulo):
    if isinstance(valor, bool) or not isinstance(valor, (int, float)):
        raise ValidationError(f"{rotulo} deve ser numérico")
    return valor


def validar_produto(dados):
    dados = _corpo(dados)

    for campo, mensagem in (
        ("nome", "Nome é obrigatório"),
        ("preco", "Preço é obrigatório"),
        ("estoque", "Estoque é obrigatório"),
    ):
        if campo not in dados:
            raise ValidationError(mensagem)

    nome = dados["nome"]
    preco = _numero(dados["preco"], "Preço")
    estoque = _numero(dados["estoque"], "Estoque")
    categoria = dados.get("categoria", CATEGORIA_PADRAO)

    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if not isinstance(nome, str) or len(nome) < NOME_PRODUTO_MIN:
        raise ValidationError("Nome muito curto")
    if len(nome) > NOME_PRODUTO_MAX:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")

    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validar_filtros_produto(args):
    def _float_opcional(chave, rotulo):
        bruto = args.get(chave)
        if not bruto:
            return None
        try:
            return float(bruto)
        except (TypeError, ValueError):
            raise ValidationError(f"{rotulo} deve ser numérico")

    return {
        "termo": args.get("q", ""),
        "categoria": args.get("categoria") or None,
        "preco_min": _float_opcional("preco_min", "preco_min"),
        "preco_max": _float_opcional("preco_max", "preco_max"),
    }


def validar_usuario(dados):
    dados = _corpo(dados)
    nome = dados.get("nome", "")
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not nome or not email or not senha:
        raise ValidationError("Nome, email e senha são obrigatórios")

    return {"nome": nome, "email": email, "senha": senha}


def validar_login(dados):
    dados = _corpo(dados)
    email = dados.get("email", "")
    senha = dados.get("senha", "")

    if not email or not senha:
        raise ValidationError("Email e senha são obrigatórios")

    return {"email": email, "senha": senha}


def validar_pedido(dados):
    dados = _corpo(dados)
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])

    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens:
        raise ValidationError("Pedido deve ter pelo menos 1 item")

    normalizados = []
    for item in itens:
        if not isinstance(item, dict) or "produto_id" not in item or "quantidade" not in item:
            raise ValidationError("Item inválido: informe produto_id e quantidade")
        quantidade = _numero(item["quantidade"], "Quantidade")
        if quantidade <= 0:
            raise ValidationError("Quantidade deve ser maior que zero")
        normalizados.append({"produto_id": item["produto_id"], "quantidade": int(quantidade)})

    return {"usuario_id": usuario_id, "itens": normalizados}


def validar_status_pedido(dados):
    dados = dados or {}
    status = dados.get("status", "")
    if status not in STATUS_PEDIDO_VALIDOS:
        raise ValidationError("Status inválido")
    return status
