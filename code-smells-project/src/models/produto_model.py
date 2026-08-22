"""Acesso a dados e serialização da entidade Produto.

Único lugar do projeto com SQL de produtos, sempre parametrizado.
"""
from src.middlewares.errors import NotFoundError

CAMPOS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def serializar(linha):
    return {campo: linha[campo] for campo in CAMPOS}


class ProdutoModel:
    def __init__(self, db):
        self._db = db

    def listar(self):
        linhas = self._db.consultar("SELECT * FROM produtos")
        return [serializar(linha) for linha in linhas]

    def obter(self, produto_id):
        linha = self._db.consultar_um("SELECT * FROM produtos WHERE id = ?", (produto_id,))
        return serializar(linha) if linha else None

    def obter_ou_falhar(self, produto_id):
        produto = self.obter(produto_id)
        if produto is None:
            raise NotFoundError("Produto não encontrado")
        return produto

    def obter_varios(self, ids):
        """Uma query para N ids — evita consulta dentro de laço (N+1)."""
        if not ids:
            return {}
        placeholders = ",".join("?" * len(ids))
        linhas = self._db.consultar(
            f"SELECT * FROM produtos WHERE id IN ({placeholders})", tuple(ids)
        )
        return {linha["id"]: serializar(linha) for linha in linhas}

    def criar(self, nome, descricao, preco, estoque, categoria):
        return self._db.executar(
            "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) "
            "VALUES (?, ?, ?, ?, ?)",
            (nome, descricao, preco, estoque, categoria),
        )

    def atualizar(self, produto_id, nome, descricao, preco, estoque, categoria):
        self._db.executar(
            "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, "
            "categoria = ? WHERE id = ?",
            (nome, descricao, preco, estoque, categoria, produto_id),
        )

    def deletar(self, produto_id):
        self._db.executar("DELETE FROM produtos WHERE id = ?", (produto_id,))

    def baixar_estoque(self, produto_id, quantidade):
        self._db.executar(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (quantidade, produto_id),
        )

    def buscar(self, termo=None, categoria=None, preco_min=None, preco_max=None):
        """Filtro dinâmico com placeholders: nada do request entra na string SQL."""
        clausulas = ["1=1"]
        params = []

        if termo:
            clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
            params.extend([f"%{termo}%", f"%{termo}%"])
        if categoria:
            clausulas.append("categoria = ?")
            params.append(categoria)
        if preco_min is not None:
            clausulas.append("preco >= ?")
            params.append(preco_min)
        if preco_max is not None:
            clausulas.append("preco <= ?")
            params.append(preco_max)

        sql = f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)}"
        return [serializar(linha) for linha in self._db.consultar(sql, tuple(params))]

    def contar(self):
        return self._db.valor_escalar("SELECT COUNT(*) FROM produtos", padrao=0)
