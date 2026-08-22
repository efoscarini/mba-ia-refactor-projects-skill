# code-smells-project

API de E-commerce em Python/Flask. Projeto de entrada do desafio `refactor-arch`,
já refatorado para o padrão MVC pela skill.

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco SQLite (`loja.db`) é criado
no primeiro boot, já com produtos e usuários de exemplo — as senhas do seed são
gravadas com hash.

A configuração é lida de variáveis de ambiente — `.env.example` documenta os
nomes; exporte-as no shell para sobrescrever os defaults de desenvolvimento. Sem
`SECRET_KEY` no ambiente, uma chave efêmera é gerada em desenvolvimento e o boot
**falha** se `APP_ENV=production`.

## Estrutura

```
app.py                  entry point
src/
├── app.py              composition root: create_app()
├── config/             settings (env) e constantes de domínio
├── infra/              conexão SQLite por thread, schema e carga inicial
├── models/             produto, usuario, pedido — único lugar com SQL
├── services/           pedido, relatório, notificação
├── controllers/        orquestração por caso de uso
├── views/              mapeamento rota → controller
└── middlewares/        error handler, exceções de domínio, validadores
```

## Endpoints

`GET /` · `GET /health` · `GET|POST /produtos` · `GET /produtos/busca` ·
`GET|PUT|DELETE /produtos/<id>` · `GET|POST /usuarios` · `GET /usuarios/<id>` ·
`POST /login` · `GET|POST /pedidos` · `GET /pedidos/usuario/<id>` ·
`PUT /pedidos/<id>/status` · `GET /relatorios/vendas`

As rotas `/admin/query` e `/admin/reset-db` foram removidas na refatoração —
executavam SQL arbitrário e apagavam o banco, sem autenticação. Ver
[`reports/audit-project-1.md`](../reports/audit-project-1.md).

## A skill

`.claude/skills/refactor-arch/` — invocação: `claude "/refactor-arch"`
