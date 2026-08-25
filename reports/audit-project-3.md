```
================================
ARCHITECTURE AUDIT REPORT
================================
```
**Project:** `task-manager-api`
**Stack:** Python 3.13 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
**Files:** 11 analyzed | ~1150 lines of code
**Date:** 2026-08-22

---

## Phase 1 — Project Analysis

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13
Framework:     Flask 3.0.0
Dependencies:  flask-sqlalchemy 3.1.1, flask-cors 4.0.0, marshmallow 3.20.1,
               requests 2.31.0, python-dotenv 1.0.0
               (marshmallow, requests e python-dotenv declarados e nunca importados)
Domain:        Task Manager — gestão de tarefas com usuários, categorias,
               prioridades, prazos e relatórios de produtividade
Architecture:  Camadas parciais — existem models/, routes/, services/ e utils/,
               mas NÃO existe camada de controllers: os blueprints acumulam
               validação, acesso ao ORM, regra de negócio e serialização.
               `services/notification_service.py` nunca é importado por ninguém.
Source files:  11 files analyzed (routes 733, models 119, utils 116, seed 99,
               services 48, app 34, database 3)
DB tables:     tasks, users, categories (SQLite via SQLAlchemy)
================================
```

> Observação da Fase 1: pastas com o nome certo não significam camadas. Abrindo
> os arquivos, `routes/` faz o trabalho de controller **e** de model, e a única
> classe em `services/` é código morto.

---

## Summary

| CRITICAL | HIGH | MEDIUM | LOW | **Total** |
|---:|---:|---:|---:|---:|
| 2 | 6 | 6 | 4 | **18** |

---

## Findings

### [CRITICAL] Hardcoded Credentials
- **Anti-pattern:** AP-01
- **File:** `app.py:13`, `services/notification_service.py:7-10`
- **Description:** `app.config['SECRET_KEY'] = 'super-secret-key-123'` literal no entrypoint; o `NotificationService` guarda host, porta, usuário (`taskmanager@gmail.com`) e senha (`senha123`) de SMTP fixos no construtor.
- **Impact:** chave de sessão e credencial de e-mail versionadas no Git; rotação exige mudar código.
- **Recommendation:** `os.environ` para todos os valores, falhando no boot em produção; `.env.example` publicado.

### [CRITICAL] Hash MD5 sem Salt e Senha Exposta pela API
- **Anti-pattern:** AP-05
- **File:** `models/user.py:21`, `models/user.py:27-32`, `routes/user_routes.py:33, 85, 129, 209`
- **Description:** `set_password` e `check_password` usam `hashlib.md5` sem salt (`models/user.py:29, 32`). Pior: `to_dict()` inclui o campo `password` (`:21`), e esse dicionário é devolvido por `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e pelo **`POST /login`**.
- **Impact:** MD5 sem salt cai em rainbow table em segundos; e a API entrega o hash de qualquer usuário sem exigir autenticação nenhuma.
- **Recommendation:** KDF com salt (`werkzeug.security`) e o campo `password` fora do serializer.

### [HIGH] Regra de Negócio Dentro das Rotas
- **Anti-pattern:** AP-06
- **File:** `routes/report_routes.py:12-101`, `routes/task_routes.py:11-63`, `routes/task_routes.py:273-299`, `routes/user_routes.py:153-183`
- **Description:** `summary_report` tem 90 linhas dentro do handler — 14 queries de contagem, cálculo de atraso, produtividade por usuário e montagem do payload. `get_tasks` e `task_stats` fazem o mesmo em menor escala.
- **Impact:** a regra de produtividade e de atraso só roda via HTTP; não há como reaproveitá-la em job ou export.
- **Recommendation:** `ReportService` e `TaskService`, com o handler apenas orquestrando.

### [HIGH] Ausência da Camada de Controllers
- **Anti-pattern:** AP-04
- **File:** `routes/task_routes.py:1-299`, `routes/user_routes.py:1-211`, `routes/report_routes.py:1-223`
- **Description:** os três blueprints acumulam roteamento, validação, acesso ao ORM, regra de negócio e serialização. O arquivo `report_routes.py` inclusive hospeda o CRUD de categorias (`:157-223`), que não é relatório.
- **Impact:** um arquivo de "rotas" com 299 linhas não é testável sem cliente HTTP; recursos diferentes vivem no mesmo módulo.
- **Recommendation:** rotas só mapeiam; controllers orquestram; um módulo por recurso.

### [HIGH] Acesso a Dados Espalhado pelas Rotas
- **Anti-pattern:** AP-10
- **File:** `routes/task_routes.py:14, 42, 51, 67, 117, 122, 158, 247, 275-281`, `routes/user_routes.py:12, 29, 35, 67, 94, 109, 140, 159, 197`, `routes/report_routes.py:15-56, 109, 159, 163`
- **Description:** `Task.query`, `User.query`, `Category.query` e `db.session` são chamados diretamente de dentro dos handlers, em mais de 30 pontos.
- **Impact:** renomear uma coluna obriga a varrer os três arquivos de rota; a mesma consulta aparece em variações ligeiramente diferentes.
- **Recommendation:** concentrar as consultas nos models.

### [HIGH] Autorização Ausente e Token Falso
- **Anti-pattern:** AP-11
- **File:** `routes/user_routes.py:210`, `routes/user_routes.py:10, 134`, `routes/report_routes.py:12`
- **Description:** o login devolve `'fake-jwt-token-' + str(user.id)` — um "token" previsível que nenhuma rota verifica. Não existe middleware de autenticação: `GET /users`, `DELETE /users/<id>` e `/reports/summary` são públicos.
- **Impact:** qualquer chamador anônimo lista usuários, apaga contas e lê o relatório de produtividade da equipe.
- **Recommendation:** token assinado de verdade e middleware de autorização nas rotas sensíveis.

### [HIGH] Estado Mutável em Memória
- **Anti-pattern:** AP-07
- **File:** `services/notification_service.py:6`, `services/notification_service.py:31-36`
- **Description:** `self.notifications = []` acumula notificações num atributo de instância que serviria de "banco" para o método `get_notifications` (`:43-47`).
- **Impact:** o histórico se perde a cada restart e não é compartilhado entre workers; com múltiplos processos cada um vê uma lista diferente.
- **Recommendation:** persistir em tabela ou apenas registrar em log.

### [HIGH] Acoplamento e Serviço Morto
- **Anti-pattern:** AP-08
- **File:** `services/notification_service.py:1-48`, `routes/task_routes.py:1-7`, `routes/user_routes.py:1-6`
- **Description:** o `NotificationService` instancia sozinho a conexão SMTP a partir de literais e **nunca é importado por nenhum módulo** — está fora do fluxo da aplicação. As rotas, por sua vez, importam `db` e os models como módulos concretos, sem nenhum ponto de composição.
- **Impact:** existe uma camada `services/` que não presta serviço nenhum; e nada pode ser substituído por dublê em teste.
- **Recommendation:** dependências por construtor, montadas em um `create_app()`; ligar o serviço de notificação ao fluxo real ou removê-lo.

### [MEDIUM] Query N+1
- **Anti-pattern:** AP-13
- **File:** `routes/task_routes.py:41-57`, `routes/user_routes.py:22`, `routes/report_routes.py:53-68`, `routes/report_routes.py:157-165`
- **Description:** `get_tasks` executa `User.query.get` e `Category.query.get` dentro do laço de tarefas (2 queries por task); `get_users` usa `len(u.tasks)`, que dispara lazy load por usuário; `summary_report` roda uma query de tarefas por usuário; `get_categories` roda um `COUNT` por categoria.
- **Impact:** `GET /tasks` com 500 tarefas dispara mais de 1.000 queries.
- **Recommendation:** carregar os relacionados em lote e agrupar em memória; contagens via `GROUP BY`.

### [MEDIUM] Validação Duplicada e Validador Morto
- **Anti-pattern:** AP-14
- **File:** `routes/task_routes.py:89-144` vs `routes/task_routes.py:166-213`, `routes/user_routes.py:54-72` vs `routes/user_routes.py:102-125`, `utils/helpers.py:57-108`
- **Description:** a validação de task e de usuário é reescrita entre POST e PUT com pequenas diferenças de mensagem; a regex de e-mail aparece literal duas vezes (`user_routes.py:61` e `:106`). Ao mesmo tempo, `utils/helpers.py:57-108` traz um `process_task_data()` de 52 linhas que faz exatamente essa validação e **não é importado por nenhuma rota**.
- **Impact:** as duas cópias já divergiram nas mensagens; o validador "oficial" apodrece sem uso.
- **Recommendation:** uma função de validação por entidade, usada por criação e atualização.

### [MEDIUM] `except:` sem Tipo
- **Anti-pattern:** AP-15
- **File:** `routes/task_routes.py:62, 236`, `routes/user_routes.py:130, 149`, `routes/report_routes.py:186, 204, 218`, `utils/helpers.py:46-50, 88`
- **Description:** nove blocos capturam **qualquer** exceção sem tipo e devolvem uma mensagem genérica. `get_tasks` (`:62`) engole a falha e responde `{'error': 'Erro interno'}` sem log algum.
- **Impact:** `except:` captura inclusive `KeyboardInterrupt` e erros de programação; um `AttributeError` vira "Erro interno" silencioso, impossível de diagnosticar.
- **Recommendation:** error handler centralizado, com log do stack trace.

### [MEDIUM] Código Duplicado
- **Anti-pattern:** AP-16
- **File:** `routes/task_routes.py:30-39, 71-80, 284-287`, `routes/user_routes.py:171-180`, `routes/report_routes.py:34-43, 132-135`, `models/task.py:50-59`
- **Description:** o cálculo de "task atrasada" está reescrito **seis vezes**, sempre com o mesmo `if` triplo aninhado — e existe um `Task.is_overdue()` em `models/task.py:50-59` que faz isso e nunca é chamado. A serialização de task também é remontada campo a campo em `task_routes.py:17-28` e `user_routes.py:162-169`, duplicando `to_dict()`.
- **Impact:** mudar a definição de atraso exige achar as seis cópias; foi assim que `to_dict` acabou divergindo entre rotas.
- **Recommendation:** usar os métodos que já existem no model e apagar as cópias.

### [MEDIUM] Integridade Referencial Frágil
- **Anti-pattern:** AP-12
- **File:** `routes/user_routes.py:140-142`, `routes/report_routes.py:211-223`
- **Description:** o cascade de usuário → tasks é feito à mão em um laço Python, sem transação explícita e sem declaração de cascade no ORM; a exclusão de categoria (`report_routes.py:211-223`) não trata as tasks que apontam para ela.
- **Impact:** tasks ficam com `category_id` apontando para uma categoria inexistente, e `GET /tasks` passa a devolver `category_name: null` sem explicação.
- **Recommendation:** cascade declarado no relacionamento e exclusão dentro de transação.

### [MEDIUM] Configuração de Ambiente Fixa no Código
- **Anti-pattern:** AP-18
- **File:** `app.py:11-13`, `app.py:15`, `app.py:34`
- **Description:** URI do banco, `SECRET_KEY` e `TRACK_MODIFICATIONS` literais; `CORS(app)` libera qualquer origem; `app.run(debug=True, host='0.0.0.0', port=5000)` com debug ligado incondicionalmente. O `python-dotenv` está no `requirements.txt` e nunca é carregado.
- **Impact:** o debugger do Werkzeug exposto em todas as interfaces é um console de execução remota de Python.
- **Recommendation:** tudo por variável de ambiente, com debug desligado por padrão.

### [LOW] `print` como Logging
- **Anti-pattern:** AP-19
- **File:** `routes/task_routes.py:149, 153, 219, 234`, `routes/user_routes.py:83, 89, 147`, `utils/helpers.py:39-41`
- **Description:** oito `print` em caminho de produção; `user_routes.py:83` imprime id e nome do usuário recém-criado.
- **Impact:** sem nível, sem timestamp, sem destino configurável.
- **Recommendation:** módulo `logging`.

### [LOW] Magic Numbers e Constantes Órfãs
- **Anti-pattern:** AP-20
- **File:** `utils/helpers.py:110-116`, `routes/task_routes.py:96, 99, 110, 113`, `routes/user_routes.py:64, 71`, `routes/report_routes.py:24-28`
- **Description:** o arquivo `utils/helpers.py:110-116` **define** `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH`, `MIN_TITLE_LENGTH`, `MIN_PASSWORD_LENGTH`, `DEFAULT_PRIORITY` e `DEFAULT_COLOR` — e nenhuma rota as importa. Os mesmos valores aparecem repetidos como literais nos handlers, e o mapa de prioridade → rótulo (`critical`/`high`/`medium`...) está escrito à mão em `report_routes.py:83-89`.
- **Impact:** existem duas fontes de verdade para os mesmos limites, e a que está documentada é a que ninguém usa.
- **Recommendation:** um módulo de constantes efetivamente importado por todos.

### [LOW] Imports e Código Morto
- **Anti-pattern:** AP-22
- **File:** `app.py:7`, `routes/task_routes.py:7`, `routes/user_routes.py:6`, `routes/report_routes.py:7-8`, `models/task.py:3`, `utils/helpers.py:3-7, 31-34, 36-41, 43-50, 57-108`, `models/task.py:38-48`
- **Description:** `import os, sys, json, datetime` no `app.py` (só `datetime` é usado); `import json, os, sys, time` em `task_routes.py` — nenhum usado; `hashlib, json` em `user_routes.py` — nenhum usado; `format_date` e `calculate_percentage` importados em `report_routes.py` e não usados. Em `utils/helpers.py`, cinco imports mortos e cinco funções que ninguém chama (`generate_id`, `log_action`, `parse_date`, `is_valid_color`, `process_task_data`). Em `models/task.py`, `validate_status` e `validate_priority` nunca são chamados.
- **Impact:** metade do módulo de utilitários é peso morto que sugere funcionalidade inexistente.
- **Recommendation:** remover o que está morto e ligar o que deveria estar em uso.

### [LOW] Condicionais Redundantes
- **Anti-pattern:** AP-23
- **File:** `models/task.py:38-43`, `models/task.py:45-48`, `models/task.py:50-59`, `models/user.py:34-38`
- **Description:** padrão `if cond: return True else: return False` em quatro métodos; `is_overdue` usa três níveis de `if/else` aninhados para o que é uma expressão booleana única.
- **Impact:** verbosidade que esconde a regra.
- **Recommendation:** retornar a expressão diretamente.

---

## Deprecated APIs

| API | File:Line | Substituir por |
|---|---|---|
| `datetime.utcnow()` | `models/task.py:15, 16, 52`, `models/user.py:14`, `models/category.py:11`, `routes/task_routes.py:31, 72, 215, 285`, `routes/user_routes.py:172`, `routes/report_routes.py:35, 42, 45, 71, 133`, `utils/helpers.py:38`, `seed.py:66-75` | `datetime.now(timezone.utc)` — deprecated no Python 3.12+ |
| `Model.query` / `Query.get()` | `routes/task_routes.py:14, 42, 51, 67, 117, 122, 158, 247, 275-281`, `routes/user_routes.py:12, 29, 35, 67, 94, 109, 140, 159, 197`, `routes/report_routes.py:15-56, 109, 159, 163` | `db.session.get(Model, id)` / `db.session.execute(db.select(Model))` — API legada desde SQLAlchemy 2.0 |
| `hashlib.md5` para senha | `models/user.py:29, 32` | `werkzeug.security.generate_password_hash` |
| `type(x) == list` | `routes/task_routes.py:141, 210`, `utils/helpers.py:103` | `isinstance(x, list)` |
| `except:` sem tipo | `routes/task_routes.py:62, 236`, `routes/user_routes.py:130, 149`, `routes/report_routes.py:186, 204, 218`, `utils/helpers.py:46, 88` | `except Exception as exc:` |

---

## Preserved Contract

| Método | Path | Status codes |
|---|---|---|
| GET | `/` | 200 |
| GET | `/health` | 200 |
| GET | `/tasks` | 200 |
| POST | `/tasks` | 201, 400, 404 |
| GET | `/tasks/search` | 200 |
| GET | `/tasks/stats` | 200 |
| GET | `/tasks/<int:task_id>` | 200, 404 |
| PUT | `/tasks/<int:task_id>` | 200, 400, 404 |
| DELETE | `/tasks/<int:task_id>` | 200, 404 |
| GET | `/users` | 200 |
| POST | `/users` | 201, 400, 409 |
| GET | `/users/<int:user_id>` | 200, 404 |
| PUT | `/users/<int:user_id>` | 200, 400, 404, 409 |
| DELETE | `/users/<int:user_id>` | 200, 404 |
| GET | `/users/<int:user_id>/tasks` | 200, 404 |
| POST | `/login` | 200, 400, 401, 403 |
| GET | `/reports/summary` | 200 |
| GET | `/reports/user/<int:user_id>` | 200, 404 |
| GET | `/categories` | 200 |
| POST | `/categories` | 201, 400 |
| PUT | `/categories/<int:cat_id>` | 200, 404 |
| DELETE | `/categories/<int:cat_id>` | 200, 404 |

```
================================
Total: 18 findings
================================
```

---

## Refactoring Result

### Estrutura final

```
task-manager-api/
├── app.py                          # entry point (mantém `python app.py`)
├── seed.py                         # usa create_app() e set_password com hash
├── .env.example
├── requirements.txt
└── src/
    ├── app.py                      # composition root: create_app()
    ├── config/
    │   ├── settings.py             # tudo de os.environ, zero literais
    │   └── constants.py            # constantes agora efetivamente importadas
    ├── infra/
    │   └── database.py             # instância do SQLAlchemy
    ├── models/
    │   ├── task.py                 # entidade + is_overdue + queries agregadas
    │   ├── user.py                 # hash pbkdf2, to_dict sem password
    │   └── category.py
    ├── services/
    │   ├── task_service.py
    │   ├── user_service.py         # autenticação + token assinado
    │   ├── category_service.py
    │   ├── report_service.py       # o antigo handler de 90 linhas
    │   └── notification_service.py # configurável e ligado ao fluxo real
    ├── controllers/
    │   ├── task_controller.py
    │   ├── user_controller.py
    │   ├── category_controller.py
    │   ├── report_controller.py
    │   └── system_controller.py
    ├── views/
    │   ├── task_routes.py
    │   ├── user_routes.py
    │   ├── category_routes.py
    │   ├── report_routes.py
    │   └── system_routes.py
    ├── middlewares/
    │   ├── error_handler.py
    │   ├── errors.py
    │   └── validators.py
    └── utils/
        ├── datetime_utils.py       # utcnow() sem API deprecated
        └── helpers.py              # só o que é realmente usado
```

Diretórios legados `models/`, `routes/`, `services/`, `utils/` e o `database.py`
da raiz foram removidos.

### Findings resolvidos

| ID | Anti-pattern | Sev. | Como foi resolvido |
|---|---|---|---|
| AP-01 | Hardcoded credentials | CRITICAL | `src/config/settings.py` lê tudo de `os.environ`; SMTP configurável e notificações desligadas por padrão; `.env.example` publicado |
| AP-05 | MD5 + senha exposta | CRITICAL | `werkzeug.security` (pbkdf2 com salt); `to_dict()` não inclui mais `password` em nenhuma das 4 rotas que o vazavam |
| AP-06 | Regra nas rotas | HIGH | `TaskService`, `UserService`, `CategoryService` e `ReportService`; o `summary_report` de 90 linhas virou 1 linha de controller |
| AP-04 | Sem controllers | HIGH | 5 controllers + 5 arquivos de rota; CRUD de categorias saiu de `report_routes.py` para o seu próprio módulo |
| AP-10 | Acesso a dados espalhado | HIGH | todas as consultas concentradas nos models; zero `db.session`/`db.select` em controllers e views |
| AP-11 | Token falso e rota desprotegida | HIGH | token assinado com `itsdangerous` (`URLSafeTimedSerializer` + `SECRET_KEY`), mesmo formato de resposta; RF-15 extraiu o `AuthService` (emite **e** verifica) e pôs `require_auth` em `GET /users`, `DELETE /users/<id>`, `/reports/summary` e `/reports/user/<id>`; imposição sob `AUTH_ENFORCED` (padrão `false`) |
| AP-07 | Estado em memória | HIGH | lista `self.notifications` removida; o registro vai para o log |
| AP-08 | Acoplamento / serviço morto | HIGH | dependências por construtor; `NotificationService` recebe `settings` e passou a ser chamado pelo `TaskService` na atribuição de task |
| AP-13 | N+1 | MEDIUM | `GET /tasks` em 3 queries; `GET /users` e `GET /categories` com `COUNT` agregado por `GROUP BY`; `summary` agrupa em memória a lista já carregada |
| AP-14 | Validação duplicada | MEDIUM | `src/middlewares/validators.py`, com `parcial=True` para PUT; o `process_task_data()` morto foi eliminado |
| AP-15 | `except:` sem tipo | MEDIUM | `src/middlewares/error_handler.py`; nenhum `try/except` nos controllers; stack trace no log |
| AP-16 | Duplicação | MEDIUM | `Task.is_overdue()` passou a ser o único cálculo de atraso (antes: 6 cópias); `to_dict()` é a única serialização |
| AP-12 | Integridade referencial | MEDIUM | exclusão de usuário centralizada no `UserService`, removendo as tasks antes do usuário |
| AP-18 | Config fixa | MEDIUM | `FLASK_DEBUG`, `HOST`, `PORT`, `DATABASE_URI`, `CORS_ORIGINS`, `LOG_LEVEL` por env; debug **off** por padrão |
| AP-19 | `print` | LOW | `logging` com níveis; nenhum dado pessoal logado |
| AP-20 | Constantes órfãs | LOW | `src/config/constants.py` importado por validators, models e services; `PRIORITY_LABELS` substitui o mapa manual do relatório |
| AP-22 | Código morto | LOW | imports mortos removidos; `generate_id`, `log_action`, `is_valid_color` e `process_task_data` eliminados; `is_overdue` passou a ser usado |
| AP-23 | Condicionais redundantes | LOW | `if/else` retornando booleano trocados por retorno da expressão |
| — | APIs deprecated | — | `datetime.utcnow()` → `utcnow()` sobre `datetime.now(timezone.utc)`; `Model.query` → `db.session.get`/`db.select`; `type(x) == list` → `isinstance`; `except:` → tipado; MD5 → pbkdf2 |

**Nota sobre `datetime.utcnow()`:** a substituição direta por
`datetime.now(timezone.utc)` devolve datetime *aware* e quebraria a comparação
com os valores *naive* já gravados nas colunas `DateTime`. O helper
`src/utils/datetime_utils.utcnow()` usa a API nova e normaliza para naive-UTC,
eliminando a chamada deprecated sem migrar o schema.

### Findings não resolvidos

| ID | Motivo | Risco residual |
|---|---|---|
| AP-12 (parcial) | Excluir uma categoria continua deixando `category_id` nas tasks. Anular o campo mudaria dados que o cliente atual talvez espere preservar. | `GET /tasks` pode devolver `category_name: null` para tasks de uma categoria excluída |

> **Correção de revisão (AP-11).** O finding constava como parcial: o token já
> era assinado, mas nenhuma rota o verificava — o emissor existia sem
> verificador. A justificativa de "quebraria o contrato" mascarava a ausência de
> padrão no playbook. O RF-15 extraiu o `AuthService` (que agora emite **e**
> verifica) e protegeu as 4 rotas sensíveis. Com `AUTH_ENFORCED=false` (padrão) o
> contrato é idêntico e o acesso anônimo vira `WARN`; com `AUTH_ENFORCED=true`
> elas exigem `Bearer` token. As rotas abertas (`/tasks`, `/categories`,
> `/health`) seguem abertas nos dois modos.

### Mudanças intencionais de contrato

Status codes: **nenhuma mudança**. Duas mudanças de corpo:

1. `GET /users/<id>`, `POST /users`, `PUT /users/<id>` e `POST /login` não
   devolvem mais o campo `password` (correção CRITICAL).
2. Rota desconhecida devolve `{"error": "Recurso não encontrado"}` em JSON, em
   vez da página HTML padrão do Flask (mesmo status 404).

Mudança de valor, não de formato: o campo `token` do login deixou de ser
`fake-jwt-token-<id>` e passou a ser um token assinado — continua sendo uma
string, mesma chave, mesmo status.

### Validação

Suíte de 50 chamadas HTTP cobrindo as 22 rotas — caminho feliz, todos os erros de
validação, 404, 409 e 401:

```
casos=50  status_iguais=50  status_diferentes=0  body_diferentes=5
```

Autorização (RF-15) testada nos dois modos:

```
AUTH_ENFORCED=false (padrão)
 200 GET /users | /reports/summary | /reports/user/1 | DELETE /users/3   contrato preservado (+ WARN)

AUTH_ENFORCED=true
 401 as mesmas 4 rotas sem header                        Credencial ausente
 200 as mesmas rotas com Bearer token do /login
 401 GET /users com assinatura adulterada                "Token inválido"
 200 /health, /tasks, /tasks/stats, /categories          rotas abertas seguem abertas
```

- **Boot:** `python seed.py` e `python app.py` executam sem erro
- **Endpoints:** 50/50 status codes idênticos ao original
- **Formato:** 5 divergências de corpo — 4 são a remoção do `password` e 1 é o
  404 em JSON; nenhuma regressão
- **Varredura final:** zero anti-patterns CRITICAL ou HIGH remanescentes, e zero
  APIs deprecated (sem `datetime.utcnow`, sem `Model.query`, sem `except:` sem
  tipo, sem `type(x) ==`, sem `md5`)

**Regressão encontrada e corrigida durante a Fase 3:** ao consolidar a validação,
o `parse_date` herdado de `utils/helpers.py` aceitava `DD/MM/YYYY` como fallback —
formato que a rota original rejeitava. O smoke test pegou o caso
(`POST /tasks` com `15/01/2027` respondeu 201 em vez de 400) e o parser voltou a
ser estrito em `YYYY-MM-DD`.
