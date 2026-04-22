# Anti-patterns Catalog

Catálogo de anti-patterns que a Fase 2 deve cruzar contra o código. Cada entrada tem **sinais de detecção** (o que procurar no código, em termos agnósticos) e **severidade** fixa.

A severidade segue a escala da skill:

- **CRITICAL** — falhas de segurança ou arquitetura que quebram a aplicação ou expõem dados sensíveis.
- **HIGH** — violações fortes de MVC/SOLID que impedem manutenção e testes.
- **MEDIUM** — problemas de padronização, performance moderada ou duplicação.
- **LOW** — melhorias de legibilidade, nomenclatura e padronização cosmética.

A lista cobre 5 categorias: **Segurança, MVC/SOLID, Performance, Qualidade de código, APIs deprecated**. Não é exaustiva — adicione findings que não se encaixem exatamente em uma entrada aqui desde que a categoria e severidade estejam justificadas.

## Sumário

### CRITICAL
1. [Hardcoded Secrets / Credentials](#1-hardcoded-secrets--credentials)
2. [SQL Injection](#2-sql-injection)
3. [Weak or Broken Cryptography](#3-weak-or-broken-cryptography)
4. [Sensitive Data Exposure in Responses](#4-sensitive-data-exposure-in-responses)
5. [Unprotected Admin / Privileged Endpoints](#5-unprotected-admin--privileged-endpoints)
6. [Debug Mode / Verbose Errors in Production](#6-debug-mode--verbose-errors-in-production)
7. [Arbitrary Code / SQL Execution Endpoint](#7-arbitrary-code--sql-execution-endpoint)

### HIGH
8. [God Class / God Module](#8-god-class--god-module)
9. [Business Logic in Controllers (Fat Controllers)](#9-business-logic-in-controllers-fat-controllers)
10. [Business Logic in Models (Fat Models)](#10-business-logic-in-models-fat-models)
11. [Missing Transactions in Multi-Step Operations](#11-missing-transactions-in-multi-step-operations)
12. [Global Mutable State](#12-global-mutable-state)
13. [Privilege Escalation via Mass Assignment](#13-privilege-escalation-via-mass-assignment)
14. [Callback Hell / Unstructured Async](#14-callback-hell--unstructured-async)

### MEDIUM
15. [N+1 Queries](#15-n1-queries)
16. [Duplicated Validation](#16-duplicated-validation)
17. [Broad Exception Handlers / Stack-Trace Leakage](#17-broad-exception-handlers--stack-trace-leakage)
18. [Missing Pagination / Unbounded Results](#18-missing-pagination--unbounded-results)
19. [Weak Input Validation](#19-weak-input-validation)
20. [Side Effects in Controllers](#20-side-effects-in-controllers)

### LOW
21. [Magic Numbers / Magic Strings](#21-magic-numbers--magic-strings)
22. [Dead Code / Unused Imports](#22-dead-code--unused-imports)
23. [Print-Based Logging](#23-print-based-logging)
24. [Inconsistent Naming and Response Format](#24-inconsistent-naming-and-response-format)
25. [Deprecated APIs](#25-deprecated-apis)

---

## CRITICAL

### 1. Hardcoded Secrets / Credentials

**Por que CRITICAL:** qualquer pessoa com acesso ao repositório (ou a um leak dele) tem as chaves de produção. É irreversível — uma vez commitada, a secret precisa ser rotacionada.

**Sinais de detecção:**
- Strings literais em variáveis chamadas `SECRET_KEY`, `API_KEY`, `PASSWORD`, `DB_PASSWORD`, `JWT_SECRET`, `STRIPE_KEY`, `SMTP_PASS`, `AWS_ACCESS_KEY_ID`.
- URIs de conexão completas (`postgres://user:pass@host/db`, `mongodb://...:...`) em arquivos-fonte.
- Prefixos de chaves reais: `pk_live_`, `sk_live_`, `AKIA...`, `ghp_...`, `xoxb-...`.
- Senha literal como fallback (`password or "123456"`).

**Anti-exemplo conceitual:** `SECRET_KEY = "minha-chave-super-secreta"`

---

### 2. SQL Injection

**Por que CRITICAL:** permite ao atacante ler, modificar ou apagar o banco inteiro.

**Sinais de detecção:**
- Query SQL construída via concatenação ou interpolação de strings com valores vindos de request (`"SELECT * FROM users WHERE id = " + userId`, f-strings com `{user_input}` dentro de SQL, template literals `` `...${x}...` `` em queries).
- Uso de `cursor.execute(sql_pronto)` sem parâmetros quando `sql_pronto` foi montado a partir de variáveis.
- ORMs com `raw()` / `query()` recebendo strings montadas.

**Oposto correto:** placeholders parametrizados (`?`, `%s`, `$1`, `:name`), com valores passados separadamente.

---

### 3. Weak or Broken Cryptography

**Por que CRITICAL:** senhas vazadas em um banco com hash fraco (ou nenhum hash real) são quebradas em segundos por rainbow tables ou brute force.

**Sinais de detecção:**
- `md5(senha)`, `sha1(senha)`, `hashlib.md5(...)`, `crypto.createHash('md5')` para senhas.
- Hash sem salt (dois usuários com a mesma senha têm o mesmo hash).
- Funções caseiras: concatenação, XOR, `base64.encode(senha)`, loops de "embaralhamento".
- Senhas em texto puro (sem hash algum).
- Uso de `Math.random()` / `random.random()` para gerar tokens ou IDs de sessão.

**Oposto correto:** bcrypt, argon2 ou scrypt com salt aleatório e custo adequado; `crypto.randomBytes`/`secrets` para tokens.

---

### 4. Sensitive Data Exposure in Responses

**Por que CRITICAL:** basta chamar o endpoint para exfiltrar a coluna `password`/`token`/`secret` do banco. Geralmente uma violação combinada de MVC (model cuspindo tudo que tem) + segurança.

**Sinais de detecção:**
- Serializers que devolvem o modelo inteiro (`to_dict()`, `.toJSON()`, `jsonify(user.__dict__)`) sem filtro.
- Respostas JSON contendo campos `password`, `password_hash`, `token`, `secret`, `api_key`, `ssn`, `card_number`.
- Endpoints que dão "echo" da config (`/health` retornando `SECRET_KEY` ou `DEBUG=true`).
- Logs que imprimem o body do request contendo cartão, senha ou token.

---

### 5. Unprotected Admin / Privileged Endpoints

**Por que CRITICAL:** qualquer cliente externo consegue apagar o banco, promover-se a admin, ou listar dados sensíveis.

**Sinais de detecção:**
- Rotas como `/admin/*`, `/debug/*`, `/internal/*`, `/reset-db`, `/flush-cache` sem middleware de autenticação/autorização.
- Handlers que fazem `DELETE`/`DROP`/`TRUNCATE` acessíveis via HTTP sem checar role.
- Endpoint de "reset" ou "seed" disponível em produção.
- Endpoints que aceitam um header `X-Admin: true` e confiam nele.

---

### 6. Debug Mode / Verbose Errors in Production

**Por que CRITICAL:** modo debug de muitos frameworks expõe um console interativo que permite execução remota de código (Werkzeug debugger no Flask, por exemplo). Stack traces completos em produção revelam estrutura interna do código.

**Sinais de detecção:**
- `debug=True`, `DEBUG=True`, `app.debug = true`, `NODE_ENV` não checado.
- `app.run(debug=True)`, `flask run --debug` em scripts de produção.
- `console.error(err.stack)` mandado no response body.
- Mensagens de erro como `"erro": str(e)` onde `e` é uma exception com stack interno.

---

### 7. Arbitrary Code / SQL Execution Endpoint

**Por que CRITICAL:** endpoint que executa o que vier no body do request. É RCE ou full-DB-access disfarçado de "ferramenta de admin".

**Sinais de detecção:**
- Handler chamando `eval(request.body)`, `exec(...)`, `Function(code)()`.
- Handler chamando `cursor.execute(request.json['query'])`.
- Endpoints `/query`, `/run`, `/execute`, `/cmd` com entrada livre.

---

## HIGH

### 8. God Class / God Module

**Por que HIGH:** impossível testar em isolamento, qualquer mudança afeta tudo, ninguém ousa tocar porque o risco é enorme.

**Sinais de detecção:**
- Um único arquivo > 300–500 linhas contendo **dois ou mais** de: conexão com banco, schema/DDL, roteamento, validação, regra de negócio, serialização.
- Classe com > 15 métodos que operam em domínios distintos (usuários + produtos + pedidos na mesma classe).
- Arquivo `utils.js` / `helpers.py` que virou depósito: conexão de DB + cálculos + formatação + estado global juntos.

---

### 9. Business Logic in Controllers (Fat Controllers)

**Por que HIGH:** acopla a regra à camada HTTP. Não dá para reusar a regra em um worker, CLI ou teste unitário sem subir um request.

**Sinais de detecção:**
- Handler de rota com > 50 linhas contendo `if/else` de regra de domínio (cálculo de desconto, decisão de aprovar pedido, agregação de relatório).
- Route handler que monta JOINs e agrega resultados em vez de delegar.
- Route handler que chama diretamente `Email.send()`, `SMS.send()`, `push.notify()` em meio ao fluxo.

---

### 10. Business Logic in Models (Fat Models)

**Por que HIGH:** o inverso do anterior. Quando o model decide baixar estoque, calcular desconto, enviar notificação — ele vira um segundo God Object.

**Sinais de detecção:**
- Método `save()` ou `create()` que executa regras não relacionadas à persistência (calcular imposto, escolher gateway de pagamento).
- Model com referência direta a serviços externos (SMTP, Redis, fila).
- Validação de regra de domínio (`if estoque < quantidade: raise`) misturada com CRUD.

Observação: "fat model vs fat controller" é uma tensão clássica. A saída é uma **camada de service** para regras que não pertencem nem ao model (dados puros) nem ao controller (fluxo HTTP).

---

### 11. Missing Transactions in Multi-Step Operations

**Por que HIGH:** falha no meio deixa o banco inconsistente. Ex: matrícula feita mas pagamento não registrado, estoque baixado mas pedido não criado.

**Sinais de detecção:**
- Dois ou mais `INSERT`/`UPDATE` consecutivos no mesmo handler sem `BEGIN`/`COMMIT`, `with db.transaction()`, `async.transaction()`, `@transactional`.
- Operação de checkout, transferência, matrícula, cancelamento — candidatos naturais a transação.
- Mensagens no próprio código tipo `// TODO: wrap in transaction` ou `// this should be atomic`.

---

### 12. Global Mutable State

**Por que HIGH:** estado compartilhado entre requests leva a race conditions, leaks de dados entre usuários e testes flaky.

**Sinais de detecção:**
- Conexão de banco como singleton mutável em nível de módulo (`db = sqlite3.connect(..., check_same_thread=False)`).
- Caches globais crescendo sem bound (`globalCache = {}` no topo do módulo).
- Contadores "total", "counter", "last_id" em escopo de módulo modificados por handlers.
- Variáveis `export let totalRevenue = 0` mutadas em qualquer lugar.

---

### 13. Privilege Escalation via Mass Assignment

**Por que HIGH:** rota de update aceita qualquer campo do body — incluindo `role`, `is_admin`, `verified`, `balance`. Qualquer user vira admin.

**Sinais de detecção:**
- `PUT /users/:id` que faz `Object.assign(user, req.body)`, `user.update(**request.json)`, `User.objects.filter(id=id).update(**request.data)`.
- Ausência de whitelist/allowlist dos campos atualizáveis.
- Ausência de checagem de autorização (o usuário pode atualizar a si mesmo mas não outros; usuário comum não pode mudar `role`).

---

### 14. Callback Hell / Unstructured Async

**Por que HIGH:** código profundamente aninhado onde erros são frequentemente engolidos, lógica fica ilegível e composição fica impossível. Comum em Node legado e código que não migrou para Promises/async-await.

**Sinais de detecção:**
- Três ou mais níveis de callbacks aninhados (`db.query(..., (err, rows) => { db.query(..., (err2, r2) => { ... }) })`).
- Contadores manuais de "pending" (`let pending = n; ... if (--pending === 0) done()`).
- Callbacks onde `err` é checado mas só logado e a execução continua como se nada.

---

## MEDIUM

### 15. N+1 Queries

**Por que MEDIUM:** performance degrada linearmente com o tamanho da lista. Invisível em dev com 10 registros, fatal em prod com 10k.

**Sinais de detecção:**
- Loop sobre uma lista de registros fazendo uma query por iteração (`for pedido in pedidos: itens = db.query("SELECT ... WHERE pedido_id = ?", pedido.id)`).
- Em ORMs: ausência de `select_related`/`prefetch_related` (Django), `joinedload` (SQLAlchemy), `include` (Sequelize/Prisma), `Includes` (EF).
- Serialização que dispara lazy-loading em cada elemento.

---

### 16. Duplicated Validation

**Por que MEDIUM:** a regra é mantida em dois lugares e eventualmente diverge. Bug garantido quando um lado é atualizado.

**Sinais de detecção:**
- Mesma lista de checagens (presence, length, formato) em handlers de `POST` e `PUT` para o mesmo recurso.
- Mesma regex/string de validação copiada em múltiplos arquivos.
- `VALID_STATUSES` definido em um módulo mas strings literais usadas nas rotas.

---

### 17. Broad Exception Handlers / Stack-Trace Leakage

**Por que MEDIUM:** bugs silenciosos + potencial de vazar detalhes internos no response.

**Sinais de detecção:**
- `except Exception as e: return jsonify({"error": str(e)})` — leak direto.
- `except:` (sem tipo) ou `catch (e) {}` vazio — engole tudo.
- `try { ... } catch(e) { console.log(e); }` sem repropagação e sem resposta HTTP correta.

---

### 18. Missing Pagination / Unbounded Results

**Por que MEDIUM:** `GET /users` que devolve 10 milhões de registros derruba o servidor ou o cliente. Também leva a downstream que não aguenta.

**Sinais de detecção:**
- Listagens sem parâmetro `limit`/`page`/`cursor`.
- Handlers que fazem `.find({})` / `.all()` / `SELECT * FROM table` sem `LIMIT`.
- Reports/summary que agregam tabela inteira em memória.

---

### 19. Weak Input Validation

**Por que MEDIUM:** combinado com outros anti-patterns, amplifica o impacto. Sozinho, leva a respostas 500 e corrupção leve de dados.

**Sinais de detecção:**
- Apenas checagem de presença (`if not data.get('email')`) sem checar formato.
- Regras de negócio fortes baseadas em input controlado pelo cliente (`if cc.startsWith("4"): approve()` usando o cartão para decidir aprovação).
- Aceita tipos errados sem converter/rejeitar (espera int, recebe string, passa adiante).

---

### 20. Side Effects in Controllers

**Por que MEDIUM:** Envio de email, SMS, push, webhook inline no handler HTTP. Acopla a rota ao serviço externo e bloqueia a resposta.

**Sinais de detecção:**
- `send_email(...)`, `smtp.send(...)`, `sms.send(...)`, `push.notify(...)`, `requests.post(webhook_url)` dentro de um route handler.
- Envio síncrono no caminho crítico do request quando poderia ser uma fila/worker.

---

## LOW

### 21. Magic Numbers / Magic Strings

**Por que LOW:** não quebra nada, mas torna a intenção opaca. Difícil mudar uma regra quando ela está enterrada.

**Sinais de detecção:**
- Comparações com literais sem nome (`if total > 10000`, `if role == "adm"`) repetidas no código.
- Listas inline repetidas (`categorias_validas = ["A", "B", "C"]` em vários lugares).

---

### 22. Dead Code / Unused Imports

**Por que LOW:** ruído. Indica também decaimento de cuidado no projeto.

**Sinais de detecção:**
- Imports `os`, `sys`, `json`, `time`, `math` em arquivos que não os usam.
- Funções/classes nunca referenciadas.
- Arquivos comentados ou marcados `// deprecated, remove later` há muito tempo.

---

### 23. Print-Based Logging

**Por que LOW:** sem níveis, sem contexto, sem destino estruturado. Impossível filtrar em prod.

**Sinais de detecção:**
- `print(...)` / `console.log(...)` usado para logging real (não debug efêmero).
- Logs em ALL-CAPS (`"ERRO CRITICO"`) misturados com logs normais.
- Ausência de logger estruturado (`logging`, `winston`, `pino`, `zap`, `logrus`).

---

### 24. Inconsistent Naming and Response Format

**Por que LOW:** torna o contrato imprevisível para o consumidor.

**Sinais de detecção:**
- Mistura de idiomas em nomes (`usuario` vs `user`, `erro` vs `error`) no mesmo projeto.
- Umas rotas retornam `{"sucesso": true, ...}` e outras só `{...}`.
- `snake_case` e `camelCase` misturados em campos de response.
- Códigos HTTP inconsistentes (200 quando deveria ser 201, 500 para erro de validação).

---

### 25. Deprecated APIs

**Por que LOW (ou superior conforme o caso):** APIs obsoletas tipicamente têm melhores substitutos (mais seguros, mais performáticos, ou com melhor ergonomia). Ignorar a depreciação eventualmente quebra quando o ecossistema remove o suporte.

Esta categoria **deve sempre ser verificada** — o desafio exige detecção explícita.

**Sinais de detecção (por stack):**

| Stack | Pattern deprecated | Moderno equivalente |
|---|---|---|
| Node | `sqlite3` callbacks `db.all(sql, cb)` | `better-sqlite3` sync ou wrapper `sqlite` com promises |
| Node | `new Buffer(x)` | `Buffer.from(x)` |
| Node | `request` lib | `fetch`/`undici`/`axios` |
| Node | `fs.exists(path, cb)` | `fs.existsSync` / `fs.promises.access` |
| Node | `util.isArray`, `util.isString` | `Array.isArray`, `typeof x === 'string'` |
| Python | `type(x) == list` | `isinstance(x, list)` |
| Python | `datetime.utcnow()` | `datetime.now(timezone.utc)` |
| Python | `hashlib.md5(senha)` para senha | `bcrypt` / `argon2-cffi` |
| Python | `imp` module | `importlib` |
| Python | `urllib2`, `urllib.urlopen` no Py3 | `urllib.request` ou `requests`/`httpx` |
| Python | `pkg_resources` | `importlib.metadata`, `importlib.resources` |
| Python | `Flask.before_first_request` | lifecycle do Flask 2.3+ / factory com setup explícito |
| Ruby | `Fixnum`/`Bignum` | `Integer` |
| Java | `java.util.Date` mutável | `java.time.*` |
| Java | `SimpleDateFormat` não thread-safe | `DateTimeFormatter` |
| C# | `WebClient` | `HttpClient` |
| PHP | `mysql_*` funções | `mysqli` ou PDO |
| Geral SQL | Drivers callback-style | Drivers com suporte a `async/await`/`context` |

Para cada deprecated detectado, registre o equivalente moderno na recomendação do finding.
