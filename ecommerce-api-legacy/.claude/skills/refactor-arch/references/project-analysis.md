# Project Analysis — Heurísticas de Detecção

Referência da **Fase 1**. Objetivo: descobrir stack, domínio e arquitetura atual
sem depender de conhecimento prévio sobre o projeto.

## 1. Detecção de linguagem e framework

A ordem é sempre a mesma: **manifesto primeiro, imports depois**. O manifesto dá
a versão; os imports confirmam o que é realmente usado.

### 1.1 Manifestos → linguagem

| Arquivo encontrado | Linguagem |
|---|---|
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python |
| `package.json` | JavaScript / TypeScript |
| `tsconfig.json` presente junto de `package.json` | TypeScript |
| `pom.xml`, `build.gradle` | Java / Kotlin |
| `go.mod` | Go |
| `composer.json` | PHP |
| `Gemfile` | Ruby |
| `*.csproj`, `*.sln` | C# / .NET |
| `Cargo.toml` | Rust |

Se não houver manifesto, caia para a extensão dominante dos arquivos-fonte.

### 1.2 Dependências → framework e versão

Leia o manifesto e extraia a versão declarada. Exemplos:

- `flask==3.1.1` → Flask 3.1.1
- `"express": "^4.18.2"` → Express 4.x
- `flask-sqlalchemy`, `sqlalchemy` → ORM SQLAlchemy
- `sqlite3`, `psycopg2`, `mysql2`, `pg`, `mongoose` → driver de banco
- `django`, `fastapi`, `nestjs`, `spring-boot-starter-web`, `gin-gonic`, `laravel/framework` → framework web

Confirme com os imports do código: um pacote declarado e nunca importado não
conta; um import sem declaração é dependência implícita — registre como finding.

### 1.3 Sinais de framework no código

| Sinal no código | Framework |
|---|---|
| `Flask(__name__)`, `@app.route`, `Blueprint` | Flask |
| `FastAPI()`, `@app.get` | FastAPI |
| `express()`, `app.use(`, `app.get('/...` | Express |
| `@Controller`, `@RestController` | Spring / NestJS |
| `urls.py`, `INSTALLED_APPS` | Django |
| `http.HandleFunc`, `gin.Default()` | net/http, Gin |

## 2. Inventário de arquivos

Liste os fontes ignorando: `node_modules/`, `.venv/`, `venv/`, `__pycache__/`,
`dist/`, `build/`, `.git/`, `vendor/`, `target/`, arquivos minificados e lockfiles.

Registre para cada arquivo: caminho, nº de linhas, papel aparente (entrypoint,
rotas, dados, util, config, teste).

Sinais de entrypoint: `if __name__ == "__main__"`, `app.listen(`, `main()`,
campo `main`/`scripts.start` do `package.json`, `app.run(`.

## 3. Mapeamento de rotas

Extraia **todas** as rotas — elas são o contrato que a Fase 3 precisa preservar.

| Framework | Padrão a procurar |
|---|---|
| Flask | `@app.route(...)`, `@bp.route(...)`, `app.add_url_rule(...)` |
| Express | `app.get/post/put/delete/patch(`, `router.<verbo>(` |
| FastAPI | `@app.get/post/...`, `@router.<verbo>` |
| Spring | `@GetMapping`, `@RequestMapping` |

Para cada rota registre: método HTTP, path, handler, status codes retornados e
formato do corpo da resposta. Atenção às rotas registradas fora de decorator
(`add_url_rule`) e às definidas dentro de métodos/classes — elas escapam de uma
busca por decorators.

## 4. Camada de dados

Procure, nesta ordem:

1. **DDL** — `CREATE TABLE`, migrations, `db.Model`, `@Entity`, schemas de ORM.
   Daí saem os nomes das tabelas.
2. **Acesso** — SQL cru (`cursor.execute`, `db.run`, `db.query`) ou ORM
   (`Model.query`, `findAll`, `repository.save`).
3. **Conexão** — onde é aberta, se é global/singleton, se há pool.

Registre o modo de acesso: `raw SQL`, `ORM` ou `misto` (misto quase sempre vira
finding de inconsistência).

## 5. Configuração e segredos

Varra por: `SECRET_KEY`, `password`, `passwd`, `pwd`, `token`, `api_key`,
`apiKey`, `secret`, `DATABASE_URL`, strings `pk_live_`/`sk_live_`, `Bearer `,
credenciais SMTP, hosts e portas fixos.

Classifique cada um: vem de variável de ambiente (ok) ou está hardcoded (finding
CRITICAL).

## 6. Domínio de negócio

Deduza pelas entidades, rotas e nomes de tabela — não pelo nome do repositório,
que costuma mentir em projeto legado.

- tabelas `produtos`, `pedidos`, `itens_pedido` → e-commerce
- tabelas `courses`, `enrollments`, `payments` → plataforma de cursos / LMS
- tabelas `tasks`, `categories`, `users` → gestor de tarefas

Descreva em uma linha: `<tipo de aplicação> (<entidades principais>)`.

## 7. Classificação da arquitetura atual

| Nível | Sinais | Como descrever |
|---|---|---|
| Monolítica | tudo em 1–4 arquivos, rotas + SQL + regra juntos | "Monolítica — sem separação de camadas" |
| God Class | uma classe/módulo concentra rotas, banco e negócio | "Monolítica — God Class em `<arquivo>`" |
| Camadas parciais | existem pastas (`models/`, `routes/`) mas a regra vazou para as rotas | "Camadas parciais — sem controllers, regra nas rotas" |
| MVC | models, controllers e rotas separados, config isolada | "MVC — verificar aderência fina" |

Nunca conclua "já está MVC" só porque existem as pastas: abra os arquivos e
confira **onde a regra de negócio realmente está**. Pasta com nome certo e
conteúdo errado é o caso mais comum em projeto parcialmente organizado.

## 8. Saída da fase

Preencha o bloco `PHASE 1: PROJECT ANALYSIS` do `SKILL.md` e guarde para as
fases seguintes: lista de arquivos, lista de rotas (contrato), tabelas e pontos
de configuração.
