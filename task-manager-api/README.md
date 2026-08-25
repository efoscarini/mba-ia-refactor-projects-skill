# task-manager-api

API de Task Manager em Python/Flask + SQLAlchemy. Projeto de entrada do desafio
`refactor-arch`, já refatorado para o padrão MVC pela skill.

Este era o projeto "parcialmente organizado": tinha `models/`, `routes/`,
`services/` e `utils/`, mas sem camada de controllers — as rotas acumulavam
validação, acesso ao ORM, regra de negócio e serialização.

## Como rodar

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
python seed.py                                  # rode antes do primeiro boot
python app.py
```

A aplicação sobe em `http://127.0.0.1:5000`. O banco fica em
`instance/tasks.db`. Usuários do seed: `joao@email.com` / `1234`,
`maria@email.com` / `abcd`, `pedro@email.com` / `pass`.

A configuração é lida de variáveis de ambiente — `.env.example` documenta os
nomes (`SECRET_KEY`, `DATABASE_URI`, `SMTP_*`, `NOTIFICATIONS_ENABLED`); exporte-as
no shell para sobrescrever os defaults de desenvolvimento.

## Estrutura

```
app.py                  entry point
seed.py                 carga inicial (senhas com hash)
src/
├── app.py              composition root: create_app()
├── config/             settings (env) e constantes de domínio
├── infra/              instância do SQLAlchemy
├── models/             task, user, category — entidade + acesso a dados
├── services/           task, user, category, report, notification
├── controllers/        orquestração por caso de uso
├── views/              mapeamento rota → controller
├── middlewares/        error handler, exceções de domínio, validadores
└── utils/              datas (sem API deprecated) e helpers de cálculo
```

## Endpoints

`GET /` · `GET /health` · `GET|POST /tasks` 🔒 · `GET /tasks/search` 🔒 ·
`GET /tasks/stats` 🔒 · `GET|PUT|DELETE /tasks/<id>` 🔒 · `POST /users` ·
`GET /users` 🔒 · `GET|PUT|DELETE /users/<id>` 🔒 · `GET /users/<id>/tasks` 🔒 ·
`POST /login` · `GET /reports/summary` 🔒 · `GET /reports/user/<id>` 🔒 ·
`GET /categories` · `POST /categories` 🔒 · `PUT|DELETE /categories/<id>` 🔒

🔒 = exige `Authorization: Bearer <token>`, obtido em `POST /login`. A imposição
vem ligada (`AUTH_ENFORCED=true`); suba com `AUTH_ENFORCED=false` para restaurar
o contrato original durante uma migração — o acesso anônimo vira `WARN` no log.
Task tem dono (`user_id`), por isso `/tasks` é tratado como dado de usuário e não
como catálogo público.

Na refatoração: o campo `password` saiu de todas as respostas, o hash passou a
ser pbkdf2 com salt e o token do login é assinado de verdade. Ver
[`reports/audit-project-3.md`](../reports/audit-project-3.md).

## A skill

`.claude/skills/refactor-arch/` — invocação: `claude "/refactor-arch"`
