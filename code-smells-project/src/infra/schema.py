"""Criação do schema e carga inicial.

Antes vivia dentro de `get_db()`, misturado à abertura da conexão. Aqui é um
passo explícito do boot, e as senhas de exemplo entram já com hash.
"""
import logging

from src.config.constants import TIPO_USUARIO_PADRAO

logger = logging.getLogger(__name__)

TABELAS = (
    """
    CREATE TABLE IF NOT EXISTS produtos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        descricao TEXT,
        preco REAL NOT NULL,
        estoque INTEGER NOT NULL DEFAULT 0,
        categoria TEXT,
        ativo INTEGER DEFAULT 1,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        tipo TEXT DEFAULT '{tipo_padrao}',
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """.format(tipo_padrao=TIPO_USUARIO_PADRAO),
    """
    CREATE TABLE IF NOT EXISTS pedidos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        status TEXT DEFAULT 'pendente',
        total REAL,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS itens_pedido (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        pedido_id INTEGER REFERENCES pedidos(id) ON DELETE CASCADE,
        produto_id INTEGER REFERENCES produtos(id),
        quantidade INTEGER NOT NULL,
        preco_unitario REAL NOT NULL
    )
    """,
)

PRODUTOS_EXEMPLO = (
    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
)

USUARIOS_EXEMPLO = (
    ("Admin", "admin@loja.com", "admin123", "admin"),
    ("João Silva", "joao@email.com", "123456", "cliente"),
    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
)


def criar_schema(db):
    for ddl in TABELAS:
        db.executar(ddl)


def popular_dados_iniciais(db, gerar_hash, senha_admin=""):
    """Carga idempotente. Senhas de exemplo são gravadas já com hash."""
    if db.valor_escalar("SELECT COUNT(*) FROM produtos", padrao=0) > 0:
        return

    db.executar_muitos(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        PRODUTOS_EXEMPLO,
    )

    usuarios = []
    for nome, email, senha_padrao, tipo in USUARIOS_EXEMPLO:
        senha = senha_admin if (tipo == "admin" and senha_admin) else senha_padrao
        usuarios.append((nome, email, gerar_hash(senha), tipo))

    db.executar_muitos(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        usuarios,
    )
    logger.info("Dados iniciais carregados: %d produtos, %d usuários",
                len(PRODUTOS_EXEMPLO), len(usuarios))
