# Skill de Auditoria e Refatoração Arquitetural — `refactor-arch`

Solução do desafio de Custom Skills (o enunciado original está em [DESAFIO.md](DESAFIO.md)).

Uma skill do Claude Code que audita um projeto legado e o reestrutura para o
padrão MVC, em 3 fases: **análise da stack → relatório de auditoria (com pausa
para confirmação humana) → refatoração validada**. Foi executada nos 3 projetos
do repositório — dois Python/Flask e um Node.js/Express.

| Projeto | Stack | Findings | Status codes preservados | Relatório |
|---|---|---:|---|---|
| `code-smells-project` | Python + Flask 3.1.1 | 22 | 31/31 | [audit-project-1.md](reports/audit-project-1.md) |
| `ecommerce-api-legacy` | Node.js + Express 4.18 | 21 | 9/9 | [audit-project-2.md](reports/audit-project-2.md) |
| `task-manager-api` | Python + Flask 3.0 (SQLAlchemy) | 18 | 50/50 | [audit-project-3.md](reports/audit-project-3.md) |

---

## A) Análise Manual

Antes de escrever uma linha da skill eu li os três projetos na mão, anotando o
que doía. A ideia não era achar tudo — era entender que *tipos* de problema a
skill ia precisar reconhecer.

### `code-smells-project` (Python/Flask — API de e-commerce)

Comecei por esse. São 4 arquivos e 780 linhas; o `app.py` parece inofensivo até
você rolar até o fim.

- **[CRITICAL] `POST /admin/query` executa SQL arbitrário** (`app.py:59-78`).
  Pega o campo `sql` do corpo, manda pro banco e dá `commit` se for escrita. Sem
  autenticação. Do lado dele mora `/admin/reset-db`, que apaga as 4 tabelas —
  também aberto. Meu palpite é que nasceu como atalho de debug e ninguém tirou.
- **[CRITICAL] SQL montado com `+` em 19 lugares do `models.py`.** A pior é o
  login (`models.py:109-111`), que joga e-mail e senha crus dentro do `WHERE` —
  dá pra entrar como qualquer um com uma tautologia no campo de e-mail. As
  outras 18 concatenam ids via `str()`: menos explorável, mesma doença.
- **[CRITICAL] Senha em texto plano, e a API devolve.** O seed grava `123456`
  como está e o `to_dict` do usuário inclui o campo `senha`. `GET /usuarios`
  entrega a lista de senhas pra quem pedir. Não precisa nem invadir o banco.
- **[MEDIUM] O mesmo `try/except Exception as e` em 17 handlers**, todos
  devolvendo `str(e)` no corpo — o cliente recebe mensagem interna do SQLite com
  nome de tabela e coluna.
- **[CRITICAL] `models.py` faz tudo.** 314 linhas com SQL, regra de negócio,
  cálculo de desconto e serialização dos 4 domínios embolados. Esse é o arquivo
  que me convenceu de que a skill precisava de um playbook de "quebrar por
  camada e por domínio", não só de uma lista de smells.
- **[MEDIUM] N+1 de três níveis em `get_todos_pedidos`:** os pedidos, depois os
  itens de cada pedido, depois o nome do produto de cada item, um `execute` por
  vez. 50 pedidos de 4 itens dão ~250 queries numa rota só.
- **[MEDIUM] POST e PUT de produto divergiram.** Os dois validam, mas o PUT
  esqueceu tamanho de nome e categoria. Dá pra gravar por PUT o que o POST
  recusa — validação copiada e depois corrigida só de um lado.
- **[LOW] 17 `print` fazendo papel de log** (sem contar os dois `"=" * 50` de
  enfeite no boot). Dois imprimem e-mail de usuário.
- **[LOW] Faixas de desconto como literais soltos** no meio do cálculo:
  `10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`.
- **[LOW]** `import sqlite3` no `models.py` e `import os` no `database.py`, os
  dois sem uso.

### `ecommerce-api-legacy` (Node.js/Express — LMS com checkout)

Bem menor — 3 arquivos, 180 linhas — e bem pior por linha.

- **[CRITICAL] Credenciais de produção literais no `utils.js:1-7`:** senha de
  banco, usuário SMTP e uma chave de gateway com prefixo `pk_live_`. O nome da
  variável diz `prod`. Está versionado.
- **[CRITICAL] O número do cartão vai pro log.** `AppManager.js:45` imprime o
  PAN completo do request junto com a chave do gateway, na mesma linha.
- **[CRITICAL] Criptografia caseira.** `badCrypto()` concatena 10 mil vezes os 2
  primeiros caracteres do base64 da senha e devolve os 10 primeiros do
  resultado. Sem salt, determinístico, espaço de saída minúsculo. É pior que não
  ter hash nenhum, porque parece que tem.
- **[HIGH] Callback hell de 5 níveis no checkout, sem transação.** Se o insert
  do pagamento falhar, a matrícula já ficou gravada sozinha e ninguém desfaz.
- **[HIGH] O delete de usuário admite o próprio bug** — a resposta literalmente
  diz que *"as matrículas e pagamentos ficaram sujos no banco"*. E ficam mesmo:
  as tabelas foram criadas sem uma FK sequer.
- **[MEDIUM] Relatório financeiro com N+1 de dois níveis** e contadores manuais
  (`coursesPending--`) pra decidir a hora de responder. Como a resposta sai no
  callback que zerar o contador, a ordem do JSON depende de qual query terminar
  primeiro.
- **[MEDIUM] Quatro callbacks recebem `err` e nunca olham.**
- **[LOW] Variáveis de uma letra pra dado de negócio** — `u`, `e`, `p`, `cid`,
  `cc` (`AppManager.js:29-33`). `e` é e-mail, não erro, o que atrapalha a
  leitura justamente onde tem callback aninhado.
- **[LOW] Estado global que ninguém consome.** `globalCache` é escrito a cada
  checkout e nunca lido; `totalRevenue` é exportado e nunca atualizado. Fiquei
  um tempo procurando quem incrementava — não incrementa ninguém. É andaime
  esquecido, mas passa a impressão de que existe métrica.

### `task-manager-api` (Python/Flask — gestor de tarefas)

O "parcialmente organizado": tem `models/`, `routes/`, `services/` e `utils/`.
Foi o que mais me ensinou sobre o desafio, porque pasta com nome certo não é
camada — abrindo os arquivos, `routes/` faz o trabalho de controller e de model,
e `services/` não é importado por ninguém.

- **[CRITICAL] Senha em MD5 sem salt — e o hash sai na resposta.** O `to_dict()`
  do usuário inclui `password`, devolvido inclusive pelo `POST /login`.
- **[CRITICAL] `SECRET_KEY` e senha de SMTP hardcoded**, no `app.py` e no
  `notification_service.py`.
- **[HIGH] Não existe camada de controller.** As rotas fazem validação, ORM,
  regra e serialização. O `summary_report` tem 90 linhas dentro do handler.
- **[HIGH] Token de mentira:** o login devolve `'fake-jwt-token-' + id` e
  nenhuma rota confere. Como nenhuma rota é protegida, o token é decorativo —
  o que é pior do que não ter, porque sugere que existe autenticação.
- **[HIGH] `services/` é código morto** — `NotificationService` não é importado
  em lugar nenhum.
- **[MEDIUM] "Task atrasada" reescrito 6 vezes** ao longo das rotas, enquanto um
  `Task.is_overdue()` existe no model e ninguém chama.
- **[MEDIUM] O validador oficial também é ignorado.** `utils/helpers.py` tem um
  `process_task_data()` de 52 linhas que nenhuma rota importa; a validação está
  duplicada à mão entre POST e PUT. Pelo jeito foi escrito primeiro e as rotas
  seguiram sem ele.
- **[MEDIUM] N+1 no `GET /tasks`** (2 queries por task) e no `GET /users`, onde
  `len(u.tasks)` dispara lazy load por usuário.
- **[LOW] `except:` sem tipo em 9 pontos das `routes/`** (tem mais 3 no
  `utils/helpers.py`). Um deles engole o erro do `GET /tasks` inteiro e responde
  "Erro interno" sem logar nada — foi o que mais me irritou de depurar.
- **[LOW] Constantes declaradas e nunca importadas** (`utils/helpers.py:110-116`
  define os limites de validação; os handlers repetem os literais).
- **[LOW] `datetime.utcnow()` em 18 lugares**, deprecated desde o Python 3.12.
  Esse foi o achado que me fez incluir detecção de API obsoleta no catálogo.

> A lista completa, com arquivo, linha e impacto de cada achado, está nos
> relatórios em [`reports/`](reports/).

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                          # o prompt: 3 fases, regras invioláveis
└── references/
    ├── project-analysis.md           # heurísticas de detecção de stack
    ├── anti-patterns.md              # catálogo: 23 anti-patterns + deprecated
    ├── report-template.md            # formato do relatório
    ├── architecture-guidelines.md    # MVC alvo e responsabilidade por camada
    └── refactoring-playbook.md       # 14 transformações antes/depois
```

O `SKILL.md` é curto de propósito: ele diz **o que fazer e em que ordem**, e
aponta qual arquivo de referência abrir em cada fase. O conhecimento de domínio
(sinais de detecção, severidades, exemplos de código) fica nos arquivos de
referência, que só são lidos quando a fase precisa deles.

### Decisões de design

**As 3 fases são sequenciais e a Fase 2 é um portão.** O `SKILL.md` abre com
"Regras invioláveis", e a primeira é: nenhum arquivo é modificado antes da
confirmação humana. A Fase 2 termina com `Phase 2 complete. Proceed with
refactoring (Phase 3)? [y/n]` e uma instrução explícita de parar ali.

**Detecção pelo manifesto, nunca por suposição.** O `project-analysis.md` tem
uma tabela `arquivo encontrado → linguagem` cobrindo 10 stacks, e manda cruzar o
manifesto com os imports reais — pacote declarado e nunca importado não conta.

**Sinais de detecção acionáveis, não adjetivos.** Cada anti-pattern do catálogo
lista o que procurar no código, não uma descrição vaga. Em vez de "código ruim":
`execute("... " + var)`, `SELECT dentro de for/forEach`, `let de módulo exportado
e mutado`, `contador manual de pendência (pending--)`. Vários trazem
contraexemplo, pra não gerar falso positivo — placeholders `?`/`%s` com lista de
parâmetros **não** são finding de SQL injection.

**Severidade tabelada, com regra de desempate.** Se o problema expõe segredo ou
permite injeção, é CRITICAL independentemente do tamanho do trecho. Isso evita a
IA classificar um `secret_key` de uma linha como LOW só por ser pequeno.

**Portão de qualidade dentro da própria Fase 2.** Antes de imprimir, a skill
checa: ≥5 findings, ≥1 CRITICAL ou HIGH, todo finding com arquivo e linha. Se não
bater, a instrução é **voltar e varrer de novo** — explicitamente "não relaxe o
critério".

**A Fase 3 captura o contrato antes de mexer.** O primeiro passo é listar todas
as rotas (método + path + status codes) a partir do código. Esse baseline é o que
a validação final compara. E a ordem das transformações (config → models →
services → controllers → rotas → middlewares → app) foi escolhida pra cada etapa
deixar a aplicação executável.

### Quais anti-patterns entraram e por quê

23 anti-patterns, distribuídos por severidade. A seleção veio da análise manual —
cada um resolve algo que eu vi de fato em pelo menos um dos três projetos:

| Sev. | IDs | O que cobrem |
|---|---|---|
| CRITICAL | AP-01 a AP-05 | segredos, SQL injection, endpoint de execução arbitrária, God Class, senha insegura |
| HIGH | AP-06 a AP-12 | regra no controller, estado global, acoplamento sem DI, callback hell, falta de camada de dados, autorização ausente, integridade referencial |
| MEDIUM | AP-13 a AP-18 | N+1, validação ausente/espalhada, erro duplicado ou silencioso, duplicação, contrato inconsistente, config fixa |
| LOW | AP-19 a AP-23 | `print` como log, magic numbers, nomenclatura, código morto, condicional redundante |

Mais uma seção própria de **APIs deprecated**, com tabela por linguagem
(`datetime.utcnow`, `Model.query` do SQLAlchemy 1.x, `new Buffer`, `body-parser`,
`sqlite3.verbose`, `except:` sem tipo…). Severidade padrão MEDIUM, subindo pra
CRITICAL quando a API deprecated é o hash de senha.

O playbook tem 14 transformações (RF-01 a RF-14), todas com antes/depois de
código real, alternando Python e JavaScript de propósito — pra deixar claro que o
padrão é o mesmo e só a sintaxe muda.

### Como garanti que é agnóstica de tecnologia

1. **Zero nome de arquivo específico no `SKILL.md`.** Nada de "abra o
   `models.py`". A skill descobre os arquivos na Fase 1.
2. **Os sinais de detecção têm variantes por linguagem.** O de N+1 lista
   `for`/`forEach`/`map`; o de rota lista Flask, Express, FastAPI e Spring.
3. **Os exemplos do playbook alternam as duas linguagens.** RF-02 e RF-09 em
   Python, RF-07 e RF-08 em JavaScript, RF-13 com tabela nas duas.
4. **A estrutura alvo é definida por responsabilidade, não por nomenclatura.** O
   `architecture-guidelines.md` diz "adapte a nomenclatura à convenção da
   linguagem; o que não muda é a direção das dependências".
5. **Teste real nos 3 projetos.** A mesma pasta `.claude/skills/refactor-arch/`,
   copiada sem alteração, rodou nos três.

### Desafios encontrados

**O projeto "parcialmente organizado" quase enganou a Fase 1.** O
`task-manager-api` tem `models/`, `routes/` e `services/` — pela estrutura de
pastas, parece MVC. Foi preciso escrever no `project-analysis.md`: *"nunca
conclua que já está MVC só porque existem as pastas: abra os arquivos e confira
onde a regra de negócio realmente está"*. É o caso mais comum em legado real.

**Preservar contrato x corrigir segurança entram em conflito.** Tirar o campo
`senha` do `GET /usuarios` **é** uma quebra de contrato. Resolvi com uma regra
explícita na skill: mudanças de contrato só são permitidas quando são a própria
correção de segurança, e cada uma tem que ser listada no relatório final. Todas
as mudanças de corpo dos 3 projetos estão documentadas nos relatórios.

**Substituir API deprecated pode quebrar em runtime.** Trocar
`datetime.utcnow()` por `datetime.now(timezone.utc)` gera datetime *aware*, que
não compara com os valores *naive* já gravados — `TypeError` no primeiro
`GET /tasks`. O aviso virou nota no RF-13 do playbook, e a solução aplicada foi
um helper `utcnow()` que usa a API nova e normaliza pra naive-UTC.

**O commit condicional do SQLite quebrou o Projeto 1 na primeira execução.** A
camada de infra fazia `if not conexao.in_transaction: commit()` — mas com o
`isolation_level` padrão o `execute` já abre transação implícita, então o commit
nunca acontecia e a conexão segurava o lock (`database is locked`). O smoke test
pegou. A correção foi `isolation_level=None` com transações explícitas.

**Falso positivo na validação de data.** Ao consolidar os validadores do Projeto
3, herdei o `parse_date` do `utils/helpers.py` — que aceitava `DD/MM/YYYY` como
fallback. Só que esse helper era código morto, e a rota real aceitava apenas
`YYYY-MM-DD`. O smoke test acusou (`POST /tasks` com `15/01/2027` respondeu 201
em vez de 400). Lição que virou regra na skill: consolidar código morto com
código vivo pode afrouxar validação sem ninguém perceber.

---

## C) Resultados

### Resumo dos relatórios

| | Projeto 1 | Projeto 2 | Projeto 3 |
|---|---:|---:|---:|
| CRITICAL | 7 | 4 | 2 |
| HIGH | 5 | 7 | 6 |
| MEDIUM | 6 | 6 | 6 |
| LOW | 4 | 4 | 4 |
| **Total** | **22** | **21** | **18** |
| APIs deprecated | 0 | 3 | 5 |

### Antes / depois

| | Antes | Depois |
|---|---|---|
| **Projeto 1** | 4 arquivos, 780 linhas. Tudo em `models.py` + `controllers.py`. 19 queries concatenadas. Conexão global. | 24 módulos em `src/`. 100% parametrizado. Conexão por thread injetada. 2 endpoints perigosos removidos. |
| **Projeto 2** | 3 arquivos, 180 linhas. God Class de 141 linhas. 5 níveis de callback. Sem FK. | 22 módulos em `src/`. `async/await` com transação. FKs em cascata. Cartão mascarado. |
| **Projeto 3** | 11 arquivos, 1150 linhas. `routes/` de 733 linhas fazendo tudo. `services/` morto. | 26 módulos em `src/`. Controllers separados. Serviço de notificação ligado ao fluxo. Zero API deprecated. |

Detalhes de segurança:

| Correção | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| Segredos fora do código (`.env.example`) | ✓ | ✓ | ✓ |
| Senha com hash + salt | ✓ (pbkdf2) | ✓ (scrypt) | ✓ (pbkdf2) |
| Senha/hash fora da resposta HTTP | ✓ | — | ✓ |
| Queries parametrizadas | ✓ | já era | já era |
| Endpoint de SQL arbitrário removido | ✓ | — | — |
| Debug desligado por padrão | ✓ | — | ✓ |
| Dado sensível fora do log | ✓ | ✓ (cartão) | ✓ |

### Checklist de validação

**Fase 1 — Análise**

| Item | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| Linguagem detectada corretamente | ✓ | ✓ | ✓ |
| Framework detectado corretamente | ✓ | ✓ | ✓ |
| Domínio descrito corretamente | ✓ | ✓ | ✓ |
| Nº de arquivos condiz com a realidade | ✓ 4 | ✓ 3 | ✓ 11 |

**Fase 2 — Auditoria**

| Item | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| Relatório segue o template | ✓ | ✓ | ✓ |
| Cada finding com arquivo e linhas exatos | ✓ | ✓ | ✓ |
| Ordenados CRITICAL → LOW | ✓ | ✓ | ✓ |
| Mínimo de 5 findings | ✓ 22 | ✓ 21 | ✓ 18 |
| Detecção de APIs deprecated | ✓ (0) | ✓ (3) | ✓ (5) |
| Pausa pedindo confirmação antes da Fase 3 | ✓ | ✓ | ✓ |

**Fase 3 — Refatoração**

| Item | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| Estrutura de diretórios MVC | ✓ | ✓ | ✓ |
| Config extraída, sem hardcoded | ✓ | ✓ | ✓ |
| Models abstraindo os dados | ✓ | ✓ | ✓ |
| Views/Routes só roteando | ✓ | ✓ | ✓ |
| Controllers concentrando o fluxo | ✓ | ✓ | ✓ |
| Error handling centralizado | ✓ | ✓ | ✓ |
| Entry point claro | ✓ | ✓ | ✓ |
| Aplicação inicia sem erros | ✓ | ✓ | ✓ |
| Endpoints originais respondem | ✓ 31/31 | ✓ 9/9 | ✓ 50/50 |

**Critérios de aceite** — atingidos nos 3 projetos:

| Critério | P1 | P2 | P3 |
|---|:-:|:-:|:-:|
| Fase 1 detecta a stack | ✓ | ✓ | ✓ |
| Fase 2 encontra ≥ 5 findings | ✓ | ✓ | ✓ |
| Fase 2 tem ≥ 1 CRITICAL ou HIGH | ✓ | ✓ | ✓ |
| Fase 3 aplicação funciona | ✓ | ✓ | ✓ |

### Logs de validação

Cada projeto foi exercitado por um smoke test que chama todas as rotas **antes** e
**depois** da refatoração e compara status code e formato do corpo.

**Projeto 1 — `code-smells-project`**

```
casos=33  status_iguais=31  status_diferentes=2  shape_diferentes=13
```

Os 2 status divergentes são `POST /admin/query` e `POST /admin/reset-db`,
removidos de propósito (200 → 404). As 13 divergências de corpo são as correções
de segurança: `/health` sem `secret_key`/`db_path`/`debug`, `/usuarios` sem
`senha`, e `"sucesso": false` adicionado ao envelope de erro (aditivo).

```
$ curl -s http://127.0.0.1:5000/health
{"counts":{"pedidos":1,"produtos":10,"usuarios":4},"database":"connected","status":"ok","versao":"1.0.0"}

$ curl -s -X POST http://127.0.0.1:5000/login -d '{"email":"joao@email.com","senha":"123456"}'
{"dados":{"email":"joao@email.com","id":2,"nome":"João Silva","tipo":"cliente"},"mensagem":"Login OK","sucesso":true}
```

**Projeto 2 — `ecommerce-api-legacy`**

```
casos=9  status_iguais=9  status_diferentes=0  body_diferentes=3
```

Verificação extra do conteúdo do relatório financeiro (mesma sequência de
checkouts nos dois códigos, JSON normalizado e comparado com `diff`):

```
RELATORIO FINANCEIRO: IDENTICO ao original
```

As 3 divergências de corpo: mensagem do `DELETE` (a limpeza em cascata agora
acontece), relatório após delete (sem os órfãos `"Unknown"`) e 404 em texto em vez
de HTML.

**Projeto 3 — `task-manager-api`**

```
casos=50  status_iguais=50  status_diferentes=0  body_diferentes=5
```

4 das 5 divergências são a remoção do campo `password`; a quinta é o 404 em JSON.

```
$ curl -s http://127.0.0.1:5000/tasks/stats
{"cancelled":1,"completion_rate":10.0,"done":1,"in_progress":2,"overdue":2,"pending":6,"total":10}

$ curl -s -X POST http://127.0.0.1:5000/login -d '{"email":"joao@email.com","password":"1234"}'
{"message":"Login realizado com sucesso","token":"eyJ1c2VyX2lkIjoxfQ.aonNEg.6xfIg9_grYue55RLmnUhyF-pxZY",
 "user":{"active":true,"email":"joao@email.com","id":1,"name":"João Silva","role":"admin"}}
```

### Varredura final de anti-patterns

Nos 3 projetos, depois da refatoração:

```
segredos hardcoded ............ nenhum
SQL por concatenação .......... nenhum
estado global mutável ......... nenhum
SQL/ORM fora de models/ ....... nenhum
try/except em controllers ..... nenhum
print/console.log direto ...... nenhum
md5 / hash caseiro ............ nenhum
APIs deprecated ............... nenhuma
```

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://claude.com/claude-code) instalado e autenticado
- Python 3.11+ (projetos 1 e 3)
- Node.js 18+ (projeto 2)

### Rodando a skill

A skill já está em `.claude/skills/refactor-arch/` dentro dos 3 projetos. Como o
Claude Code carrega skills a partir do diretório atual, basta entrar na pasta do
projeto e invocar:

```bash
cd code-smells-project
claude "/refactor-arch"

cd ../ecommerce-api-legacy
claude "/refactor-arch"

cd ../task-manager-api
claude "/refactor-arch"
```

A execução para no fim da Fase 2 e pede confirmação:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
> y
```

Responder `n` encerra com o relatório entregue e **nenhum arquivo modificado**.

Para aplicar em outro projeto, copie a pasta inteira:

```bash
cp -r code-smells-project/.claude/skills/refactor-arch /caminho/do/projeto/.claude/skills/
```

### Validando o resultado

**Projeto 1 — Python/Flask**

```bash
cd code-smells-project
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # Linux/macOS: .venv/bin/pip
python app.py                 # http://127.0.0.1:5000
```

Em desenvolvimento não é preciso configurar nada: sem `SECRET_KEY` a aplicação
gera uma chave efêmera e avisa no log. Para sobrescrever qualquer valor, exporte
a variável antes de subir (a config é lida do ambiente — veja
[.env.example](code-smells-project/.env.example) para a lista completa):

```bash
export SECRET_KEY=... DATABASE_PATH=loja.db     # PowerShell: $env:SECRET_KEY="..."
```

```bash
curl http://127.0.0.1:5000/health
curl http://127.0.0.1:5000/produtos
curl -X POST http://127.0.0.1:5000/login \
     -H "Content-Type: application/json" \
     -d '{"email":"joao@email.com","senha":"123456"}'
curl -X POST http://127.0.0.1:5000/pedidos \
     -H "Content-Type: application/json" \
     -d '{"usuario_id":2,"itens":[{"produto_id":2,"quantidade":2}]}'
curl http://127.0.0.1:5000/relatorios/vendas
```

Sinais de que a refatoração funcionou: `/health` **não** devolve `secret_key`,
`/usuarios` **não** devolve `senha`, e `/admin/query` responde **404**.

**Projeto 2 — Node.js/Express**

```bash
cd ecommerce-api-legacy
npm install
npm start                     # http://127.0.0.1:3000
```

Em desenvolvimento roda sem configuração (banco em `:memory:`, seed automático).
As variáveis de [.env.example](ecommerce-api-legacy/.env.example) são lidas do
ambiente; para carregá-las de um arquivo, use o suporte nativo do Node 20.6+:

```bash
cp .env.example .env && node --env-file=.env src/app.js
```

```bash
curl -X POST http://127.0.0.1:3000/api/checkout \
     -H "Content-Type: application/json" \
     -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
curl http://127.0.0.1:3000/api/admin/financial-report
curl -X DELETE http://127.0.0.1:3000/api/users/1
curl http://127.0.0.1:3000/api/admin/financial-report   # sem alunos "Unknown"
```

O arquivo `api.http` continua valendo (VS Code REST Client / JetBrains).

Sinais de que funcionou: o log mostra o cartão mascarado
(`**** **** **** 4444`), e o relatório após o `DELETE` não tem mais registros
órfãos.

**Projeto 3 — Python/Flask + SQLAlchemy**

```bash
cd task-manager-api
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt
python seed.py                # popule antes do primeiro boot
python app.py                 # http://127.0.0.1:5000
```

Como no projeto 1, a config vem do ambiente e o modo de desenvolvimento não
exige nenhuma variável — veja [.env.example](task-manager-api/.env.example) para
os nomes (`SECRET_KEY`, `DATABASE_URI`, `SMTP_*`, `NOTIFICATIONS_ENABLED`).

```bash
curl http://127.0.0.1:5000/tasks
curl http://127.0.0.1:5000/tasks/stats
curl http://127.0.0.1:5000/reports/summary
curl -X POST http://127.0.0.1:5000/login \
     -H "Content-Type: application/json" \
     -d '{"email":"joao@email.com","password":"1234"}'
```

Sinais de que funcionou: nenhuma resposta contém o campo `password`, o `token` do
login é assinado (não `fake-jwt-token-1`), e uma rota inexistente devolve JSON.

### Estrutura do repositório

```
.
├── README.md                        # este arquivo
├── DESAFIO.md                       # enunciado original
├── reports/
│   ├── audit-project-1.md
│   ├── audit-project-2.md
│   └── audit-project-3.md
├── code-smells-project/             # Python/Flask — refatorado
│   ├── .claude/skills/refactor-arch/
│   ├── app.py
│   └── src/{config,infra,models,services,controllers,views,middlewares}/
├── ecommerce-api-legacy/            # Node/Express — refatorado
│   ├── .claude/skills/refactor-arch/
│   └── src/{config,infra,models,services,controllers,routes,middlewares}/
└── task-manager-api/                # Python/Flask+SQLAlchemy — refatorado
    ├── .claude/skills/refactor-arch/
    ├── app.py
    ├── seed.py
    └── src/{config,infra,models,services,controllers,views,middlewares,utils}/
```
