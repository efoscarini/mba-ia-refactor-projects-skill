# Playbook de Refatoração

Referência da **Fase 3**. Uma transformação por anti-pattern do catálogo, com
antes/depois. Os exemplos alternam Python e JavaScript de propósito: o padrão é
o mesmo, muda a sintaxe.

Aplique na ordem do `SKILL.md` (config → models → services → controllers →
routes → middlewares → app). Cada etapa deve deixar a aplicação executável.

---

## RF-01 — Extrair configuração e segredos (resolve AP-01, AP-18)

**Antes**
```python
app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"
app.config["DEBUG"] = True
db_path = "loja.db"
```

**Depois** — `src/config/settings.py`
```python
import os

class Settings:
    SECRET_KEY = os.environ.get("SECRET_KEY", "")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    DATABASE_PATH = os.environ.get("DATABASE_PATH", "loja.db")
    PORT = int(os.environ.get("PORT", "5000"))

    @classmethod
    def validate(cls):
        if not cls.SECRET_KEY:
            raise RuntimeError("SECRET_KEY não definida. Veja .env.example")

settings = Settings()
```

E `.env.example` (versionado, sem valores reais):
```
SECRET_KEY=troque-por-um-valor-aleatorio
FLASK_DEBUG=false
DATABASE_PATH=loja.db
```

Regras: default seguro (debug **desligado**), falha no boot se faltar segredo,
nenhum valor real versionado. Em Node é o mesmo com `process.env`.

---

## RF-02 — Parametrizar queries (resolve AP-02)

**Antes**
```python
cursor.execute("SELECT * FROM produtos WHERE id = " + str(id))
cursor.execute(
    "SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"
)
```

**Depois**
```python
cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))
cursor.execute("SELECT * FROM usuarios WHERE email = ?", (email,))
```

Filtro dinâmico também é parametrizável — monte a cláusula e a lista de
parâmetros em paralelo:

```python
def buscar(termo=None, categoria=None, preco_min=None):
    clausulas, params = ["1=1"], []
    if termo:
        clausulas.append("(nome LIKE ? OR descricao LIKE ?)")
        params += [f"%{termo}%", f"%{termo}%"]
    if categoria:
        clausulas.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clausulas.append("preco >= ?")
        params.append(preco_min)
    cursor.execute(f"SELECT * FROM produtos WHERE {' AND '.join(clausulas)}", params)
```

O `f-string` aqui interpola apenas fragmentos SQL construídos pelo próprio
código; **nenhum dado de request entra na string**.

---

## RF-03 — Remover endpoint de execução arbitrária (resolve AP-03)

**Antes**
```python
@app.route("/admin/query", methods=["POST"])
def executar_query():
    cursor.execute(request.get_json().get("sql", ""))
```

**Depois**: rota deletada. Se a operação for legítima, vira script de manutenção
fora da API:

```python
# scripts/reset_db.py — executado manualmente, nunca exposto por HTTP
if __name__ == "__main__":
    if os.environ.get("ALLOW_DB_RESET") != "true":
        raise SystemExit("Reset bloqueado. Defina ALLOW_DB_RESET=true.")
    reset()
```

Registre a remoção no relatório: é a única quebra de contrato permitida.

---

## RF-04 — Quebrar a God Class por camada e domínio (resolve AP-04, AP-10)

**Antes** — `AppManager.js`: banco, rotas, checkout, relatório, tudo junto.

**Depois**
```
src/
├── models/course.model.js       # SELECT/INSERT de courses
├── models/user.model.js
├── models/enrollment.model.js
├── models/payment.model.js
├── services/checkout.service.js # orquestra o caso de uso
├── controllers/checkout.controller.js
└── routes/checkout.routes.js
```

Roteiro: (1) mapear as responsabilidades do arquivo; (2) extrair primeiro o
acesso a dados, entidade por entidade; (3) extrair a regra para service; (4) o
que sobra é controller; (5) rotas passam a apontar para o controller; (6)
apagar o arquivo original.

---

## RF-05 — Hash de senha seguro e sem vazamento (resolve AP-05)

**Antes**
```python
def set_password(self, pwd):
    self.password = hashlib.md5(pwd.encode()).hexdigest()

def to_dict(self):
    return {"id": self.id, "email": self.email, "password": self.password}
```

**Depois**
```python
from werkzeug.security import generate_password_hash, check_password_hash

def set_password(self, raw_password):
    self.password = generate_password_hash(raw_password)

def check_password(self, raw_password):
    return check_password_hash(self.password, raw_password)

def to_dict(self):
    # senha nunca é serializada
    return {"id": self.id, "name": self.name, "email": self.email, "role": self.role}
```

Em Node: `bcrypt.hash(pwd, 10)` / `bcrypt.compare(...)`.

**Compatibilidade**: trocar o algoritmo invalida hashes já gravados. Ou o seed é
reexecutado, ou o `check_password` aceita o hash antigo e regrava no formato novo
no primeiro login bem-sucedido. Escolha uma das duas e registre no relatório.

---

## RF-06 — Mover regra de negócio para model/service (resolve AP-06)

**Antes** — cálculo, persistência e notificação dentro do controller:
```python
def criar_pedido():
    dados = request.get_json()
    total = 0
    for item in dados["itens"]:
        cursor.execute("SELECT * FROM produtos WHERE id = " + str(item["produto_id"]))
        produto = cursor.fetchone()
        total += produto["preco"] * item["quantidade"]
    ...
    print("ENVIANDO EMAIL: ...")
    print("ENVIANDO SMS: ...")
    return jsonify({...}), 201
```

**Depois** — `services/pedido_service.py`
```python
class PedidoService:
    def __init__(self, pedido_model, produto_model, notificador):
        self.pedidos = pedido_model
        self.produtos = produto_model
        self.notificador = notificador

    def criar(self, usuario_id, itens):
        produtos = self.produtos.get_por_ids([i["produto_id"] for i in itens])
        total = self._calcular_total(itens, produtos)   # regra pura, testável
        pedido_id = self.pedidos.criar(usuario_id, itens, produtos, total)
        self.notificador.pedido_criado(pedido_id, usuario_id)
        return {"pedido_id": pedido_id, "total": total}
```

`controllers/pedido_controller.py`
```python
def criar_pedido(self):
    dados = request.get_json() or {}
    usuario_id, itens = validar_pedido(dados)          # levanta ValidationError
    resultado = self.service.criar(usuario_id, itens)  # sem try/except: erro sobe
    return jsonify({"dados": resultado, "sucesso": True}), 201
```

O controller encolhe para ~5 linhas e a regra vira testável sem HTTP.

---

## RF-07 — Eliminar estado global e injetar dependências (resolve AP-07, AP-08)

**Antes**
```javascript
// utils.js
let globalCache = {};
let totalRevenue = 0;
module.exports = { globalCache, totalRevenue };

// AppManager.js
class AppManager {
    constructor() { this.db = new sqlite3.Database(':memory:'); }
}
```

**Depois** — a dependência entra pelo construtor:
```javascript
// models/course.model.js
class CourseModel {
    constructor(db) { this.db = db; }
    findActiveById(id) {
        return this.db.get('SELECT * FROM courses WHERE id = ? AND active = 1', [id]);
    }
}

// app.js (composition root) — único lugar que instancia infraestrutura
const db = createDatabase(config.databasePath);
const courseModel = new CourseModel(db);
const checkoutService = new CheckoutService({ courseModel, userModel, paymentGateway });
const checkoutController = new CheckoutController(checkoutService);
app.use('/api', buildRoutes({ checkoutController }));
```

Estado que precisa sobreviver (receita acumulada, cache) vai para o banco ou
para um store explícito, nunca para variável de módulo mutável.

---

## RF-08 — Callback hell → async/await com transação (resolve AP-09, AP-12)

**Antes**
```javascript
this.db.get("SELECT * FROM courses WHERE id = ?", [cid], (err, course) => {
    this.db.get("SELECT id FROM users WHERE email = ?", [e], (err, user) => {
        this.db.run("INSERT INTO enrollments ...", [userId, cid], function(err) {
            self.db.run("INSERT INTO payments ...", [...], function(err) {
                self.db.run("INSERT INTO audit_logs ...", [...], (err) => {
                    res.status(200).json({ msg: "Sucesso" });
                });
            });
        });
    });
});
```

**Depois** — driver promisificado + transação:
```javascript
// infra/database.js
const run = (sql, params = []) => new Promise((resolve, reject) =>
    db.run(sql, params, function (err) { err ? reject(err) : resolve(this); }));

// services/checkout.service.js
async execute({ name, email, courseId, card }) {
    const course = await this.courses.findActiveById(courseId);
    if (!course) throw new NotFoundError('Curso não encontrado');

    const user = await this.users.findOrCreateByEmail({ name, email, password });
    const payment = await this.gateway.charge({ card, amount: course.price });
    if (payment.status === 'DENIED') throw new PaymentDeniedError();

    return this.db.transaction(async () => {           // tudo ou nada
        const enrollmentId = await this.enrollments.create(user.id, courseId);
        await this.payments.create(enrollmentId, course.price, payment.status);
        await this.auditLogs.create(`Checkout curso ${courseId} por ${user.id}`);
        return { enrollmentId };
    });
}
```

Erros passam a subir para o error handler; a escrita parcial deixa de existir.

---

## RF-09 — Matar N+1 com JOIN ou agregação (resolve AP-13)

**Antes** — 1 + N + N*M queries:
```python
for row in pedidos:
    cursor2.execute("SELECT * FROM itens_pedido WHERE pedido_id = " + str(row["id"]))
    for item in cursor2.fetchall():
        cursor3.execute("SELECT nome FROM produtos WHERE id = " + str(item["produto_id"]))
```

**Depois** — 2 queries, agrupando em memória:
```python
def listar_com_itens(self, usuario_id=None):
    pedidos = self._buscar_pedidos(usuario_id)
    if not pedidos:
        return []
    ids = [p["id"] for p in pedidos]
    placeholders = ",".join("?" * len(ids))
    cursor.execute(f"""
        SELECT i.pedido_id, i.produto_id, i.quantidade, i.preco_unitario, p.nome AS produto_nome
        FROM itens_pedido i
        LEFT JOIN produtos p ON p.id = i.produto_id
        WHERE i.pedido_id IN ({placeholders})
    """, ids)
    itens_por_pedido = defaultdict(list)
    for item in cursor.fetchall():
        itens_por_pedido[item["pedido_id"]].append(dict(item))
    for pedido in pedidos:
        pedido["itens"] = itens_por_pedido[pedido["id"]]
    return pedidos
```

No ORM, o equivalente é eager loading (`joinedload`/`selectinload`) ou
`func.count()` agrupado em vez de `len(lista)` e `COUNT` por item.

---

## RF-10 — Centralizar validação (resolve AP-14, AP-16)

**Antes** — a mesma sequência de `if` repetida em POST e PUT, com divergências.

**Depois** — `middlewares/validators.py`
```python
class ValidationError(Exception):
    def __init__(self, mensagem, status=400):
        self.mensagem, self.status = mensagem, status

STATUS_VALIDOS = ("pending", "in_progress", "done", "cancelled")
TITULO_MIN, TITULO_MAX = 3, 200

def validar_task(dados, parcial=False):
    if not dados:
        raise ValidationError("Dados inválidos")
    resultado = {}
    if "title" in dados or not parcial:
        titulo = (dados.get("title") or "").strip()
        if not TITULO_MIN <= len(titulo) <= TITULO_MAX:
            raise ValidationError(f"Título deve ter entre {TITULO_MIN} e {TITULO_MAX} caracteres")
        resultado["title"] = titulo
    if "status" in dados:
        if dados["status"] not in STATUS_VALIDOS:
            raise ValidationError("Status inválido")
        resultado["status"] = dados["status"]
    return resultado
```

Uma função por entidade, usada por criação (`parcial=False`) e atualização
(`parcial=True`). As constantes deixam de ser literais espalhados.

---

## RF-11 — Error handler centralizado (resolve AP-15, AP-17)

**Antes** — `try/except` idêntico em cada handler, devolvendo `str(e)` ao cliente.

**Depois** — `middlewares/error_handler.py`
```python
import logging
logger = logging.getLogger(__name__)

def registrar_error_handlers(app):
    @app.errorhandler(ValidationError)
    def _validacao(exc):
        return jsonify({"erro": exc.mensagem, "sucesso": False}), exc.status

    @app.errorhandler(NotFoundError)
    def _nao_encontrado(exc):
        return jsonify({"erro": str(exc), "sucesso": False}), 404

    @app.errorhandler(404)
    def _rota(_):
        return jsonify({"erro": "Recurso não encontrado", "sucesso": False}), 404

    @app.errorhandler(Exception)
    def _inesperado(exc):
        logger.exception("Erro não tratado")          # stack no log
        return jsonify({"erro": "Erro interno", "sucesso": False}), 500  # nunca no corpo
```

Em Express: `app.use((err, req, res, next) => {...})` registrado **depois** das
rotas. Os controllers deixam de ter `try/catch`; o erro sobe sozinho.

---

## RF-12 — Rotas declarativas (resolve AP-04, AP-06)

**Antes**
```python
app.add_url_rule("/produtos", "listar_produtos", controllers.listar_produtos, methods=["GET"])
# ... 16 linhas iguais, misturadas com handlers definidos no próprio app.py
```

**Depois** — `src/views/produto_routes.py`
```python
def criar_produto_blueprint(controller):
    bp = Blueprint("produtos", __name__, url_prefix="/produtos")
    bp.add_url_rule("", view_func=controller.listar, methods=["GET"])
    bp.add_url_rule("/busca", view_func=controller.buscar, methods=["GET"])
    bp.add_url_rule("/<int:produto_id>", view_func=controller.obter, methods=["GET"])
    bp.add_url_rule("", view_func=controller.criar, methods=["POST"])
    return bp
```

Um arquivo de rotas por recurso, sem nenhuma lógica; o `url_prefix` preserva os
paths originais.

---

## RF-13 — Substituir APIs deprecated (resolve a seção de deprecated)

| Antes | Depois |
|---|---|
| `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| `Task.query.get(id)` | `db.session.get(Task, id)` |
| `Task.query.filter_by(...).all()` | `db.session.execute(db.select(Task).filter_by(...)).scalars().all()` |
| `type(x) == list` | `isinstance(x, list)` |
| `except:` | `except Exception as exc:` |
| `new Buffer(x)` | `Buffer.from(x)` |
| `crypto.createHash('md5')` (senha) | `bcrypt.hash(pwd, 10)` |
| `sqlite3.verbose()` | driver sem `verbose` |

Atenção com `datetime.now(timezone.utc)`: gera datetime *aware*. Se o banco
guarda datetimes *naive*, comparar os dois levanta `TypeError` — normalize os
dois lados (grave sempre aware, ou compare com `datetime.now(timezone.utc).replace(tzinfo=None)`).

---

## RF-14 — Logging estruturado, constantes e limpeza (resolve AP-19, AP-20, AP-21, AP-22, AP-23)

**Antes**
```python
print("Listando " + str(len(produtos)) + " produtos")
if faturamento > 10000:
    desconto = faturamento * 0.1
if new_status in valid: return True
else: return False
import os, sys, json, datetime   # nada usado
```

**Depois**
```python
import logging
logger = logging.getLogger(__name__)

# config/constants.py
FAIXAS_DESCONTO = ((10_000, 0.10), (5_000, 0.05), (1_000, 0.02))

def calcular_desconto(faturamento):
    for limite, taxa in FAIXAS_DESCONTO:
        if faturamento > limite:
            return round(faturamento * taxa, 2)
    return 0.0

logger.info("Listando %d produtos", len(produtos))

def status_valido(status):
    return status in STATUS_VALIDOS
```

Também nesta etapa: renomear `u`/`e`/`cc` para nomes completos, remover imports
mortos, aplicar early return. **Nunca logar** senha, cartão ou chave de API.

---

## RF-15 — Autorização em rota sensível (resolve AP-11)

Este é o único RF que conflita de frente com a **regra inviolável nº 2**: exigir
credencial faz a rota responder 401 para um cliente que hoje recebe 200. Por isso
a tentação é não fazer nada — foi exatamente assim que AP-11 ficou reportado e
nunca corrigido.

Só que rota sensível aberta é o próprio finding. Deixar a imposição desligada
"para preservar o contrato" entrega o mecanismo e mantém o buraco: o relatório
financeiro continua respondendo a chamada anônima. **A imposição nasce ligada.**
O 401 nas rotas sensíveis é uma **mudança intencional de contrato** — a única
categoria que a regra nº 2 admite, e que por isso precisa estar declarada no
relatório, rota por rota.

O que continua separado é o **mecanismo** da **imposição**: `AUTH_ENFORCED=false`
existe como válvula de escape para quem precisa de uma janela de migração (dar
tempo aos clientes de passarem a mandar o header). Com a flag desligada o
contrato volta a ser o original e cada acesso anônimo a rota sensível **vira log
de aviso**, para o buraco ficar visível em vez de silencioso.

**Nunca** entregue só o mecanismo e declare o AP-11 resolvido: sem a imposição
ligada por padrão, o finding continua de pé.

### Passo 1 — classificar as rotas

Percorra **todas** as rotas e classifique uma a uma. Classificação incompleta é
o modo de falha mais comum deste RF — proteger `DELETE /users/:id` e esquecer
`PUT /users/:id` deixa o finding meio resolvido, que é o mesmo que não resolvido.

**Sensível** (recebe o middleware):
- lê dado de outro usuário — `GET /users/<id>`, `GET /users/<id>/tasks`,
  `GET /pedidos/usuario/<id>`;
- lê agregado do negócio — relatórios, faturamento, listagem de usuários,
  listagem de todos os pedidos/tasks, estatísticas;
- escreve ou apaga registro de terceiro — `PUT`/`DELETE` sobre entidade de
  usuário, mudança de status de pedido alheio;
- escreve em catálogo ou taxonomia (`POST`/`PUT`/`DELETE` de produto, categoria):
  é operação administrativa, ainda que a leitura correspondente seja pública;
- é administrativa por natureza — qualquer `/admin/*`.

**Aberta**:
- leitura pública de catálogo — `GET /produtos`, `GET /produtos/<id>`, busca;
- health check e raiz;
- auto-serviço em que o próprio autor se identifica: `POST /login`,
  cadastro (`POST /users`), checkout que recebe e-mail e senha do comprador.

O critério de "auto-serviço" é a identificação, não o verbo: uma rota que aceita
`usuario_id` no corpo **sem** provar quem é o chamador escreve registro de
terceiro e é sensível.

Registre a classificação inteira no relatório, incluindo o que ficou aberto e por
quê — é isso que permite revisar a decisão.

### Passo 2 — emitir credencial de verdade

Se o login devolve token falso (`'fake-jwt-token-' + id`) ou não devolve nada,
resolva isso primeiro — sem emissor não há o que verificar. Mantenha **o mesmo
formato de resposta**: se o campo se chama `token` e é string, continua `token` e
string; só o conteúdo passa a ser assinado.

**Antes** (Python)
```python
# rota de login
return jsonify({"token": "fake-jwt-token-" + str(user.id), "user": user.to_dict()})

# rota sensível: nenhuma checagem
@report_bp.route('/reports/summary')
def summary_report():
    ...
```

**Depois** (Python/Flask)
```python
# services/auth_service.py — emite e verifica
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

class AuthService:
    def __init__(self, settings):
        self._serializer = URLSafeTimedSerializer(settings.SECRET_KEY, salt=TOKEN_SALT)
        self._max_age = settings.TOKEN_MAX_AGE

    def emitir(self, user_id):
        return self._serializer.dumps({"user_id": user_id})

    def verificar(self, token):
        try:
            return self._serializer.loads(token, max_age=self._max_age)["user_id"]
        except (BadSignature, SignatureExpired):
            raise UnauthorizedError("Token inválido ou expirado")

# middlewares/auth.py — imposição ligada por padrão
def build_require_auth(settings, auth_service):
    def require_auth(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            token = _extrair_bearer(request.headers.get("Authorization", ""))
            if not settings.AUTH_ENFORCED:
                if not token:
                    logger.warning(
                        "Rota sensível acessada sem credencial: %s %s "
                        "(AUTH_ENFORCED=false — imposição desligada por configuração)",
                        request.method, request.path,
                    )
                return view(*args, **kwargs)
            if not token:
                raise UnauthorizedError("Credencial ausente")
            g.user_id = auth_service.verificar(token)
            return view(*args, **kwargs)
        return wrapper
    return require_auth

# views/report_routes.py — a rota declara o que precisa
bp.add_url_rule("/reports/summary", view_func=require_auth(controller.summary))
```

**Depois** (Node/Express)
```javascript
// middlewares/auth.js
function buildRequireAuth({ config, authService, logger }) {
    return (req, res, next) => {
        const token = (req.headers.authorization || '').replace(/^Bearer /, '');
        if (!config.auth.enforced) {
            if (!token) {
                logger.warn('Rota sensível acessada sem credencial', {
                    method: req.method, path: req.path,
                    hint: 'AUTH_ENFORCED=false — imposição desligada por configuração',
                });
            }
            return next();
        }
        if (!token) return next(new UnauthorizedError('Credencial ausente'));
        try {
            req.userId = authService.verify(token);
            return next();
        } catch (err) {
            return next(err);
        }
    };
}

// routes/report.routes.js
router.get('/admin/financial-report', requireAuth, asyncHandler(controller.financialReport));
```

Sem biblioteca de JWT no projeto, `crypto.createHmac` resolve: payload em base64url
+ assinatura HMAC-SHA256 com a chave do ambiente, comparada com `timingSafeEqual`.
Não invente esquema próprio de hash — assinatura é HMAC, e ponto.

O segredo de assinatura é configuração, nunca literal (AP-01): variável de
ambiente obrigatória em produção. Em desenvolvimento, gerar chave efêmera é
aceitável desde que o boot registre aviso — token não sobrevive a restart.

### Passo 3 — validar os dois modos

O smoke test da Fase 3 passa a rodar **duas vezes**:

| Modo | Esperado |
|---|---|
| `AUTH_ENFORCED=true` (padrão) | rotas sensíveis sem header → 401; com token do `/login` → mesmo status do baseline; rotas abertas → status do baseline |
| `AUTH_ENFORCED=false` (migração) | todas as rotas do baseline respondem o mesmo status de antes — contrato original restaurado, com `WARN` a cada acesso anônimo |

Teste também a rejeição: token com assinatura adulterada tem que responder 401,
senão a verificação é decorativa.

Se o segundo modo não for testado, a válvula de escape não foi entregue — foi só
escrita.

---

## Ordem de execução e validação

1. Aplique RF-01 → RF-15 na ordem das camadas (config primeiro, app por último).
2. Depois de cada camada, verifique que a aplicação ainda sobe.
3. Ao final: boot + smoke test de todas as rotas do baseline + varredura do
   catálogo sobre o código novo.
4. Só então apague os arquivos legados que ficaram sem uso.
