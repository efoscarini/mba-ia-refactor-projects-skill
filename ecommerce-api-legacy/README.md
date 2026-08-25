# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express. Projeto de entrada do desafio
`refactor-arch`, já refatorado para o padrão MVC pela skill.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://127.0.0.1:3000`. O banco SQLite é em memória por
padrão (`DATABASE_PATH=:memory:`) e carrega o seed no boot; aponte
`DATABASE_PATH` para um arquivo se quiser persistência.

A configuração é lida de `process.env` — `.env.example` documenta os nomes. Para
carregar de um arquivo, use o suporte nativo do Node 20.6+:
`cp .env.example .env && node --env-file=.env src/app.js`.
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

`POST /api/checkout` · `POST /api/login` ·
`GET /api/admin/financial-report` 🔒 · `DELETE /api/users/:id` 🔒

Exemplos de requisição em `api.http`.

🔒 = exige `Authorization: Bearer <token>`. O token vem de `POST /api/login`
(`{"email", "password"}`) e vale `AUTH_TOKEN_TTL` segundos:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:3000/api/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"leonan@fullcycle.com.br","password":"..."}' | jq -r .token)
curl -s http://127.0.0.1:3000/api/admin/financial-report -H "Authorization: Bearer $TOKEN"
```

A imposição vem ligada (`AUTH_ENFORCED=true`): sem o header essas duas rotas
respondem 401. Suba com `AUTH_ENFORCED=false` para restaurar o contrato original
durante uma migração — o acesso anônimo passa a ser registrado como `WARN`.
Sem `AUTH_SECRET` no ambiente, o boot gera uma chave efêmera e os tokens não
sobrevivem a um restart.

Na refatoração: matrículas e pagamentos passaram a ser removidos em cascata junto
com o usuário, e o número do cartão é mascarado no log. Ver
[`reports/audit-project-2.md`](../reports/audit-project-2.md).

## A skill

`.claude/skills/refactor-arch/` — invocação: `claude "/refactor-arch"`
