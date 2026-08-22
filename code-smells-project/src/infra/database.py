"""Acesso de baixo nível ao SQLite.

Substitui a conexão global mutável do projeto original: a instância é criada no
composition root e injetada nos models. A conexão é por thread, o que remove o
`check_same_thread=False` e a corrida entre requisições concorrentes.

A conexão roda em autocommit (`isolation_level=None`); transações são explícitas
via `transacao()`, o que evita segurar o lock de escrita entre requisições.
"""
import sqlite3
import threading
from contextlib import contextmanager

TIMEOUT_SEGUNDOS = 10.0


class Database:
    def __init__(self, path, timeout=TIMEOUT_SEGUNDOS):
        self._path = path
        self._timeout = timeout
        self._local = threading.local()

    @property
    def connection(self):
        conexao = getattr(self._local, "conexao", None)
        if conexao is None:
            conexao = sqlite3.connect(
                self._path, timeout=self._timeout, isolation_level=None
            )
            conexao.row_factory = sqlite3.Row
            conexao.execute("PRAGMA foreign_keys = ON")
            conexao.execute("PRAGMA journal_mode = WAL")
            self._local.conexao = conexao
        return conexao

    def consultar(self, sql, params=()):
        cursor = self.connection.execute(sql, params)
        return [dict(linha) for linha in cursor.fetchall()]

    def consultar_um(self, sql, params=()):
        linha = self.connection.execute(sql, params).fetchone()
        return dict(linha) if linha is not None else None

    def valor_escalar(self, sql, params=(), padrao=None):
        linha = self.connection.execute(sql, params).fetchone()
        if linha is None or linha[0] is None:
            return padrao
        return linha[0]

    def executar(self, sql, params=()):
        """Executa uma escrita e devolve o lastrowid."""
        return self.connection.execute(sql, params).lastrowid

    def executar_muitos(self, sql, sequencia_params):
        self.connection.executemany(sql, sequencia_params)

    @contextmanager
    def transacao(self):
        """Tudo ou nada: escritas relacionadas não deixam estado parcial."""
        conexao = self.connection
        conexao.execute("BEGIN")
        try:
            yield self
        except Exception:
            conexao.execute("ROLLBACK")
            raise
        else:
            conexao.execute("COMMIT")

    def fechar(self):
        conexao = getattr(self._local, "conexao", None)
        if conexao is not None:
            conexao.close()
            self._local.conexao = None
