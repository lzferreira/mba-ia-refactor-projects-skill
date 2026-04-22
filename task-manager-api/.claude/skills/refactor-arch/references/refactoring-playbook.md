# Refactoring Playbook — Transformações Antes/Depois

Padrões concretos para corrigir os anti-patterns detectados na Fase 2. Cada padrão tem:

- **Quando aplicar** (condição de gatilho).
- **Exemplo antes/depois** em pelo menos uma linguagem — adapte a sintaxe para a stack do projeto. A ideia é universal.
- **Cuidados** (o que pode quebrar se você aplicar mal).

Os exemplos alternam Python e JavaScript por brevidade. Em stacks diferentes (Go, Ruby, Java), o princípio é o mesmo: extraia, parametrize, isole.

## Índice

1. [Extrair secrets hardcoded para config](#1-extrair-secrets-hardcoded-para-config)
2. [Parametrizar queries SQL](#2-parametrizar-queries-sql)
3. [Substituir hashing fraco por password hashing adequado](#3-substituir-hashing-fraco-por-password-hashing-adequado)
4. [Remover campos sensíveis da serialização](#4-remover-campos-sensíveis-da-serialização)
5. [Quebrar God Module em camadas por domínio](#5-quebrar-god-module-em-camadas-por-domínio)
6. [Extrair lógica de negócio de route handlers](#6-extrair-lógica-de-negócio-de-route-handlers)
7. [Extrair regras de negócio de models para services](#7-extrair-regras-de-negócio-de-models-para-services)
8. [Envolver operações multi-step em transação](#8-envolver-operações-multi-step-em-transação)
9. [Substituir estado global mutável por injeção](#9-substituir-estado-global-mutável-por-injeção)
10. [Corrigir N+1 com eager loading / batch](#10-corrigir-n1-com-eager-loading--batch)
11. [Centralizar validação em funções reutilizáveis](#11-centralizar-validação-em-funções-reutilizáveis)
12. [Centralizar error handling em middleware](#12-centralizar-error-handling-em-middleware)
13. [Substituir print por logger estruturado](#13-substituir-print-por-logger-estruturado)
14. [Modernizar APIs deprecated](#14-modernizar-apis-deprecated)
15. [Aplicar whitelist de campos em updates (anti-mass-assignment)](#15-aplicar-whitelist-de-campos-em-updates-anti-mass-assignment)
16. [Proteger endpoints administrativos](#16-proteger-endpoints-administrativos)

---

## 1. Extrair secrets hardcoded para config

**Quando aplicar:** qualquer finding de "Hardcoded Secrets / Credentials".

**Antes (Python/Flask):**
```python
# app.py
SECRET_KEY = "minha-chave-super-secreta-123"
DB_PASSWORD = "admin123"
DEBUG = True
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
```

**Depois:**
```python
# config/settings.py
import os

def _required(name):
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    return value

SECRET_KEY = _required("SECRET_KEY")
DB_PASSWORD = _required("DB_PASSWORD")
DEBUG = os.environ.get("DEBUG", "false").lower() == "true"
```

```python
# app.py
from config.settings import SECRET_KEY, DEBUG
app = Flask(__name__)
app.config["SECRET_KEY"] = SECRET_KEY
```

Inclua um `.env.example` listando as variáveis obrigatórias (sem valores reais).

**Cuidado:** não faça commit de `.env`. Adicione ao `.gitignore`. Chaves já expostas no histórico devem ser **rotacionadas** mesmo depois de removidas — o commit antigo ainda está lá.

---

## 2. Parametrizar queries SQL

**Quando aplicar:** qualquer finding de "SQL Injection".

**Antes (Python):**
```python
def find_user(email):
    cursor.execute("SELECT * FROM users WHERE email = '" + email + "'")
```

**Depois:**
```python
def find_user(email):
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
```

**Antes (Node):**
```javascript
db.query(`SELECT * FROM users WHERE id = ${req.params.id}`, cb);
```

**Depois:**
```javascript
db.query("SELECT * FROM users WHERE id = ?", [req.params.id], cb);
```

**Cuidado:** alguns drivers usam placeholders diferentes (`$1` no `pg`, `%s` no `psycopg2`, `?` no `sqlite3`/`mysql2`, `:name` em nomeados). Combine o placeholder com o driver — misturar gera erro de runtime.

Para nomes de tabela/coluna dinâmicos (que placeholders não cobrem), use uma **allowlist** estrita, nunca input do usuário direto.

---

## 3. Substituir hashing fraco por password hashing adequado

**Quando aplicar:** finding de "Weak or Broken Cryptography" afetando senhas.

**Antes (Python):**
```python
import hashlib

def hash_password(password):
    return hashlib.md5(password.encode()).hexdigest()

def verify(password, hashed):
    return hash_password(password) == hashed
```

**Depois (usando bcrypt):**
```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())
```

**Antes (Node):**
```javascript
function badCrypto(pw) {
  let x = pw || "123456";
  for (let i = 0; i < 10000; i++) x = Buffer.from(x).toString("base64");
  return x.slice(0, 10);
}
```

**Depois:**
```javascript
const bcrypt = require("bcrypt");
async function hashPassword(pw) {
  return bcrypt.hash(pw, 12);
}
async function verify(pw, hashed) {
  return bcrypt.compare(pw, hashed);
}
```

**Cuidado:**
1. Nunca deixe um fallback tipo `pw || "123456"` — rejeite senha vazia na validação.
2. A troca **quebra usuários existentes** — os hashes antigos MD5 não validam com bcrypt. Estratégias: força reset no próximo login; ou valide em ambos e regere em bcrypt no primeiro login bem-sucedido.
3. Para tokens aleatórios, use `secrets.token_urlsafe(32)` (Python) ou `crypto.randomBytes(32).toString("hex")` (Node), nunca `random()`/`Math.random()`.

---

## 4. Remover campos sensíveis da serialização

**Quando aplicar:** finding de "Sensitive Data Exposure in Responses".

**Antes:**
```python
class User:
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "password_hash": self.password_hash,  # BOOM
            "role": self.role,
        }
```

**Depois:**
```python
class User:
    PUBLIC_FIELDS = ("id", "email", "role", "created_at")

    def to_dict(self):
        return {k: getattr(self, k) for k in self.PUBLIC_FIELDS}
```

Mesma ideia em JS:
```javascript
function serializeUser(u) {
  return { id: u.id, email: u.email, role: u.role };
}
```

**Cuidado:** busque no projeto inteiro por `to_dict`, `toJSON`, `.serialize()`, `jsonify(user)` — geralmente o bug está espalhado. Também revise endpoints `/health`, `/debug`, `/config` que podem cuspir a config inteira.

---

## 5. Quebrar God Module em camadas por domínio

**Quando aplicar:** finding de "God Class / God Module".

Estratégia em passos:

1. Liste os domínios presentes no arquivo (ex: `users`, `products`, `orders`).
2. Para cada domínio, crie 3 arquivos: `models/<dominio>_model.py`, `controllers/<dominio>_controller.py`, `routes/<dominio>_routes.py`.
3. Mova as funções pelo papel:
   - Queries SQL → model.
   - Fluxo HTTP + orquestração → controller.
   - Registro de rotas → routes.
4. Mantenha a mesma assinatura pública dos endpoints. Shapes de request/response **não mudam**.
5. Rode boot + smoke test depois de cada domínio extraído. Refatorar tudo junto e rodar no fim é a receita para debug de horas.

**Antes (esqueleto):**
```python
# models.py  ← 350 linhas
def get_produtos(): ...
def criar_pedido(user_id, items): ...
def login(email, senha): ...
def relatorio_vendas(): ...
```

**Depois:**
```
src/
├── models/
│   ├── produto_model.py
│   ├── pedido_model.py
│   └── usuario_model.py
├── controllers/
│   ├── produto_controller.py
│   ├── pedido_controller.py
│   └── usuario_controller.py
├── routes/
│   └── api_routes.py
└── app.py  # registra blueprints
```

**Cuidado:** resista à tentação de melhorar tudo no caminho. Mover primeiro, refatorar depois. Caso contrário o diff vira impossível de revisar.

---

## 6. Extrair lógica de negócio de route handlers

**Quando aplicar:** finding de "Fat Controllers" (handler > 50 linhas com `if/else` de domínio).

**Antes (Flask):**
```python
@app.route("/orders", methods=["POST"])
def create_order():
    data = request.json
    total = 0
    for item in data["items"]:
        produto = db.query("SELECT * FROM produtos WHERE id=?", (item["id"],)).fetchone()
        if produto["estoque"] < item["qty"]:
            return jsonify({"erro": "sem estoque"}), 400
        total += produto["preco"] * item["qty"]
    if total > 10000:
        total = total * 0.9
    elif total > 5000:
        total = total * 0.95
    db.execute("INSERT INTO pedidos ...")
    return jsonify({"total": total})
```

**Depois:**
```python
# services/order_service.py
class OrderService:
    def __init__(self, product_repo, order_repo):
        self.products = product_repo
        self.orders = order_repo

    def create(self, items):
        self._ensure_stock(items)
        total = self._calculate_total(items)
        total = self._apply_discount(total)
        return self.orders.insert(items, total)

    def _ensure_stock(self, items): ...
    def _calculate_total(self, items): ...
    def _apply_discount(self, total):
        if total > 10000: return total * 0.9
        if total > 5000:  return total * 0.95
        return total
```

```python
# controllers/order_controller.py
class OrderController:
    def __init__(self, service):
        self.service = service

    def create(self, payload):
        order = self.service.create(payload["items"])
        return order, 201
```

```python
# routes/order_routes.py
@bp.route("/orders", methods=["POST"])
def create_order():
    order, status = controller.create(request.json)
    return jsonify(order), status
```

**Cuidado:** a fronteira certa é "onde isso poderia ser reusado?". A regra de desconto pode ser chamada por um relatório futuro → service. O status code 201 só existe no mundo HTTP → routes.

---

## 7. Extrair regras de negócio de models para services

**Quando aplicar:** finding de "Fat Models" (model fazendo cálculo/validação/notificação além de persistir).

**Antes (JS/Sequelize-ish):**
```javascript
class Product {
  async reduceStock(qty) {
    if (qty > this.stock) throw new Error("insufficient stock");
    this.stock -= qty;
    await this.save();
    if (this.stock < 10) await sendEmail("ops@co.com", "low stock!");
    return this;
  }
}
```

**Depois:**
```javascript
class Product {
  // só persistência
  async decrementStock(qty) { this.stock -= qty; return this.save(); }
}

class InventoryService {
  constructor(productRepo, notifier) {
    this.productRepo = productRepo;
    this.notifier = notifier;
  }
  async reserve(productId, qty) {
    const p = await this.productRepo.get(productId);
    if (qty > p.stock) throw new InsufficientStockError();
    await p.decrementStock(qty);
    if (p.stock < 10) await this.notifier.lowStock(p);
    return p;
  }
}
```

**Cuidado:** o model fica "anêmico" nesse estilo — é o trade-off consciente. Alternativa: manter métodos de domínio puros no model (sem I/O) e mover apenas efeitos colaterais para service.

---

## 8. Envolver operações multi-step em transação

**Quando aplicar:** finding de "Missing Transactions".

**Antes (Node/sqlite3):**
```javascript
db.run("INSERT INTO enrollments ...", (err) => {
  if (err) return cb(err);
  db.run("INSERT INTO payments ...", (err2) => {  // se falha, enrollment já foi
    if (err2) return cb(err2);
    cb(null, ok);
  });
});
```

**Depois (Node com better-sqlite3):**
```javascript
const checkout = db.transaction((enrollment, payment) => {
  db.prepare("INSERT INTO enrollments ...").run(enrollment);
  db.prepare("INSERT INTO payments ...").run(payment);
});

function runCheckout(enrollment, payment) {
  checkout(enrollment, payment);  // atômico: todo ou nada
}
```

**Antes (Python):**
```python
def checkout(user_id, items):
    db.execute("INSERT INTO orders ...")
    db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", ...)
    db.execute("INSERT INTO payments ...")
    db.commit()
```

**Depois:**
```python
def checkout(user_id, items):
    try:
        with db:  # sqlite3 context manager = transação
            db.execute("INSERT INTO orders ...")
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", ...)
            db.execute("INSERT INTO payments ...")
    except Exception:
        raise  # rollback automático ao sair do with com exceção
```

**Cuidado:** transações longas travam linhas. Mantenha a transação **pequena** — só as operações que precisam ser atômicas entre si. Side effects externos (email, webhook) ficam fora da transação.

---

## 9. Substituir estado global mutável por injeção

**Quando aplicar:** finding de "Global Mutable State".

**Antes (Python):**
```python
# database.py
db = sqlite3.connect("app.db", check_same_thread=False)  # singleton global
```

**Depois (Flask):**
```python
# config/database.py
def create_connection(path):
    return sqlite3.connect(path)

# app.py (composition root)
from flask import g
def get_db():
    if "db" not in g:
        g.db = create_connection(settings.DB_PATH)
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop("db", None)
    if db: db.close()
```

Agora cada request tem a própria conexão, fechada ao final.

**Antes (JS):**
```javascript
// utils.js
const globalCache = {};
let totalRevenue = 0;
```

**Depois:**
```javascript
// cache.js
class InMemoryCache {
  constructor(maxSize = 1000) { this.map = new Map(); this.max = maxSize; }
  set(k, v) {
    if (this.map.size >= this.max) {
      const firstKey = this.map.keys().next().value;
      this.map.delete(firstKey);
    }
    this.map.set(k, v);
  }
  get(k) { return this.map.get(k); }
}
```

Injete `new InMemoryCache()` no composition root e passe para quem precisar.

**Cuidado:** para valores verdadeiramente singleton (ex: logger), não é errado ter no topo do módulo — mas deve ser **imutável** e não ter estado específico de request.

---

## 10. Corrigir N+1 com eager loading / batch

**Quando aplicar:** finding de "N+1 Queries".

**Antes (SQL cru):**
```python
pedidos = db.query("SELECT * FROM pedidos WHERE user_id = ?", user_id).fetchall()
for pedido in pedidos:
    itens = db.query("SELECT * FROM itens WHERE pedido_id = ?", pedido["id"]).fetchall()
    pedido["itens"] = itens  # 1 + N queries
```

**Depois (JOIN):**
```python
rows = db.query("""
    SELECT p.id, p.total, i.produto_id, i.qty
    FROM pedidos p
    LEFT JOIN itens i ON i.pedido_id = p.id
    WHERE p.user_id = ?
""", user_id).fetchall()
# agrupa em memória: 1 query
```

**Antes (ORM Sequelize):**
```javascript
const orders = await Order.findAll({ where: { userId } });
for (const o of orders) {
  o.items = await Item.findAll({ where: { orderId: o.id } });
}
```

**Depois:**
```javascript
const orders = await Order.findAll({
  where: { userId },
  include: [{ model: Item }],   // eager loading
});
```

Equivalentes:
- SQLAlchemy: `joinedload(Order.items)` ou `selectinload`.
- Django: `.select_related("user").prefetch_related("items")`.
- Prisma: `include: { items: true }`.

**Cuidado:** `JOIN` puro pode duplicar linhas se o relacionamento é 1:N — prefira `selectinload`/"second query" se o ORM oferece. Meça antes e depois.

---

## 11. Centralizar validação em funções reutilizáveis

**Quando aplicar:** finding de "Duplicated Validation".

**Antes (Python):**
```python
def criar_produto():
    data = request.json
    if not data.get("nome"): return erro()
    if data.get("preco", 0) <= 0: return erro()
    if data.get("estoque", 0) < 0: return erro()
    if data.get("categoria") not in ["A","B","C"]: return erro()
    ...

def atualizar_produto(id):
    data = request.json
    if not data.get("nome"): return erro()
    if data.get("preco", 0) <= 0: return erro()
    if data.get("estoque", 0) < 0: return erro()
    if data.get("categoria") not in ["A","B","C"]: return erro()
    ...
```

**Depois:**
```python
# validators/product_validator.py
VALID_CATEGORIES = ("A", "B", "C")

def validate_product_payload(data: dict) -> None:
    errors = []
    if not data.get("nome"): errors.append("nome obrigatório")
    if data.get("preco", 0) <= 0: errors.append("preço deve ser positivo")
    if data.get("estoque", 0) < 0: errors.append("estoque não pode ser negativo")
    if data.get("categoria") not in VALID_CATEGORIES: errors.append("categoria inválida")
    if errors:
        raise ValidationError(errors)
```

Use nos dois handlers:
```python
def criar_produto():
    data = request.json
    validate_product_payload(data)
    ...
```

**Cuidado:** se há schemas disponíveis na stack (pydantic, marshmallow, zod, joi, class-validator), prefira-os — ganham documentação automática e mensagens estruturadas de erro.

---

## 12. Centralizar error handling em middleware

**Quando aplicar:** findings de "Broad Exception Handlers" e para remover `try/except` pulverizado.

**Antes (Flask):**
```python
@app.route("/products/<id>")
def get_product(id):
    try:
        p = Product.query.get(id)
        if not p: return jsonify({"erro": "not found"}), 404
        return jsonify(p.to_dict())
    except Exception as e:
        return jsonify({"erro": str(e)}), 500  # vaza stack
```

**Depois:**
```python
# middlewares/errors.py
class AppError(Exception):
    status = 500
    message = "Internal error"

class NotFound(AppError):
    status = 404; message = "Resource not found"

class ValidationError(AppError):
    status = 400

def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(e):
        return jsonify({"error": e.message}), e.status

    @app.errorhandler(Exception)
    def handle_unexpected(e):
        app.logger.exception("unhandled error")  # stack no log
        return jsonify({"error": "Internal server error"}), 500
```

```python
# routes
@app.route("/products/<id>")
def get_product(id):
    p = Product.query.get(id)
    if not p:
        raise NotFound()
    return jsonify(p.to_dict())
```

**Antes (Express):**
```javascript
app.get("/products/:id", (req, res) => {
  try { ... } catch (e) { res.status(500).json({error: e.stack}); }
});
```

**Depois:**
```javascript
app.get("/products/:id", asyncHandler(async (req, res) => {
  const p = await repo.get(req.params.id);
  if (!p) throw new NotFoundError();
  res.json(p);
}));

// no final, depois de todas as rotas:
app.use((err, req, res, next) => {
  if (err.status) return res.status(err.status).json({ error: err.message });
  logger.error(err);
  res.status(500).json({ error: "Internal server error" });
});
```

**Cuidado:** loge o erro inesperado completo no servidor (com stack), mas devolva apenas mensagem genérica no body. Stack no cliente é vazamento de informação.

---

## 13. Substituir print por logger estruturado

**Quando aplicar:** finding de "Print-Based Logging".

**Antes (Python):**
```python
print("ERRO CRITICO: falha ao criar pedido", user_id, e)
```

**Depois:**
```python
# config/logger.py
import logging, sys, json
def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format='{"ts":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","msg":"%(message)s"}',
        stream=sys.stdout,
    )

# no código
logger = logging.getLogger(__name__)
logger.error("failed to create order", extra={"user_id": user_id}, exc_info=True)
```

**Antes (Node):**
```javascript
console.log("user logged in", email);
```

**Depois:**
```javascript
const pino = require("pino");
const logger = pino({ level: process.env.LOG_LEVEL || "info" });
logger.info({ email }, "user logged in");
```

**Cuidado:** nunca loge campos sensíveis (password, token, número de cartão) — configure redação se o logger suportar, ou apenas omita.

---

## 14. Modernizar APIs deprecated

**Quando aplicar:** finding de "Deprecated APIs".

### 14a. Python — `type(x) == list` → `isinstance`

```python
# antes
if type(x) == list: ...

# depois
if isinstance(x, list): ...
```

Funciona com subclasses e é o idioma pythônico.

### 14b. Python — `datetime.utcnow()` → timezone-aware

```python
# antes
from datetime import datetime
now = datetime.utcnow()

# depois
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
```

Evita bugs silenciosos de timezone ao serializar/comparar.

### 14c. Node — sqlite3 callbacks → promisificado

```javascript
// antes
const sqlite3 = require("sqlite3").verbose();
db.all("SELECT * FROM x", (err, rows) => {
  if (err) return cb(err);
  cb(null, rows);
});

// depois (better-sqlite3, síncrono)
const Database = require("better-sqlite3");
const db = new Database("app.db");
const rows = db.prepare("SELECT * FROM x").all();

// ou (sqlite wrapper com promises)
const sqlite = require("sqlite");
const db = await sqlite.open({ filename: "app.db", driver: sqlite3.Database });
const rows = await db.all("SELECT * FROM x");
```

### 14d. Node — `new Buffer(x)` → `Buffer.from(x)`

```javascript
// antes
const b = new Buffer(data);

// depois
const b = Buffer.from(data);
```

### 14e. Node — `request` → `fetch`/`undici`

```javascript
// antes
const request = require("request");
request.get(url, (err, res, body) => { ... });

// depois (Node 18+ nativo)
const res = await fetch(url);
const body = await res.json();
```

**Cuidado:** mudar SDK/driver é upgrade real — rode os testes completos depois. Não misture callbacks e promises no meio do caminho; migre arquivo por arquivo até cobrir tudo.

---

## 15. Aplicar whitelist de campos em updates (anti-mass-assignment)

**Quando aplicar:** finding de "Privilege Escalation via Mass Assignment".

**Antes:**
```python
@app.route("/users/<id>", methods=["PUT"])
def update_user(id):
    user = User.get(id)
    for key, value in request.json.items():
        setattr(user, key, value)   # inclui role=admin :(
    user.save()
```

**Depois:**
```python
ALLOWED_SELF_UPDATE = {"name", "email", "avatar"}

@app.route("/users/<id>", methods=["PUT"])
def update_user(id):
    if request.user.id != int(id) and not request.user.is_admin:
        raise Forbidden()
    user = User.get(id)
    allowed = ALLOWED_SELF_UPDATE
    if request.user.is_admin:
        allowed = allowed | {"role"}
    for key in allowed & set(request.json.keys()):
        setattr(user, key, request.json[key])
    user.save()
```

**Cuidado:** combine sempre com autorização — a allowlist evita escalonamento mas não garante que o usuário certo está atualizando o recurso certo.

---

## 16. Proteger endpoints administrativos

**Quando aplicar:** finding de "Unprotected Admin / Privileged Endpoints".

**Antes:**
```python
@app.route("/admin/reset-db", methods=["POST"])
def reset_db():
    db.execute("DELETE FROM ...")
    return "ok"
```

**Depois:**
```python
# middlewares/auth.py
from functools import wraps
from flask import request

def require_admin(f):
    @wraps(f)
    def wrapper(*a, **kw):
        user = authenticate(request)
        if not user or user.role != "admin":
            raise Forbidden()
        return f(*a, **kw)
    return wrapper

# routes
@app.route("/admin/reset-db", methods=["POST"])
@require_admin
def reset_db(): ...
```

**Cuidado:** endpoints de reset/seed idealmente não existem em produção. Se existirem, além de `require_admin`, gate por ambiente (`if settings.ENV != "dev": raise NotFound()`).

---

## Ordem recomendada de aplicação

Ao aplicar múltiplos padrões em um mesmo projeto, siga esta ordem para minimizar retrabalho:

1. **Extrair config** (padrão 1) — tudo depende disso.
2. **Quebrar God Module** (padrão 5) — cria os diretórios onde o resto vai morar.
3. **Segurança CRÍTICA**: parametrizar SQL (2), hashing (3), remover campos sensíveis (4), proteger admin (16), whitelist (15). Faz o projeto sair do "perigoso" antes de ser "bonito".
4. **Separação MVC**: extrair lógica de routes (6), de models (7).
5. **Confiabilidade**: transações (8), estado global (9), error handler central (12).
6. **Performance**: N+1 (10).
7. **Qualidade**: validação central (11), logger (13), deprecated APIs (14).

Valide (boot + smoke test) depois de cada grupo grande. Não vá direto do início ao fim sem rodar o servidor uma vez.
