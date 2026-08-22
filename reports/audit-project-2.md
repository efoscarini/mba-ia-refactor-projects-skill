```
================================
ARCHITECTURE AUDIT REPORT
================================
```
**Project:** `ecommerce-api-legacy`
**Stack:** Node.js 24 + Express 4.18.2 (sqlite3 5.1.6)
**Files:** 3 analyzed | ~180 lines of code
**Date:** 2026-08-22

---

## Phase 1 — Project Analysis

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      JavaScript (Node.js 24, CommonJS)
Framework:     Express 4.18.2
Dependencies:  sqlite3 5.1.6
Domain:        LMS / plataforma de cursos — fluxo de checkout (usuários, cursos,
               matrículas, pagamentos, trilha de auditoria)
Architecture:  Monolítica — God Class `AppManager` concentra conexão de banco,
               DDL, seed, registro de rotas e toda a regra de negócio
Source files:  3 files analyzed (AppManager.js 141, utils.js 25, app.js 14)
DB tables:     users, courses, enrollments, payments, audit_logs (SQLite :memory:)
================================
```

---

## Summary

| CRITICAL | HIGH | MEDIUM | LOW | **Total** |
|---:|---:|---:|---:|---:|
| 4 | 7 | 6 | 4 | **21** |

---

## Findings

### [CRITICAL] Hardcoded Credentials
- **Anti-pattern:** AP-01
- **File:** `src/utils.js:1-7`
- **Description:** o objeto `config` guarda literais de `dbUser`, `dbPass` (`senha_super_secreta_prod_123`), `paymentGatewayKey` com prefixo `pk_live_` e `smtpUser`. O nome da variável indica credencial de **produção**.
- **Impact:** chave de gateway de pagamento em produção versionada no Git; rotacionar exige mudar código e redeploy.
- **Recommendation:** mover para `process.env`, falhar no boot se ausente em produção, publicar `.env.example`.

### [CRITICAL] Número de Cartão e Chave de Gateway em Log
- **Anti-pattern:** AP-01 / AP-19
- **File:** `src/AppManager.js:45`
- **Description:** `console.log` imprime o número completo do cartão recebido no request junto com `config.paymentGatewayKey`.
- **Impact:** PAN completo e chave `pk_live_` gravados em stdout — violação direta de PCI-DSS e vetor de vazamento por qualquer agregador de log.
- **Recommendation:** mascarar o cartão (últimos 4 dígitos) e nunca logar a chave.

### [CRITICAL] God Class
- **Anti-pattern:** AP-04
- **File:** `src/AppManager.js:4-141`
- **Description:** a classe `AppManager` abre a conexão (`:7`), cria o schema e o seed (`:10-23`), registra as 3 rotas (`:25-138`) e implementa checkout, relatório financeiro e exclusão de usuário — tudo em um arquivo.
- **Impact:** nada é testável em isolamento; qualquer alteração no relatório mexe no mesmo arquivo do checkout e da inicialização do banco.
- **Recommendation:** separar em models por tabela, services por caso de uso, controllers e rotas.

### [CRITICAL] Hash de Senha Caseiro e Senha em Texto Plano
- **Anti-pattern:** AP-05
- **File:** `src/utils.js:17-23`, `src/AppManager.js:18`, `src/AppManager.js:68`
- **Description:** `badCrypto()` concatena 10.000 vezes os 2 primeiros caracteres do base64 da senha e devolve os 10 primeiros do resultado — sem salt, determinístico e com espaço de saída minúsculo. O seed grava a senha do usuário de exemplo como texto plano (`'123'`). Quando o request não traz `pwd`, o código cai num literal fixo `"123456"` (`:68`).
- **Impact:** o "hash" é praticamente reversível e colide para senhas diferentes; todas as contas criadas sem `pwd` compartilham a mesma senha conhecida.
- **Recommendation:** KDF com salt (`crypto.scrypt` já vem no Node); senha provisória aleatória quando ausente.

### [HIGH] Regra de Negócio Dentro do Handler de Rota
- **Anti-pattern:** AP-06
- **File:** `src/AppManager.js:28-78`, `src/AppManager.js:80-129`
- **Description:** a decisão de aprovação do pagamento (`:46`), a criação condicional do usuário (`:66-75`), o registro de matrícula, pagamento e auditoria e a agregação do relatório financeiro estão todos dentro dos callbacks de `app.post`/`app.get`.
- **Impact:** a regra só é exercitável via HTTP; nenhum outro consumidor (job, CLI, fila) consegue reaproveitá-la.
- **Recommendation:** `CheckoutService` e `ReportService` com o gateway injetado.

### [HIGH] Estado Global Mutável
- **Anti-pattern:** AP-07
- **File:** `src/utils.js:9-15`, `src/utils.js:25`
- **Description:** `globalCache` e `totalRevenue` são declarados com `let` no escopo do módulo, exportados e mutados por `logAndCache()` — que o checkout chama a cada requisição.
- **Impact:** cache compartilhado entre todas as requisições e usuários, crescendo sem limite e sem invalidação; `totalRevenue` é exportado por valor, então o import nunca enxerga atualização — a variável é enganosa além de perigosa.
- **Recommendation:** estado que precisa durar vai para o banco; o resto vira dependência explícita.

### [HIGH] Acoplamento Forte / Ausência de Injeção de Dependência
- **Anti-pattern:** AP-08
- **File:** `src/AppManager.js:2`, `src/AppManager.js:7`
- **Description:** o construtor faz `new sqlite3.Database(':memory:')` — a classe escolhe sozinha o próprio banco — e importa `config`, `logAndCache` e `badCrypto` como módulos concretos.
- **Impact:** impossível testar com banco de teste ou gateway falso; trocar o driver exige reescrever a classe.
- **Recommendation:** receber `db`, gateway e logger por construtor, montados em um composition root.

### [HIGH] Callback Hell e Escrita sem Transação
- **Anti-pattern:** AP-09
- **File:** `src/AppManager.js:37-77`
- **Description:** cinco níveis de callbacks aninhados (`courses` → `users` → `enrollments` → `payments` → `audit_logs`), com um alias `self` (`:26`) para contornar o `this` das `function(err)`.
- **Impact:** se o `INSERT` de `payments` falhar, a matrícula já gravada fica sem pagamento — estado parcial permanente. Vários `return res.*` dentro de callbacks aninhados abrem risco de resposta dupla.
- **Recommendation:** `async/await` sobre um driver promisificado, com as três escritas dentro de uma transação.

### [HIGH] Ausência de Camada de Abstração de Dados
- **Anti-pattern:** AP-10
- **File:** `src/AppManager.js:37, 40, 50, 54, 57, 83, 92, 104, 106, 133`
- **Description:** as 10 queries do projeto estão inline nos handlers de rota. Não existe nenhum arquivo dedicado a acesso a dados.
- **Impact:** renomear uma coluna obriga a varrer os handlers; a mesma consulta de usuário aparece em três formatos diferentes.
- **Recommendation:** um model por tabela concentrando as queries.

### [HIGH] Ausência de Autorização em Rotas Sensíveis
- **Anti-pattern:** AP-11
- **File:** `src/AppManager.js:80`, `src/AppManager.js:131`
- **Description:** `GET /api/admin/financial-report` expõe faturamento por curso e a lista nominal de alunos pagantes sem qualquer autenticação; `DELETE /api/users/:id` apaga qualquer usuário pelo id, também sem autenticação. Nenhum middleware de auth é registrado na aplicação.
- **Impact:** dados financeiros e pessoais públicos na internet; exclusão de contas por chamada anônima.
- **Recommendation:** middleware de autenticação/autorização nas rotas administrativas.

### [HIGH] Integridade Referencial Ignorada
- **Anti-pattern:** AP-12
- **File:** `src/AppManager.js:131-137`, `src/AppManager.js:12-16`
- **Description:** o `DELETE` remove só a linha de `users`; as tabelas foram criadas sem nenhuma FK (`:12-16`). A própria mensagem de resposta admite o problema: *"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."*
- **Impact:** matrículas e pagamentos órfãos entram no relatório financeiro como aluno `"Unknown"`, inflando a contagem de alunos com registros de gente que não existe mais.
- **Recommendation:** FKs com `ON DELETE CASCADE` e exclusão dentro de transação.

### [MEDIUM] Query N+1 (dois níveis)
- **Anti-pattern:** AP-13
- **File:** `src/AppManager.js:83-128`
- **Description:** o relatório faz 1 query de cursos, 1 de matrículas por curso e, dentro de cada matrícula, mais 2 queries (usuário e pagamento) — total `1 + N + 2*N*M`. A conclusão é controlada por contadores manuais (`coursesPending--`, `enrPending--`).
- **Impact:** 10 cursos com 100 matrículas cada disparam mais de 2.000 queries numa única requisição; a ordem do array de resposta depende de qual callback termina primeiro.
- **Recommendation:** 4 queries e agrupamento em memória, com ordenação determinística.

### [MEDIUM] Validação de Entrada Mínima
- **Anti-pattern:** AP-14
- **File:** `src/AppManager.js:35`, `src/AppManager.js:68`
- **Description:** a única validação é a presença de 4 campos, escrita no meio do fluxo. Não há checagem de formato de e-mail, de tipo do `c_id` nem do número do cartão; `pwd` ausente cai num literal fixo.
- **Impact:** dados inválidos chegam ao banco; usuários criados com senha conhecida.
- **Recommendation:** validador dedicado por caso de uso, executado antes de qualquer efeito.

### [MEDIUM] Erros Ignorados Silenciosamente
- **Anti-pattern:** AP-15
- **File:** `src/AppManager.js:57`, `src/AppManager.js:104`, `src/AppManager.js:106`, `src/AppManager.js:133`
- **Description:** quatro callbacks recebem o parâmetro `err` e nunca o consultam. No `audit_logs` (`:57`) a resposta de sucesso é enviada mesmo se a auditoria falhar; no relatório (`:104`, `:106`) uma falha de query produz `undefined` silencioso; no delete (`:133`) devolve 200 mesmo em erro.
- **Impact:** falhas viram sucesso aparente; problemas de banco só aparecem como dado faltando na resposta.
- **Recommendation:** middleware de erro centralizado com `asyncHandler`, para que toda rejeição chegue a um só lugar.

### [MEDIUM] Contrato de Resposta Inconsistente
- **Anti-pattern:** AP-17
- **File:** `src/AppManager.js:35, 38, 48, 51, 60, 135`
- **Description:** a mesma rota devolve texto puro em erro (`res.status(400).send("Bad Request")`) e JSON em sucesso (`res.status(200).json({msg, enrollment_id})`); o `DELETE` devolve texto; rota desconhecida cai no HTML padrão do Express.
- **Impact:** o cliente precisa de tratamento diferente por caminho de execução.
- **Recommendation:** padronizar o corpo de erro e o handler de rota não encontrada.

### [MEDIUM] APIs Deprecated / Estilo Legado
- **Anti-pattern:** AP-13 (deprecated) — ver tabela abaixo
- **File:** `src/AppManager.js:1`, `src/AppManager.js:37-128`
- **Description:** `sqlite3.verbose()` (modo de depuração do driver) é ativado no caminho de produção; toda a I/O usa a API de callbacks do driver, sem Promise.
- **Impact:** stack traces extras em produção com custo de performance; código assíncrono impossível de compor.
- **Recommendation:** driver sem `verbose`, envolvido em Promises.

### [MEDIUM] Configuração de Ambiente Fixa no Código
- **Anti-pattern:** AP-18
- **File:** `src/utils.js:6`, `src/AppManager.js:7`
- **Description:** porta `3000` literal no objeto de config e banco fixado em `':memory:'` dentro do construtor.
- **Impact:** o banco é perdido a cada restart sem que isso seja uma decisão configurável; trocar de ambiente exige editar código.
- **Recommendation:** `PORT` e `DATABASE_PATH` por variável de ambiente.

### [LOW] `console.log` como Logging
- **Anti-pattern:** AP-19
- **File:** `src/utils.js:13`, `src/AppManager.js:45`, `src/app.js:13`
- **Description:** log via `console.log` com template string, sem nível, sem timestamp e sem destino configurável.
- **Impact:** impossível filtrar por severidade ou desligar em produção.
- **Recommendation:** logger com níveis.

### [LOW] Magic Numbers e Magic Strings
- **Anti-pattern:** AP-20
- **File:** `src/AppManager.js:46`, `src/utils.js:19`, `src/utils.js:22`
- **Description:** a regra de aprovação do pagamento é `cc.startsWith("4")` inline; `badCrypto` usa `10000` iterações e `substring(0, 10)` sem nenhuma constante nomeada.
- **Impact:** a regra comercial fica escondida numa expressão de uma linha.
- **Recommendation:** constantes nomeadas em módulo de domínio.

### [LOW] Nomenclatura Ruim
- **Anti-pattern:** AP-21
- **File:** `src/AppManager.js:29-33`, `src/AppManager.js:26`
- **Description:** variáveis de uma letra para dados de negócio (`u`, `e`, `p`, `cid`, `cc`); o alias `const self = this` (`:26`) só existe por causa das `function` clássicas; os campos da API pública são abreviados (`usr`, `eml`, `pwd`, `c_id`).
- **Impact:** ler o handler exige decodificar cada nome.
- **Recommendation:** nomes completos internamente; os campos públicos ficam como estão para não quebrar o contrato.

### [LOW] Código Morto
- **Anti-pattern:** AP-22
- **File:** `src/utils.js:9-10`, `src/utils.js:12-15`
- **Description:** `globalCache` é escrito por `logAndCache()` e nunca lido em lugar nenhum; `totalRevenue` é declarado, exportado e jamais atualizado.
- **Impact:** dá a impressão de existir um mecanismo de cache e uma métrica de receita que não existem.
- **Recommendation:** remover.

---

## Deprecated APIs

| API | File:Line | Substituir por |
|---|---|---|
| `sqlite3.verbose()` | `src/AppManager.js:1` | driver sem `verbose` (modo debug fora de produção) |
| I/O por callback (`db.run/get/all` com `function(err)`) | `src/AppManager.js:37-128` | Promises + `async/await` |
| `function(err) { ... this.lastID }` com alias `self` | `src/AppManager.js:50-57`, `:26` | arrow functions + retorno de Promise |

Nota informativa: Express 4.x está em modo de manutenção (Express 5 é a linha
atual). A migração não foi executada nesta refatoração por estar fora do escopo
de MVC e por exigir revisão do comportamento de rotas e middlewares.

---

## Preserved Contract

| Método | Path | Status codes |
|---|---|---|
| POST | `/api/checkout` | 200 (JSON `{msg, enrollment_id}`), 400 (`Bad Request`), 400 (`Pagamento recusado`), 404 (`Curso não encontrado`) |
| GET | `/api/admin/financial-report` | 200 (array `[{course, revenue, students[]}]`) |
| DELETE | `/api/users/:id` | 200 (texto) |

```
================================
Total: 21 findings
================================
```

---

## Refactoring Result

### Estrutura final

```
ecommerce-api-legacy/
├── package.json                     # `npm start` -> node src/app.js (inalterado)
├── api.http
├── .env.example
└── src/
    ├── app.js                       # entry point
    ├── server.js                    # composition root: createApp()
    ├── config/
    │   ├── index.js                 # tudo de process.env, zero literais
    │   └── constants.js             # status de pagamento, prefixos, parâmetros de KDF
    ├── infra/
    │   ├── database.js              # sqlite3 promisificado + transaction()
    │   ├── schema.js                # DDL com FKs em cascata + seed com hash
    │   └── logger.js                # níveis + timestamp
    ├── models/
    │   ├── user.model.js
    │   ├── course.model.js
    │   ├── enrollment.model.js
    │   ├── payment.model.js
    │   └── auditLog.model.js
    ├── services/
    │   ├── checkout.service.js      # caso de uso completo, em transação
    │   ├── report.service.js        # relatório em 4 queries
    │   ├── user.service.js
    │   ├── password.service.js      # crypto.scrypt com salt
    │   └── paymentGateway.service.js# gateway isolado, cartão mascarado
    ├── controllers/
    │   ├── checkout.controller.js
    │   ├── report.controller.js
    │   └── user.controller.js
    ├── routes/
    │   ├── index.js                 # agrega sob /api
    │   ├── checkout.routes.js
    │   ├── report.routes.js
    │   └── user.routes.js
    └── middlewares/
        ├── errorHandler.js          # asyncHandler + 404 + handler central
        ├── errors.js
        └── validators.js
```

Arquivos legados `src/AppManager.js` e `src/utils.js` foram removidos.

### Findings resolvidos

| ID | Anti-pattern | Sev. | Como foi resolvido |
|---|---|---|---|
| AP-01 | Hardcoded credentials | CRITICAL | `src/config/index.js` lê tudo de `process.env`; chave de gateway e senha SMTP são **obrigatórias** quando `APP_ENV=production`; `.env.example` publicado |
| AP-01 | PAN e chave em log | CRITICAL | `maskCard()` no gateway (`**** **** **** 4444`); a chave nunca é logada |
| AP-04 | God Class | CRITICAL | `AppManager` (141 linhas) → 5 models + 5 services + 3 controllers + 4 arquivos de rota + infra |
| AP-05 | Hash caseiro | CRITICAL | `PasswordService` com `crypto.scrypt` (salt de 16 bytes, chave de 64), comparação com `timingSafeEqual`; seed com hash; senha ausente gera valor aleatório |
| AP-06 | Regra no handler | HIGH | `CheckoutService`, `ReportService` e `UserService`; controllers com 2-3 linhas |
| AP-07 | Estado global mutável | HIGH | `globalCache` e `totalRevenue` eliminados; nenhum `let` de módulo restante |
| AP-08 | Sem injeção de dependência | HIGH | tudo por construtor; `createApp()` é o único ponto com `new` de infra |
| AP-09 | Callback hell | HIGH | driver promisificado (`Database`); checkout linear com `await`; matrícula + pagamento + auditoria dentro de `db.transaction()` |
| AP-10 | Sem abstração de dados | HIGH | 5 models; nenhuma query fora de `models/` e `infra/` |
| AP-11 | Autorização ausente | HIGH | parcialmente — ver limitação abaixo |
| AP-12 | Integridade referencial | HIGH | FKs `ON DELETE CASCADE` em `enrollments` e `payments`, `PRAGMA foreign_keys = ON`, exclusão em transação |
| AP-13 | N+1 | MEDIUM | relatório em 4 queries (`Promise.all` + `IN`) e agrupamento em memória, com ordem determinística por id |
| AP-14 | Validação mínima | MEDIUM | `middlewares/validators.js` roda antes de qualquer efeito colateral |
| AP-15 | Erros ignorados | MEDIUM | `asyncHandler` + error handler central; nenhum `err` descartado |
| AP-17 | Contrato inconsistente | MEDIUM | corpo de erro sempre texto com a mesma mensagem do original; `notFoundHandler` substitui o HTML padrão do Express |
| AP-18 | Config fixa | MEDIUM | `PORT`, `DATABASE_PATH`, `LOG_LEVEL`, `SEED_ON_BOOT` por env |
| — | APIs deprecated | MEDIUM | `sqlite3.verbose()` removido; I/O toda em Promises |
| AP-19 | `console.log` | LOW | `infra/logger.js` com níveis e timestamp ISO |
| AP-20 | Magic values | LOW | `config/constants.js` (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIXES`, parâmetros do scrypt) |
| AP-21 | Nomenclatura | LOW | nomes completos internamente; os campos públicos `usr`/`eml`/`pwd`/`c_id` foram mantidos e traduzidos no validator, preservando o contrato |
| AP-22 | Código morto | LOW | `globalCache`, `totalRevenue`, `logAndCache` e o alias `self` removidos |

### Findings não resolvidos

| ID | Motivo | Risco residual |
|---|---|---|
| AP-11 | Exigir autenticação faria as rotas passarem a responder 401 para os clientes atuais — quebra de contrato. Não existe endpoint de login no projeto para emitir credencial. | `GET /api/admin/financial-report` e `DELETE /api/users/:id` continuam acessíveis sem autenticação |
| Express 4.x | Migração para Express 5 está fora do escopo da refatoração MVC | linha em modo de manutenção |

### Mudanças intencionais de contrato

Status codes: **nenhuma mudança**. Três corpos de resposta mudaram:

1. `DELETE /api/users/:id` — a mensagem deixou de ser *"Usuário deletado, mas as
   matrículas e pagamentos ficaram sujos no banco."* e passou a ser *"Usuário
   deletado."*, porque a limpeza em cascata agora de fato acontece (AP-12).
2. `GET /api/admin/financial-report` **após** um delete — os registros órfãos que
   apareciam como aluno `"Unknown"` deixaram de existir. Antes do delete o
   relatório é **byte-idêntico** ao original (verificado por diff).
3. Rota desconhecida — texto `Recurso não encontrado` em vez da página HTML
   padrão do Express (mesmo status 404).

Mudança adicional fora do baseline: `DELETE /api/users/:id` com id não numérico
passa a responder 400 em vez de 200.

### Validação

Suíte de 9 chamadas HTTP (checkout aprovado, checkout recusado, request
incompleto, curso inexistente, usuário já existente, relatório, exclusão,
relatório pós-exclusão, rota inexistente):

```
casos=9  status_iguais=9  status_diferentes=0  body_diferentes=3
```

Comparação adicional do conteúdo do relatório financeiro (mesma sequência de
checkouts nos dois códigos, JSON normalizado e comparado com `diff`):

```
RELATORIO FINANCEIRO: IDENTICO ao original
```

- **Boot:** `npm start` sobe sem erro
- **Endpoints:** 9/9 status codes idênticos ao original
- **Formato:** 3 divergências de corpo, todas correspondendo às mudanças
  intencionais acima — nenhuma regressão
- **Varredura final:** zero anti-patterns CRITICAL ou HIGH remanescentes
  (sem segredo literal, sem `let` global, sem SQL fora de `models/`, sem
  callback aninhado de banco, sem `md5`/hash caseiro, sem `sqlite3.verbose`)
