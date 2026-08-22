# Catálogo de Anti-Patterns

Referência da **Fase 2**. Cada entrada traz: sinais de detecção acionáveis,
severidade fixa e recomendação. Percorra o catálogo inteiro, de cima para baixo,
contra todos os arquivos-fonte.

## Escala de severidade

| Nível | Critério |
|---|---|
| **CRITICAL** | Falha grave de arquitetura ou segurança: expõe dados sensíveis, permite execução arbitrária, ou viola completamente a separação de responsabilidades (God Class com banco + regra + rota no mesmo arquivo). |
| **HIGH** | Violação forte de MVC/SOLID que inviabiliza manutenção e teste: regra de negócio presa no controller/rota, acoplamento sem injeção de dependência, estado global mutável. |
| **MEDIUM** | Padronização, duplicação ou performance moderada: N+1, ausência de validação, tratamento de erro repetido, middleware mal usado. |
| **LOW** | Legibilidade: nomenclatura ruim, magic numbers, `print` como log, imports mortos. |

Regra de desempate: se o problema **expõe segredo ou permite injeção**, é
CRITICAL, independentemente de quão pequeno pareça o trecho.

---

## CRITICAL

### AP-01 — Hardcoded Credentials / Secrets
**Sinais**
- Literais atribuídos a `SECRET_KEY`, `password`, `pass`, `pwd`, `token`, `api_key`, `apiKey`, `dbPass`.
- Strings com prefixo de chave de provedor: `pk_live_`, `sk_live_`, `AKIA`, `ghp_`.
- Credenciais SMTP/DB dentro de construtor ou objeto `config` no código-fonte.
- Segredo devolvido em resposta HTTP (health check que ecoa `secret_key`).

**Impacto**: segredo versionado no Git vaza para qualquer um com acesso ao repositório; rotação exige deploy.
**Recomendação**: mover para variáveis de ambiente com `.env.example` documentando as chaves; remover o valor do código e do histórico de resposta.

### AP-02 — SQL Injection (query por concatenação)
**Sinais**
- `execute("... " + var)`, f-string/template literal dentro de `execute`/`query`/`run`.
- `WHERE id = " + str(id)`, `LIKE '%" + termo + "%'`.
- Query montada por append em loop ou por `if` encadeado.
- Contraexemplo (não é finding): placeholders `?`, `%s`, `:nome` com lista de parâmetros.

**Impacto**: leitura, alteração ou destruição de dados por entrada do usuário; bypass de autenticação em query de login.
**Recomendação**: queries parametrizadas em 100% dos acessos; nenhum dado de request concatenado em SQL.

### AP-03 — Arbitrary Code / SQL Execution Endpoint
**Sinais**
- Rota que recebe SQL/comando do corpo e executa (`/admin/query`, `eval(`, `exec(`, `child_process.exec` com input).
- Rota destrutiva sem autenticação (`/admin/reset-db`, `DELETE FROM` em massa).

**Impacto**: RCE ou destruição total dos dados por qualquer chamador anônimo.
**Recomendação**: remover o endpoint. Se a operação for necessária, vira comando de CLI/migration fora da API.

### AP-04 — God Class / God Module
**Sinais**
- Um arquivo concentra ≥ 2 de: definição de rotas, acesso a banco, regra de negócio, formatação de resposta, configuração.
- Classe com nome genérico: `Manager`, `Helper`, `Utils`, `Service` cuidando de tudo.
- Arquivo-fonte muito acima da média do projeto e tocando múltiplos domínios.

**Impacto**: nada é testável em isolamento; qualquer mudança tem raio de alcance sobre todos os domínios.
**Recomendação**: quebrar por domínio e por camada (model / controller / rota).

### AP-05 — Senha em Texto Plano ou Hash Inseguro
**Sinais**
- `INSERT INTO users ... senha` recebendo o valor cru do request.
- Comparação direta `WHERE senha = '<valor>'`.
- `hashlib.md5`, `sha1`, `crypto.createHash('md5')` para senha.
- Hash caseiro (loop de `base64`, XOR, substring).
- Senha presente no `to_dict()`/serializer e devolvida pela API.

**Impacto**: vazamento do banco expõe as senhas reais dos usuários; MD5/SHA1 caem em ataque de dicionário.
**Recomendação**: hash lento com salt (`bcrypt`, `argon2`, `scrypt`, `pbkdf2`); nunca serializar o campo de senha.

---

## HIGH

### AP-06 — Business Logic no Controller / na Rota
**Sinais**
- Handler de rota com cálculo de total, regra de desconto, decisão de fluxo, montagem de relatório.
- Handler acima de ~40 linhas ou com mais de 3 níveis de indentação.
- Handler chamando o banco diretamente e formatando o resultado.
- Efeito colateral de negócio (envio de e-mail/SMS/push, gravação de auditoria) dentro do handler.

**Impacto**: a regra só é testável subindo o servidor HTTP; a mesma regra é reescrita em cada rota que precisa dela.
**Recomendação**: controller apenas orquestra (valida entrada → chama model/service → devolve resposta); a regra vai para model/service.

### AP-07 — Estado Global Mutável / Singleton Implícito
**Sinais**
- `global <var>` reatribuída em runtime; conexão de banco guardada em variável de módulo.
- `let cache = {}` / `let total = 0` exportados e mutados por outros módulos.
- Acumulador de valores em memória (lista de notificações, contador de receita).

**Impacto**: estado compartilhado entre requisições concorrentes → race condition e vazamento de dados entre usuários; perda de tudo a cada restart; testes contaminados entre si.
**Recomendação**: injetar a dependência via composition root; estado que precisa durar vai para o banco.

### AP-08 — Acoplamento Forte / Ausência de Injeção de Dependência
**Sinais**
- Módulo instancia sua própria dependência (`new Database(...)`, `SMTP(...)` dentro do construtor).
- Camada de dados importada diretamente pela rota.
- Import circular entre camadas ou `import` de módulo concreto onde caberia abstração.
- Credencial/host de infraestrutura fixa dentro da classe que a usa.

**Impacto**: impossível trocar a implementação em teste; um `import` traz meia aplicação junto.
**Recomendação**: receber dependências por parâmetro/construtor e montá-las no entrypoint.

### AP-09 — Callback Hell / Fluxo Assíncrono sem Controle
**Sinais**
- ≥ 3 níveis de callbacks aninhados de I/O.
- Contadores manuais de pendência (`pending--; if (pending === 0) res.json(...)`).
- Resposta enviada de dentro de callback aninhado sem `return` garantido → risco de double-send.
- Sequência de escritas relacionadas sem transação.

**Impacto**: erro de um nível é engolido pelos outros; ordem de resposta não determinística; escrita parcial deixa o banco inconsistente.
**Recomendação**: `async/await` com wrapper de Promise, agregação por `Promise.all`, e transação envolvendo escritas relacionadas.

### AP-10 — Ausência de Camada de Abstração de Dados
**Sinais**
- SQL/ORM chamado de dentro de rota, controller, util ou template.
- O mesmo `SELECT` repetido em arquivos diferentes.
- Serialização de entidade (`to_dict`, montagem de payload) espalhada por vários handlers.

**Impacto**: mudar uma coluna obriga a caçar todas as ocorrências pelo projeto.
**Recomendação**: um model/repository por entidade concentra acesso e serialização.

### AP-11 — Autorização Ausente em Rota Sensível
**Sinais**
- Rota `/admin/*`, relatório financeiro, `DELETE /users/:id` sem checagem de identidade/papel.
- Login que devolve token falso/previsível (`'fake-jwt-token-' + id`) ou nenhum token.
- Nenhum middleware de autenticação registrado na aplicação.

**Impacto**: qualquer chamador anônimo lê dados de faturamento ou apaga registros.
**Recomendação**: middleware de autenticação/autorização aplicado às rotas sensíveis; token assinado de verdade.

### AP-12 — Integridade Referencial Ignorada
**Sinais**
- `DELETE` do registro pai sem tratar filhos (matrículas, pagamentos, itens órfãos).
- FK declarada sem `ON DELETE` nem cascade no ORM.
- Comentário/mensagem admitindo o problema ("ficaram sujos no banco").
- Baixa de estoque / movimentação financeira fora de transação.

**Impacto**: dados órfãos corrompem relatórios e quebram joins.
**Recomendação**: cascade explícito ou remoção lógica, dentro de transação.

---

## MEDIUM

### AP-13 — Query N+1
**Sinais**
- `SELECT`/`.query`/`.get` dentro de `for`/`forEach`/`map`.
- Loop externo sobre a lista pai e consulta por item filho — às vezes em 2 níveis (N*M).
- ORM sem `join`/`eager loading` acessando relacionamento dentro do loop.

**Impacto**: latência cresce linearmente com o volume; a rota degrada em produção com dados reais.
**Recomendação**: uma query com `JOIN`/`IN`, ou eager loading; agregação (`COUNT`, `SUM`) no banco.

### AP-14 — Validação Ausente ou Espalhada
**Sinais**
- Campo do request usado sem checar presença/tipo (`data['x']` direto, `req.body.x` sem guarda).
- Regra de validação repetida em POST e PUT com pequenas diferenças.
- Lista de valores válidos escrita inline em cada handler.
- Conversão numérica sem tratamento (`int(param)` sobre query string).

**Impacto**: 500 em vez de 400; regra diverge entre rotas com o tempo.
**Recomendação**: schema/validador único por entidade, chamado por todos os handlers.

### AP-15 — Tratamento de Erro Duplicado / Silencioso
**Sinais**
- `try/except`/`try/catch` idêntico repetido em cada handler.
- `except:` sem tipo, `catch(e) {}` vazio, erro engolido sem log.
- Detalhe de exceção interna devolvido ao cliente (`str(e)` no corpo da resposta).
- Callback de erro ignorado (`(err) => { ... }` sem checar `err`).

**Impacto**: falha some ou vaza stack trace; resposta de erro inconsistente entre rotas.
**Recomendação**: middleware/handler de erro centralizado, com log estruturado e corpo de erro padronizado.

### AP-16 — Código Duplicado / DRY
**Sinais**
- Blocos quase idênticos em handlers diferentes (montagem de payload, cálculo de "overdue", checagem de existência).
- Mesma constante/lista literal repetida em vários arquivos.
- Método `to_dict` do model existindo em paralelo a uma montagem manual do mesmo dicionário na rota.

**Impacto**: correção aplicada em um lugar e esquecida nos outros.
**Recomendação**: extrair para o model ou para um helper único e usar em todos os pontos.

### AP-17 — Contrato de Resposta Inconsistente
**Sinais**
- Rotas do mesmo projeto devolvendo ora `{"dados": ...}`, ora array cru, ora texto puro (`res.send("...")`).
- Status code errado para o caso (200 em criação, 200 em erro de negócio).
- Mensagem de erro em idiomas ou formatos diferentes entre rotas.

**Impacto**: cliente precisa de um parser por rota.
**Recomendação**: um envelope de resposta e uma tabela de status codes para toda a API.

### AP-18 — Configuração de Ambiente Fixa no Código
**Sinais**
- `debug=True`, `DEBUG` ligado incondicionalmente.
- `host`, `port`, caminho de banco, URL de serviço externo como literal.
- CORS liberado para qualquer origem sem configuração.

**Impacto**: `debug=True` expõe console de execução remota; mudar de ambiente exige alterar código.
**Recomendação**: valores por variável de ambiente, com default seguro (debug desligado).

---

## LOW

### AP-19 — `print`/`console.log` como Logging
**Sinais**: `print(`, `console.log(` em caminho de execução de produção; log com concatenação de string; log de dado sensível (e-mail, número de cartão, chave de gateway).
**Impacto**: sem nível, sem timestamp, sem destino configurável; risco de logar dado sensível.
**Recomendação**: logger da linguagem com níveis; nunca logar credencial ou PAN.

### AP-20 — Magic Numbers e Magic Strings
**Sinais**: números soltos em regra (`> 10000`, `* 0.1`, `< 3`, `> 200`); listas de status literais repetidas; limites de validação inline.
**Impacto**: intenção ilegível e alteração propensa a erro.
**Recomendação**: constantes nomeadas em módulo de configuração/domínio.

### AP-21 — Nomenclatura Ruim
**Sinais**: variáveis de uma letra fora de loop (`u`, `e`, `p`, `cc`); campos de API abreviados (`usr`, `eml`, `pwd`, `c_id`); nomes genéricos (`data`, `result`, `temp`, `manager`); mistura de idiomas no mesmo escopo.
**Impacto**: leitura exige decodificar em vez de ler.
**Recomendação**: nomes completos e um idioma só por projeto.

### AP-22 — Imports Não Utilizados / Código Morto
**Sinais**: `import os, sys, json, time` sem uso; função nunca chamada; variável atribuída e não lida; `import` dentro de função sem motivo.
**Impacto**: ruído e falsa impressão de dependência.
**Recomendação**: remover.

### AP-23 — Condicional Redundante / Aninhamento Desnecessário
**Sinais**: `if cond: return True else: return False`; `if` aninhado que poderia ser expressão booleana única; `else` após `return`.
**Impacto**: verbosidade que esconde a regra.
**Recomendação**: retornar a expressão diretamente e usar early return.

---

## Checagem de APIs Deprecated

Seção obrigatória da Fase 2. Cruze com as versões detectadas na Fase 1.

### Python

| API | Situação | Substituir por |
|---|---|---|
| `datetime.utcnow()` | Deprecated no Python 3.12+ | `datetime.now(timezone.utc)` |
| `datetime.utcfromtimestamp()` | Deprecated no Python 3.12+ | `datetime.fromtimestamp(ts, timezone.utc)` |
| `Model.query` / `Query.get()` (SQLAlchemy) | Legacy desde SQLAlchemy 2.0 / Flask-SQLAlchemy 3.x | `db.session.get(Model, id)`, `db.session.execute(db.select(Model))` |
| `hashlib.md5`/`sha1` para senha | Inseguro (não deprecated, mas proibido para senha) | `bcrypt`, `argon2` |
| `imp`, `distutils` | Removidos no 3.12 | `importlib`, `setuptools`/`packaging` |
| `@app.before_first_request` (Flask) | Removido no Flask 2.3+ | inicialização no factory / `with app.app_context()` |
| `flask.Markup`, `flask.escape` | Removidos no Flask 2.4+ | `markupsafe` |
| `dict` com `type(x) == list` | Estilo obsoleto | `isinstance(x, list)` |
| `except:` sem tipo | Anti-pattern histórico | `except Exception as exc:` |

### Node.js / JavaScript

| API | Situação | Substituir por |
|---|---|---|
| `new Buffer(...)` | Deprecated desde Node 6 | `Buffer.from(...)` / `Buffer.alloc(...)` |
| `url.parse()` | Legacy | `new URL(...)` |
| `crypto.createHash('md5'/'sha1')` para senha | Inseguro | `bcrypt`, `argon2` |
| `body-parser` como dependência | Embutido desde Express 4.16 | `express.json()`, `express.urlencoded()` |
| `sqlite3.verbose()` em produção | Modo de debug | driver sem `verbose`, ou `node:sqlite` / `better-sqlite3` |
| `util.isArray`, `util._extend` | Deprecated | `Array.isArray`, spread |
| `domain`, `punycode` | Deprecated | remover |
| Callbacks de I/O sem Promise | Estilo legado | `fs/promises`, `util.promisify`, `async/await` |
| `var` | Estilo pré-ES6 | `const` / `let` |

### Como reportar

Um finding por API deprecated encontrada, com arquivo e linha. Severidade padrão
**MEDIUM**; sobe para **CRITICAL** quando a API deprecated é o hash de senha.

---

## Cobertura mínima da auditoria

Antes de imprimir o relatório, confirme:

- [ ] ≥ 5 findings
- [ ] ≥ 1 CRITICAL ou HIGH
- [ ] todo finding com arquivo **e** linha(s) reais
- [ ] checagem de deprecated executada
- [ ] findings ordenados CRITICAL → HIGH → MEDIUM → LOW
