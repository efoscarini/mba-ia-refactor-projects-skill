# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express. Projeto de entrada do desafio
`refactor-arch`, já refatorado para o padrão MVC pela skill.

## Como rodar

```bash
npm install
cp .env.example .env
npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória por
padrão (`DATABASE_PATH=:memory:`) e carrega o seed no boot; aponte
`DATABASE_PATH` para um arquivo se quiser persistência.

`PAYMENT_GATEWAY_KEY` e `SMTP_PASSWORD` são obrigatórias quando
`APP_ENV=production`.

## Estrutura

```
src/
├── app.js              entry point
├── server.js           composition root: createApp()
├── config/             env e constantes de domínio
├── infra/              sqlite promisificado com transações, schema, logger
├── models/             user, course, enrollment, payment, auditLog
├── services/           checkout, report, user, password (scrypt), gateway
├── controllers/        orquestração por caso de uso
├── routes/             mapeamento rota → controller, sob /api
└── middlewares/        asyncHandler, error handler, validadores
```

## Endpoints

`POST /api/checkout` · `GET /api/admin/financial-report` ·
`DELETE /api/users/:id`

Exemplos de requisição em `api.http`.

Na refatoração: matrículas e pagamentos passaram a ser removidos em cascata junto
com o usuário, e o número do cartão é mascarado no log. Ver
[`reports/audit-project-2.md`](../reports/audit-project-2.md).

## A skill

`.claude/skills/refactor-arch/` — invocação: `claude "/refactor-arch"`
