```
================================
ARCHITECTURE AUDIT REPORT
================================
```
**Project:** `code-smells-project`
**Stack:** Python 3.13 + Flask 3.1.1 (flask-cors 5.0.1)
**Files:** 4 analyzed | ~780 lines of code
**Date:** 2026-08-22

---

## Phase 1 — Project Analysis

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      Python 3.13
Framework:     Flask 3.1.1
Dependencies:  flask-cors 5.0.1, sqlite3 (stdlib)
Domain:        E-commerce API (produtos, usuários, pedidos, relatório de vendas)
Architecture:  Monolítica — 4 arquivos, sem separação de camadas; models.py
               acumula SQL, regra de negócio e serialização dos 4 domínios
Source files:  4 files analyzed (app.py 88, controllers.py 292, models.py 314,
               database.py 86)
DB tables:     produtos, usuarios, pedidos, itens_pedido
================================
```

---

## Summary

| CRITICAL | HIGH | MEDIUM | LOW | **Total** |
|---:|---:|---:|---:|---:|
| 7 | 5 | 6 | 4 | **22** |

---

## Findings

### [CRITICAL] Hardcoded Credentials
- **Anti-pattern:** AP-01
- **File:** `app.py:7`
- **Description:** `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` — a chave de assinatura de sessão está literal no código e versionada no Git.
- **Impact:** qualquer pessoa com acesso ao repositório consegue forjar sessões; rotacionar a chave exige alterar código e redeploy.
- **Recommendation:** ler de `SECRET_KEY` no ambiente, falhar no boot se ausente em produção, publicar `.env.example`.

### [CRITICAL] Segredos Expostos na Resposta HTTP
- **Anti-pattern:** AP-01
- **File:** `controllers.py:285-289`
- **Description:** o `/health` devolve no corpo da resposta a `secret_key` com o valor literal, além de `db_path`, `debug` e `ambiente`.
- **Impact:** endpoint público e sem autenticação entrega a chave secreta e o mapa de infraestrutura a qualquer chamador.
- **Recommendation:** health check devolve apenas status, versão e contadores; nenhum dado de configuração.

### [CRITICAL] SQL Injection (queries por concatenação)
- **Anti-pattern:** AP-02
- **File:** `models.py:28, 47-50, 57-61, 68, 92, 109-111, 126-129, 140, 148-151, 155-160, 163-166, 174, 188, 192, 220, 224, 279-281, 289-299`
- **Description:** **todas** as 19 queries do projeto são montadas com concatenação de string. Casos mais graves: `login_usuario` (`models.py:109-111`) concatena e-mail e senha direto na cláusula WHERE, e `buscar_produtos` (`models.py:289-299`) concatena o termo de busca dentro de um LIKE.
- **Impact:** bypass total de autenticação com uma tautologia no campo de e-mail do login; leitura, alteração e destruição de qualquer tabela a partir de parâmetros de request.
- **Recommendation:** placeholders com tupla de parâmetros em 100% dos acessos; filtro dinâmico monta cláusula e lista de params em paralelo.

### [CRITICAL] Endpoint de Execução de SQL Arbitrário
- **Anti-pattern:** AP-03
- **File:** `app.py:59-78`
- **Description:** `POST /admin/query` recebe o campo `sql` do corpo e executa direto no banco, com commit para comandos de escrita. Sem autenticação.
- **Impact:** qualquer chamador anônimo lê a tabela de usuários inteira, altera preços ou dropa tabelas.
- **Recommendation:** remover o endpoint; operação de manutenção vira script de CLI fora da API.

### [CRITICAL] Endpoint Destrutivo sem Autenticação
- **Anti-pattern:** AP-03
- **File:** `app.py:47-57`
- **Description:** `POST /admin/reset-db` apaga `itens_pedido`, `pedidos`, `produtos` e `usuarios` sem qualquer verificação de identidade.
- **Impact:** perda total dos dados por uma requisição anônima.
- **Recommendation:** remover da API; reset vira script protegido por variável de ambiente.

### [CRITICAL] God Module
- **Anti-pattern:** AP-04
- **File:** `models.py:1-314`
- **Description:** um único arquivo concentra acesso a dados, regra de negócio (cálculo de total do pedido em `133-169`, faixas de desconto em `256-262`), validação de estoque e serialização, para os 4 domínios (produtos, usuários, pedidos, relatórios).
- **Impact:** nada é testável em isolamento; mudança em qualquer domínio tem raio de alcance sobre todos os outros.
- **Recommendation:** quebrar em um model por entidade e mover a regra de negócio para services.

### [CRITICAL] Senhas em Texto Plano
- **Anti-pattern:** AP-05
- **File:** `database.py:75-83`, `models.py:105-120`, `models.py:122-131`, `models.py:79-86`, `models.py:95-102`
- **Description:** o seed grava as senhas de exemplo como texto plano (`database.py:75-83`); `criar_usuario` insere a senha crua (`models.py:126-129`); `login_usuario` compara a senha dentro do WHERE (`models.py:109-111`); e a serialização de usuário inclui o campo `senha`, devolvido por `GET /usuarios` e `GET /usuarios/<id>`.
- **Impact:** o vazamento do banco — ou uma simples chamada a `GET /usuarios` — expõe as senhas reais de todos os usuários.
- **Recommendation:** hash com salt (`werkzeug.security`), comparação via `check_password_hash`, e o campo `senha` fora de qualquer serializer.

### [HIGH] Regra de Negócio e Efeito Colateral no Controller
- **Anti-pattern:** AP-06
- **File:** `controllers.py:208-210`, `controllers.py:247-250`
- **Description:** o disparo de e-mail, SMS e push do pedido está como `print` dentro de `criar_pedido`; a decisão de notificar por mudança de status está como `if` dentro de `atualizar_status_pedido`.
- **Impact:** a regra de notificação só é testável subindo o servidor HTTP; qualquer outro caminho que crie pedido não notifica.
- **Recommendation:** extrair um `NotificacaoService` injetado no service de pedido.

### [HIGH] Conexão Global Mutável
- **Anti-pattern:** AP-07
- **File:** `database.py:4-10`
- **Description:** `db_connection = None` no escopo de módulo é reatribuída dentro de `get_db()` via `global`, com `check_same_thread=False`, e compartilhada por todas as requisições.
- **Impact:** com o servidor multi-thread, cursores e transações de requisições concorrentes se misturam na mesma conexão; a flag `check_same_thread=False` apenas desliga o alerta do driver.
- **Recommendation:** conexão por thread, instanciada no composition root e injetada nos models.

### [HIGH] Acoplamento Forte / Ausência de Injeção de Dependência
- **Anti-pattern:** AP-08
- **File:** `controllers.py:2-3`, `models.py:1`, `database.py:7`
- **Description:** `controllers` importa `models` e `database` como módulos concretos; `models` chama `get_db()` global em cada função. Não existe ponto de composição.
- **Impact:** impossível trocar o banco por um dublê em teste; importar o controller traz metade da aplicação junto.
- **Recommendation:** classes recebendo dependências por construtor, montadas em um único `create_app()`.

### [HIGH] SQL Dentro do Controller
- **Anti-pattern:** AP-10
- **File:** `controllers.py:264-274`
- **Description:** `health_check` abre cursor e roda quatro SELECT direto na camada de controller, ignorando os models.
- **Impact:** mudança de schema quebra o controller; o acesso a dados deixa de ter um lugar único.
- **Recommendation:** contadores expostos como método dos models.

### [HIGH] Ausência de Autorização em Rotas Sensíveis
- **Anti-pattern:** AP-11
- **File:** `app.py:47`, `app.py:59`, `controllers.py:128-134`, `controllers.py:167-186`
- **Description:** as rotas `/admin/*` não verificam identidade; `GET /usuarios` lista todos os usuários (com senha) sem autenticação; o `login` não emite token nenhum, então não há como proteger rota alguma depois.
- **Impact:** toda a API é efetivamente pública, inclusive as operações administrativas.
- **Recommendation:** middleware de autenticação e emissão de token assinado.

### [MEDIUM] Query N+1
- **Anti-pattern:** AP-13
- **File:** `models.py:139-146`, `models.py:154-166`, `models.py:171-201`, `models.py:203-233`
- **Description:** `get_pedidos_usuario` e `get_todos_pedidos` fazem 3 níveis de consulta aninhada (pedidos → itens de cada pedido → nome do produto de cada item); `criar_pedido` consulta o mesmo produto duas vezes, uma vez por item.
- **Impact:** listar 50 pedidos com 4 itens cada dispara cerca de 250 queries; a rota degrada linearmente com o volume.
- **Recommendation:** duas queries com IN + LEFT JOIN e agrupamento em memória; agregações via SUM/COUNT no banco.

### [MEDIUM] Validação Duplicada e Divergente
- **Anti-pattern:** AP-14
- **File:** `controllers.py:28-54`, `controllers.py:72-90`
- **Description:** a validação de produto é repetida quase idêntica em `criar_produto` e `atualizar_produto`, mas o PUT **não** valida tamanho do nome nem categoria — as duas rotas divergiram.
- **Impact:** é possível gravar por PUT um produto que o POST rejeitaria.
- **Recommendation:** uma função de validação por entidade, usada pelas duas rotas.

### [MEDIUM] Tratamento de Erro Duplicado com Vazamento de Detalhe Interno
- **Anti-pattern:** AP-15
- **File:** `controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292`
- **Description:** os 17 handlers repetem o mesmo `try/except Exception as e` e devolvem `str(e)` no corpo da resposta.
- **Impact:** mensagens internas do SQLite (nomes de tabela e coluna) chegam ao cliente; o padrão de erro é reescrito a cada handler.
- **Recommendation:** error handler centralizado, com log do stack trace e corpo de erro genérico.

### [MEDIUM] Serialização Duplicada
- **Anti-pattern:** AP-16
- **File:** `models.py:12-21`, `models.py:31-40`, `models.py:304-313`, `models.py:79-86`, `models.py:95-102`
- **Description:** o dicionário de produto é montado campo a campo em 3 lugares e o de usuário em 2, sempre idênticos.
- **Impact:** adicionar uma coluna exige lembrar de 5 pontos; foi exatamente assim que o campo `senha` acabou exposto em duas rotas.
- **Recommendation:** uma função de serialização por entidade dentro do model.

### [MEDIUM] Contrato de Resposta Inconsistente
- **Anti-pattern:** AP-17
- **File:** `controllers.py:29`, `controllers.py:206`, `app.py:32-45`, `controllers.py:276-290`
- **Description:** erros de validação devolvem só a chave `erro`, erros de negócio devolvem `erro` + `sucesso`, e `/` e `/health` devolvem objetos sem o envelope `dados`/`sucesso`.
- **Impact:** o cliente precisa de um parser por rota.
- **Recommendation:** um envelope único de erro para toda a API.

### [MEDIUM] Configuração de Ambiente Fixa no Código
- **Anti-pattern:** AP-18
- **File:** `app.py:8`, `app.py:9`, `app.py:88`
- **Description:** `DEBUG = True` no config e `debug=True` no `app.run`; `CORS(app)` libera qualquer origem; host `0.0.0.0`, porta `5000` e caminho `loja.db` fixos no código.
- **Impact:** o modo debug do Werkzeug expõe um console de execução de Python remoto; trocar de ambiente exige alterar código.
- **Recommendation:** todos os valores por variável de ambiente, com debug desligado por padrão.

### [LOW] `print` como Logging
- **Anti-pattern:** AP-19
- **File:** `controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250`, `app.py:56, 83-86`
- **Description:** 17 chamadas a `print` com concatenação de string; `controllers.py:161` e `179` logam o e-mail do usuário em operações de cadastro e login.
- **Impact:** sem nível, sem timestamp e sem destino configurável; dado pessoal vai para stdout.
- **Recommendation:** módulo `logging` com níveis e formatação parametrizada.

### [LOW] Magic Numbers e Magic Strings
- **Anti-pattern:** AP-20
- **File:** `models.py:256-262`, `controllers.py:47-52`, `controllers.py:242`
- **Description:** faixas de desconto (10000/0.1, 5000/0.05, 1000/0.02) soltas dentro da função de relatório; limites 2 e 200 do nome do produto e a lista de categorias válidas escritos inline no handler; lista de status válidos repetida literalmente.
- **Impact:** a regra comercial fica ilegível e espalhada.
- **Recommendation:** constantes nomeadas em módulo de configuração de domínio.

### [LOW] Imports Não Utilizados
- **Anti-pattern:** AP-22
- **File:** `models.py:2`, `database.py:2`
- **Description:** `import sqlite3` em `models.py` e `import os` em `database.py` nunca são usados.
- **Impact:** ruído e falsa impressão de dependência.
- **Recommendation:** remover.

### [LOW] Nomenclatura — Shadowing de Builtin
- **Anti-pattern:** AP-21
- **File:** `controllers.py:14, 64, 98`, `models.py:24, 54, 65, 89`
- **Description:** o parâmetro `id` sobrescreve o builtin do Python em 7 funções; em `controllers.py:56` a variável local `id` também sombreia o builtin.
- **Impact:** o builtin fica indisponível no escopo e o nome não diz de qual entidade é o id.
- **Recommendation:** `produto_id`, `usuario_id`, `pedido_id`.

---

## Deprecated APIs

Nenhuma API deprecated detectada. Verificações executadas contra Python 3.13 e
Flask 3.1.1: `datetime.utcnow()`, `flask.Markup`/`flask.escape`,
`@app.before_first_request`, `imp`/`distutils` e adaptadores de data do `sqlite3` —
nenhum presente no código.

---

## Preserved Contract

Rotas mapeadas na Fase 1 que devem continuar respondendo igual após a Fase 3:

| Método | Path | Status codes |
|---|---|---|
| GET | `/` | 200 |
| GET | `/health` | 200 |
| GET | `/produtos` | 200 |
| GET | `/produtos/busca` | 200 |
| GET | `/produtos/<int:id>` | 200, 404 |
| POST | `/produtos` | 201, 400 |
| PUT | `/produtos/<int:id>` | 200, 400, 404 |
| DELETE | `/produtos/<int:id>` | 200, 404 |
| GET | `/usuarios` | 200 |
| GET | `/usuarios/<int:id>` | 200, 404 |
| POST | `/usuarios` | 201, 400 |
| POST | `/login` | 200, 400, 401 |
| POST | `/pedidos` | 201, 400 |
| GET | `/pedidos` | 200 |
| GET | `/pedidos/usuario/<int:usuario_id>` | 200 |
| PUT | `/pedidos/<int:pedido_id>/status` | 200, 400 |
| GET | `/relatorios/vendas` | 200 |
| ~~POST~~ | ~~`/admin/reset-db`~~ | removida na Fase 3 (AP-03) |
| ~~POST~~ | ~~`/admin/query`~~ | removida na Fase 3 (AP-03) |

```
================================
Total: 22 findings
================================
```

---

## Refactoring Result

### Estrutura final

```
code-smells-project/
├── app.py                          # entry point (mantém `python app.py`)
├── .env.example
├── requirements.txt
└── src/
    ├── app.py                      # composition root: create_app()
    ├── config/
    │   ├── settings.py             # tudo de os.environ, zero literais
    │   └── constants.py            # categorias, status, faixas de desconto
    ├── infra/
    │   ├── database.py             # conexão por thread + transações
    │   └── schema.py               # DDL + carga inicial (senhas com hash)
    ├── models/
    │   ├── produto_model.py
    │   ├── usuario_model.py        # hash de senha, serializer sem senha
    │   └── pedido_model.py         # itens via JOIN, agregados no banco
    ├── services/
    │   ├── pedido_service.py       # cálculo de total + validação de estoque
    │   ├── relatorio_service.py    # regra de desconto
    │   └── notificacao_service.py
    ├── controllers/
    │   ├── produto_controller.py
    │   ├── usuario_controller.py
    │   ├── pedido_controller.py
    │   ├── relatorio_controller.py
    │   └── system_controller.py
    ├── views/
    │   ├── produto_routes.py
    │   ├── usuario_routes.py
    │   ├── pedido_routes.py
    │   ├── relatorio_routes.py
    │   └── system_routes.py
    └── middlewares/
        ├── error_handler.py        # handler centralizado
        ├── errors.py               # exceções de domínio
        └── validators.py           # validação por entidade
```

Arquivos legados `controllers.py`, `models.py` e `database.py` foram removidos.

### Findings resolvidos

| ID | Anti-pattern | Sev. | Como foi resolvido |
|---|---|---|---|
| AP-01 | Hardcoded credentials | CRITICAL | `src/config/settings.py` lê tudo de `os.environ`; sem `SECRET_KEY` gera chave efêmera em dev e **falha no boot** em produção; `.env.example` publicado |
| AP-01 | Segredos no `/health` | CRITICAL | `system_controller.health()` devolve apenas `status`, `database`, `counts` e `versao` |
| AP-02 | SQL Injection | CRITICAL | 100% das queries parametrizadas; o filtro dinâmico de busca monta cláusula e lista de params em paralelo |
| AP-03 | `/admin/query` | CRITICAL | rota removida |
| AP-03 | `/admin/reset-db` | CRITICAL | rota removida |
| AP-04 | God Module | CRITICAL | `models.py` (314 linhas) → 3 models + 3 services + 5 controllers + 5 arquivos de rota |
| AP-05 | Senhas em texto plano | CRITICAL | `werkzeug.security` no `UsuarioModel`; seed grava hash; `CAMPOS_PUBLICOS` exclui `senha` |
| AP-06 | Regra no controller | HIGH | `PedidoService` + `NotificacaoService`; controllers com no máximo 8 linhas por handler |
| AP-07 | Conexão global mutável | HIGH | `Database` com `threading.local()`, instanciado no composition root |
| AP-08 | Sem injeção de dependência | HIGH | models/services/controllers recebem dependências por construtor; `create_app()` é o único lugar que instancia infra |
| AP-10 | SQL no controller | HIGH | contadores viraram `contar()` nos models |
| AP-11 | Autorização ausente | HIGH | rotas administrativas eliminadas **e** RF-15: `AuthService` (`itsdangerous`, token com validade), `/login` passa a emitir `token` (campo aditivo), `require_auth` em `/usuarios`, `/usuarios/<id>` e `/relatorios/vendas`; imposição sob `AUTH_ENFORCED` (padrão `false`) |
| AP-13 | N+1 | MEDIUM | listagem de pedidos em 2 queries (IN + LEFT JOIN); relatório em 1 query agregada |
| AP-14 | Validação duplicada | MEDIUM | `middlewares/validators.py`, uma função por entidade, usada por POST e PUT |
| AP-15 | Erro duplicado | MEDIUM | `middlewares/error_handler.py`; nenhum `try/except` nos controllers; detalhe da exceção só no log |
| AP-16 | Serialização duplicada | MEDIUM | `serializar()` única por model |
| AP-17 | Contrato inconsistente | MEDIUM | envelope de erro único com `erro` + `sucesso: false` (aditivo — nenhum campo removido) |
| AP-18 | Config fixa | MEDIUM | `FLASK_DEBUG`, `HOST`, `PORT`, `DATABASE_PATH`, `CORS_ORIGINS` por env; debug **off** por padrão |
| AP-19 | `print` como log | LOW | `logging` com níveis; nenhum e-mail ou credencial logado |
| AP-20 | Magic numbers | LOW | `src/config/constants.py` (`FAIXAS_DESCONTO`, `CATEGORIAS_VALIDAS`, limites de nome) |
| AP-21 | Shadowing de builtin | LOW | parâmetros renomeados nas camadas novas (`produto_id`, `usuario_id`, `pedido_id`) |
| AP-22 | Imports mortos | LOW | removidos junto com os arquivos legados |

### Findings não resolvidos

Nenhum.

> **Correção de revisão (AP-11).** Este finding constava como parcial, com a
> justificativa de que autenticação obrigatória mudaria o contrato. A conclusão
> estava errada: faltava padrão no playbook, não viabilidade. O RF-15 separa
> **mecanismo** de **imposição** — o `/login` passou a emitir token assinado
> (campo `token`, aditivo: `dados`, `sucesso` e `mensagem` seguem iguais) e as
> rotas sensíveis ganharam `require_auth`. Com `AUTH_ENFORCED=false` (padrão) o
> contrato é idêntico ao original e o acesso anônimo vira `WARN` no log; com
> `AUTH_ENFORCED=true` as três rotas exigem `Bearer` token.

### Mudanças intencionais de contrato

As 3 abaixo são correções de segurança, registradas explicitamente:

1. `POST /admin/query` e `POST /admin/reset-db` → **404** (rotas removidas).
2. `GET /health` não devolve mais `secret_key`, `db_path`, `debug` e `ambiente`.
3. `GET /usuarios` e `GET /usuarios/<id>` não devolvem mais o campo `senha`.

Além delas, o corpo de erro passou a incluir `sucesso: false` onde antes só
havia `erro` — mudança **aditiva**, nenhum campo foi removido. Pelo mesmo
critério, o `POST /login` passou a incluir `token` (RF-15): os campos `dados`,
`sucesso` e `mensagem` seguem idênticos para quem já consome a rota.

### Validação

Suíte de 33 chamadas HTTP (caminho feliz + erros de validação + 404 + regra de
negócio), executada contra o código original e contra o refatorado:

```
casos=33  status_iguais=31  status_diferentes=2  shape_diferentes=13
```

Autorização (RF-15) testada nos dois modos:

```
AUTH_ENFORCED=false (padrão)
 200 GET /usuarios | /usuarios/1 | /relatorios/vendas    contrato preservado (+ WARN no log)

AUTH_ENFORCED=true
 401 GET /usuarios | /usuarios/1 | /relatorios/vendas    Credencial ausente
 200 mesmas 3 rotas com Bearer token do /login
 401 GET /usuarios com assinatura adulterada             "Token inválido"
 200 /, /health, /produtos, /produtos/1, /pedidos        rotas abertas seguem abertas
```

- **Boot:** aplicação sobe sem erro (`python app.py`), 17 rotas registradas
- **Endpoints:** 31/31 status codes idênticos ao original; os 2 divergentes são
  os `/admin/*` removidos de propósito
- **Formato:** 13 divergências de corpo, **todas** correspondendo às 3 mudanças
  intencionais mais o `sucesso: false` aditivo — nenhuma regressão
- **Varredura final:** zero anti-patterns CRITICAL ou HIGH remanescentes
  (sem segredo literal, sem SQL concatenado, sem estado global, sem SQL fora de
  `models/`, sem `try/except` em controller)
