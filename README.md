# Desafio Skills — Refatoração Arquitetural Automatizada

Este repositório é o fork do boilerplate do desafio de Skills (MBA). Contém três projetos legados (Python/Flask e Node.js/Express) que servem de insumo para a construção de uma skill `refactor-arch` capaz de auditar e migrar qualquer um deles para o padrão MVC.

## Análise Manual

Antes de construir a skill, cada projeto foi lido linha a linha para mapear os problemas de arquitetura, segurança e qualidade que a skill precisa detectar. A classificação segue a escala definida em [desafio.md:21-28](desafio.md#L21-L28) (CRITICAL / HIGH / MEDIUM / LOW).

> **Notação:** cada finding aponta arquivo e linha exatos (`file:line`) para permitir verificação direta no código.

### Projeto 1 — code-smells-project (Python/Flask, API de E-commerce)

Monolito de 4 arquivos (~800 LOC) com roteamento, regras de negócio, queries SQL e seed misturados. Os achados abaixo são representativos — há repetição do mesmo padrão em vários pontos.

| # | Severidade | Finding | Arquivo:Linha |
|---|---|---|---|
| 1 | **CRITICAL** | SQL Injection por concatenação de strings em todas as queries (produtos, usuários, login, pedidos, busca) | [models.py:28](code-smells-project/models.py#L28), [models.py:47-50](code-smells-project/models.py#L47-L50), [models.py:109-111](code-smells-project/models.py#L109-L111), [models.py:289-297](code-smells-project/models.py#L289-L297) |
| 2 | **CRITICAL** | Endpoint `/admin/query` executa SQL arbitrário vindo do body — RCE no banco | [app.py:59-78](code-smells-project/app.py#L59-L78) |
| 3 | **CRITICAL** | Rotas administrativas (`/admin/reset-db`, `/admin/query`) sem autenticação — qualquer cliente apaga o banco | [app.py:47-78](code-smells-project/app.py#L47-L78) |
| 4 | **CRITICAL** | Senhas em texto puro no banco, no seed, no login e retornadas pela API (`get_todos_usuarios` expõe a coluna `senha`) | [models.py:83](code-smells-project/models.py#L83), [models.py:109-120](code-smells-project/models.py#L109-L120), [database.py:76-79](code-smells-project/database.py#L76-L79) |
| 5 | **CRITICAL** | `SECRET_KEY` hardcoded e, pior, devolvida no payload de `/health` junto de `debug=True` | [app.py:7](code-smells-project/app.py#L7), [controllers.py:287-289](code-smells-project/controllers.py#L287-L289) |
| 6 | **HIGH** | "God Module" — `models.py` concentra 4 domínios (produtos, usuários, pedidos, relatório) com SQL, mapeamento e regras de negócio | [models.py:1-315](code-smells-project/models.py#L1-L315) |
| 7 | **HIGH** | Regra de negócio (cálculo de desconto escalonado, checagem de estoque, baixa de estoque) dentro da camada de modelo | [models.py:133-169](code-smells-project/models.py#L133-L169), [models.py:256-263](code-smells-project/models.py#L256-L263) |
| 8 | **HIGH** | Conexão SQLite global mutável com `check_same_thread=False` — estado compartilhado e corrida de threads | [database.py:4-10](code-smells-project/database.py#L4-L10) |
| 9 | **HIGH** | `DEBUG=True` hardcoded + `app.run(debug=True)` — Werkzeug debugger habilitado permite execução remota de código | [app.py:8](code-smells-project/app.py#L8), [app.py:88](code-smells-project/app.py#L88) |
| 10 | **MEDIUM** | N+1: listar pedidos roda uma query por item e outra por produto dentro do loop | [models.py:187-199](code-smells-project/models.py#L187-L199), [models.py:219-231](code-smells-project/models.py#L219-L231) |
| 11 | **MEDIUM** | Validação duplicada e ad-hoc entre `criar_produto` e `atualizar_produto` (nome, preço, estoque, categoria) | [controllers.py:28-55](code-smells-project/controllers.py#L28-L55), [controllers.py:72-91](code-smells-project/controllers.py#L72-L91) |
| 12 | **MEDIUM** | Side effects de notificação (email/SMS/push via `print`) dentro do controller de pedidos | [controllers.py:208-210](code-smells-project/controllers.py#L208-L210), [controllers.py:247-250](code-smells-project/controllers.py#L247-L250) |
| 13 | **MEDIUM** | `except Exception as e: return jsonify({"erro": str(e)})` vaza stack trace / detalhes internos em todas as rotas | [controllers.py:10-12](code-smells-project/controllers.py#L10-L12), [controllers.py:60-62](code-smells-project/controllers.py#L60-L62) |
| 14 | **LOW** | Logging via `print()` misturado com ALL-CAPS ("ERRO CRITICO") — sem logger estruturado | [controllers.py:8](code-smells-project/controllers.py#L8), [controllers.py:161](code-smells-project/controllers.py#L161), [controllers.py:219](code-smells-project/controllers.py#L219) |
| 15 | **LOW** | Magic numbers e listas duplicadas (categorias válidas, faixas de desconto 10000/5000/1000 com taxas 0.1/0.05/0.02) | [controllers.py:52](code-smells-project/controllers.py#L52), [models.py:257-262](code-smells-project/models.py#L257-L262) |
| 16 | **LOW** | Concatenação manual com `str()` em vez de f-strings, formato de erro inconsistente (PT/EN misturados, `sucesso` presente em umas respostas e ausente em outras) | [controllers.py:8](code-smells-project/controllers.py#L8), [controllers.py:57](code-smells-project/controllers.py#L57) |

**Justificativa dos destaques:** os 5 CRITICAL fazem o projeto inviável em qualquer ambiente com usuários reais (injeção + plaintext + RCE). Os HIGH são o que mais trava a refatoração para MVC: sem quebrar `models.py` e `app.py`, não há como isolar camadas.

---

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

Três arquivos (`app.js`, `AppManager.js`, `utils.js`). O fluxo de checkout (pagamento + matrícula + auditoria) é todo implementado como callbacks aninhados dentro de uma única classe "gerente".

| # | Severidade | Finding | Arquivo:Linha |
|---|---|---|---|
| 1 | **CRITICAL** | Credenciais de produção hardcoded: senha do DB, chave `pk_live_` do gateway de pagamento, SMTP | [src/utils.js:1-7](ecommerce-api-legacy/src/utils.js#L1-L7) |
| 2 | **CRITICAL** | Número do cartão completo + chave do gateway logados em `console.log` — violação direta de PCI-DSS | [src/AppManager.js:45](ecommerce-api-legacy/src/AppManager.js#L45) |
| 3 | **CRITICAL** | `badCrypto` faz 10.000 concatenações base64 e retorna 10 chars — não é hash criptográfico; além disso usa senha default `"123456"` se o usuário não mandar uma | [src/utils.js:17-23](ecommerce-api-legacy/src/utils.js#L17-L23), [src/AppManager.js:68](ecommerce-api-legacy/src/AppManager.js#L68) |
| 4 | **HIGH** | "God Class" `AppManager`: dona da conexão, do schema, do seed, do roteamento, dos controllers e das regras de pagamento | [src/AppManager.js:1-142](ecommerce-api-legacy/src/AppManager.js#L1-L142) |
| 5 | **HIGH** | Checkout sem transação atômica — se `INSERT INTO payments` falha, a matrícula já está commitada → estado inconsistente | [src/AppManager.js:50-63](ecommerce-api-legacy/src/AppManager.js#L50-L63) |
| 6 | **HIGH** | Callback hell no financial-report com contadores manuais (`coursesPending`, `enrPending`) — race-condition-prone e engole erros | [src/AppManager.js:80-129](ecommerce-api-legacy/src/AppManager.js#L80-L129) |
| 7 | **MEDIUM** | Validação de input limitada a `presence check`; aceita `card`, `email`, `usr` sem checar formato — e ainda usa o cartão para decidir aprovação (`cc.startsWith("4")`) | [src/AppManager.js:28-46](ecommerce-api-legacy/src/AppManager.js#L28-L46) |
| 8 | **MEDIUM** | `DELETE /api/users/:id` documenta na própria resposta que deixa matrículas/pagamentos órfãos no banco | [src/AppManager.js:131-137](ecommerce-api-legacy/src/AppManager.js#L131-L137) |
| 9 | **MEDIUM** | SQLite `:memory:` em projeto que se diz de produção — toda data some no restart | [src/AppManager.js:7](ecommerce-api-legacy/src/AppManager.js#L7) |
| 10 | **MEDIUM** | Estado global mutável: `globalCache` cresce sem bound e `totalRevenue` é exportado mas nunca atualizado | [src/utils.js:9-10](ecommerce-api-legacy/src/utils.js#L9-L10), [src/utils.js:25](ecommerce-api-legacy/src/utils.js#L25) |
| 11 | **LOW** | Nomes crípticos de variáveis: `u`, `e`, `p`, `cid`, `cc` no body do checkout | [src/AppManager.js:29-33](ecommerce-api-legacy/src/AppManager.js#L29-L33) |
| 12 | **LOW** | API de callbacks do `sqlite3` + `sqlite3.verbose()`: padrão deprecated em favor de promise/async (`better-sqlite3`, `sqlite` wrapper, etc.) | [src/AppManager.js:1](ecommerce-api-legacy/src/AppManager.js#L1) |
| 13 | **LOW** | Sem middleware central de erro no Express — erros são checados inline em cada callback e frequentemente ignorados | [src/app.js:1-14](ecommerce-api-legacy/src/app.js#L1-L14), [src/AppManager.js:133-137](ecommerce-api-legacy/src/AppManager.js#L133-L137) |
| 14 | **LOW** | Magic literal: `cc.startsWith("4")` como regra de aprovação (prefixo VISA) | [src/AppManager.js:46](ecommerce-api-legacy/src/AppManager.js#L46) |

**Justificativa dos destaques:** o trio CRITICAL (credenciais em claro + log de PAN + hashing fake) combinado com a ausência de transação (HIGH #5) torna o fluxo de checkout perigoso — a skill precisa reconhecer esses três padrões explicitamente.

---

### Projeto 3 — task-manager-api (Python/Flask, Task Manager com organização parcial)

Projeto já separado em `models/`, `routes/`, `services/`, `utils/`. A separação existe fisicamente mas não na lógica: a camada de routes faz serialização, agregação e validação; services guarda credenciais; utils acumula funções não utilizadas.

| # | Severidade | Finding | Arquivo:Linha |
|---|---|---|---|
| 1 | **CRITICAL** | MD5 sem salt para senhas — quebrado, vulnerável a rainbow tables | [models/user.py:29](task-manager-api/models/user.py#L29), [models/user.py:32](task-manager-api/models/user.py#L32) |
| 2 | **CRITICAL** | Hash da senha incluído em todas as respostas `to_dict()` — vaza credenciais em `/users`, `/users/<id>`, `/login`, `/users/<id>/tasks` | [models/user.py:17-25](task-manager-api/models/user.py#L17-L25), [routes/user_routes.py:85](task-manager-api/routes/user_routes.py#L85), [routes/user_routes.py:207-211](task-manager-api/routes/user_routes.py#L207-L211) |
| 3 | **CRITICAL** | Credenciais SMTP e `SECRET_KEY` hardcoded no código | [services/notification_service.py:9-10](task-manager-api/services/notification_service.py#L9-L10), [app.py:13](task-manager-api/app.py#L13) |
| 4 | **HIGH** | Nenhuma rota exige autenticação/autorização: listar/deletar usuários, reports, categorias — tudo público. `/login` devolve um "fake-jwt-token-<id>" | [routes/user_routes.py:10-151](task-manager-api/routes/user_routes.py#L10-L151), [routes/user_routes.py:210](task-manager-api/routes/user_routes.py#L210) |
| 5 | **HIGH** | `PUT /users/<id>` aceita alterar `role` sem checagem — qualquer caller promove-se a admin | [routes/user_routes.py:119-122](task-manager-api/routes/user_routes.py#L119-L122) |
| 6 | **HIGH** | Regras de negócio (agregação de reports, cálculo de overdue, productivity) vivem nos handlers de rota — controllers gordos | [routes/report_routes.py:12-101](task-manager-api/routes/report_routes.py#L12-L101), [routes/task_routes.py:273-299](task-manager-api/routes/task_routes.py#L273-L299) |
| 7 | **HIGH** | Lógica de "overdue" duplicada em 5 lugares (model + 4 rotas diferentes), cada uma com `if / else` aninhado | [models/task.py:50-60](task-manager-api/models/task.py#L50-L60), [routes/task_routes.py:30-39](task-manager-api/routes/task_routes.py#L30-L39), [routes/task_routes.py:71-80](task-manager-api/routes/task_routes.py#L71-L80), [routes/user_routes.py:171-181](task-manager-api/routes/user_routes.py#L171-L181), [routes/report_routes.py:33-43](task-manager-api/routes/report_routes.py#L33-L43) |
| 8 | **MEDIUM** | N+1 generalizado: loops que chamam `User.query.get` / `Category.query.get` / `Task.query.filter_by` por registro em vez de um JOIN | [routes/task_routes.py:41-57](task-manager-api/routes/task_routes.py#L41-L57), [routes/report_routes.py:53-68](task-manager-api/routes/report_routes.py#L53-L68) |
| 9 | **MEDIUM** | Bare `except:` engolindo erros silenciosamente em múltiplas rotas — mascara bugs e dificulta troubleshooting | [routes/task_routes.py:62-63](task-manager-api/routes/task_routes.py#L62-L63), [routes/task_routes.py:236-238](task-manager-api/routes/task_routes.py#L236-L238), [routes/user_routes.py:130-132](task-manager-api/routes/user_routes.py#L130-L132), [routes/report_routes.py:186-188](task-manager-api/routes/report_routes.py#L186-L188) |
| 10 | **MEDIUM** | Sem paginação / limite nas listagens (`GET /tasks`, `/users`, `/reports/summary` carrega tudo) | [routes/task_routes.py:11-63](task-manager-api/routes/task_routes.py#L11-L63), [routes/report_routes.py:12-101](task-manager-api/routes/report_routes.py#L12-L101) |
| 11 | **MEDIUM** | "Fake JWT" hardcoded no login pode ser confundido com autenticação real pelo frontend | [routes/user_routes.py:210](task-manager-api/routes/user_routes.py#L210) |
| 12 | **LOW** | Imports não utilizados em quase todos os arquivos (`os`, `sys`, `json`, `time`, `math`, `hashlib`) | [app.py:7](task-manager-api/app.py#L7), [routes/task_routes.py:7](task-manager-api/routes/task_routes.py#L7), [utils/helpers.py:1-7](task-manager-api/utils/helpers.py#L1-L7) |
| 13 | **LOW** | `type(x) == list` em vez de `isinstance(x, list)` — não-pythônico e não lida com subclasses | [routes/task_routes.py:141](task-manager-api/routes/task_routes.py#L141), [routes/task_routes.py:210](task-manager-api/routes/task_routes.py#L210), [utils/helpers.py:103](task-manager-api/utils/helpers.py#L103) |
| 14 | **LOW** | Constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` declaradas em `helpers.py` mas rotas usam strings soltas — convenção morta | [utils/helpers.py:110-116](task-manager-api/utils/helpers.py#L110-L116), [routes/task_routes.py:110](task-manager-api/routes/task_routes.py#L110), [routes/user_routes.py:71](task-manager-api/routes/user_routes.py#L71) |
| 15 | **LOW** | `is_overdue` com `if/else` aninhado profundo que poderia ser uma única expressão booleana | [models/task.py:50-60](task-manager-api/models/task.py#L50-L60) |

**Justificativa dos destaques:** este é o projeto que "parece" arrumado mas vaza credenciais em cada resposta (CRITICAL #2) e permite escalonamento de privilégio via PUT (HIGH #5). A skill precisa ir além de olhar a estrutura de pastas — tem que inspecionar o conteúdo dos handlers e serializers.

---

### Padrões recorrentes nos 3 projetos (insumo para a skill)

Agrupando os findings, as categorias que a skill deve reconhecer são:

- **Segurança:** credenciais/hash hardcoded, SQL injection via concatenação, hashing fraco (MD5 sem salt, "badCrypto" caseiros), vazamento de senha/secret em resposta da API, endpoints administrativos sem auth, debug mode em produção.
- **MVC / SOLID:** God Class/Module (tudo num arquivo), lógica de negócio em controllers, lógica de negócio em models, estado global mutável, ausência de camada service.
- **Performance:** N+1 queries, ausência de paginação, transações faltando em operações multi-step.
- **Qualidade:** `except:` / `try/except Exception` que engolem erros, validação duplicada entre endpoints de create/update, magic numbers/strings, logging via `print`, imports mortos, nomes crípticos.
- **APIs deprecated:** `sqlite3` callback-style em Node, `type(x) == list`, chamadas sem `onupdate`/timezone-aware datetime.

---

## Construção da Skill

### Decisões de design

A skill `refactor-arch` foi construída em **3 fases sequenciais com confirmação** entre cada uma:

1. **Análise** — leitura do projeto, detecção de tecnologia (Python/Flask, Node.js/Express, etc.) e mapeamento de todos os anti-patterns encontrados.
2. **Auditoria com confirmação** — geração do relatório de auditoria em `reports/` com findings classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW); aguarda aprovação do usuário antes de qualquer escrita.
3. **Refatoração com validação** — reestrutura o projeto para MVC, executa a aplicação e valida cada endpoint antes de declarar sucesso.

### Anti-patterns incluídos e justificativa

Os padrões foram escolhidos pela recorrência nos três projetos e pelo impacto real em produção:

| Categoria | Anti-pattern | Motivo da inclusão |
|---|---|---|
| Segurança | Credenciais/secrets hardcoded | Presentes nos 3 projetos; risco imediato de vazamento |
| Segurança | SQL Injection por concatenação | Vetor de ataque direto; trivial de explorar |
| Segurança | Hashing fraco (MD5, base64-loop) | Senhas quebráveis offline; violação de PCI-DSS |
| Segurança | Senha/hash em respostas da API | Vaza credenciais para qualquer consumidor da API |
| Segurança | Debug mode em produção | Werkzeug debugger = execução remota de código |
| Arquitetura | God Class / God Module | Impede isolamento de camadas; bloqueador da refatoração |
| Arquitetura | Lógica de negócio em routes/controllers | Viola Single Responsibility; dificulta teste unitário |
| Arquitetura | Estado global mutável | Race conditions em cenários multi-thread/multi-request |
| Arquitetura | Ausência de camada Service | Lógica transacional (ex: checkout) sem fronteira clara |
| Performance | N+1 queries | Degradação exponencial com volume de dados |
| Performance | Transação ausente em operações multi-step | Estado inconsistente em caso de falha parcial |
| Qualidade | `except:` / bare except engolindo erros | Mascara bugs; impossibilita troubleshooting |
| Qualidade | `print()` como logging | Sem nível, sem estrutura, sem destino configurável |
| Qualidade | Validação duplicada entre create/update | Divergência silenciosa de regras ao longo do tempo |
| APIs | `sqlite3` callback-style (Node) | Padrão deprecated; callback hell; engole erros |

### Agnóstica de tecnologia

A skill detecta a stack em tempo de execução inspecionando extensões de arquivo e arquivos de manifesto (`requirements.txt`, `package.json`, `go.mod`, etc.) antes de aplicar qualquer regra. Os padrões de detecção são expressos em linguagem natural (não em regex fixos de uma linguagem), permitindo ao modelo aplicar o mesmo raciocínio a Python, Node.js, Ruby, Go, Java ou PHP sem reescrever a lógica central.

### Desafios encontrados

- **Preservar contrato de API:** a refatoração precisou documentar explicitamente as mudanças no contrato HTTP (ex: remoção do campo `senha` das respostas, remoção de endpoints `/admin/reset-db`). Cada projeto tem uma seção "Changes to External Contract" ou equivalente no seu README para rastreabilidade.
- **Banco de dados incompatível após mudança de hash:** no `code-smells-project`, a migração de senhas plaintext para bcrypt tornou o banco SQLite existente incompatível — o seed precisou ser refeito.
- **Projeto "falso-organizado":** o `task-manager-api` já tinha pastas `models/`, `routes/`, `services/` mas a separação era apenas física — a lógica de negócio ainda vivia nas routes. A skill precisou ir além da estrutura de diretórios e inspecionar o conteúdo dos handlers.
- **Decidir o que não corrigir:** autenticação real (JWT/session) foi conscientemente deixada de fora nos três projetos pois requer decisões de produto (estratégia de auth, armazenamento de token) que extrapolam o escopo de uma refatoração arquitetural automatizada.

---

## Resultados

### Resumo por projeto

| Projeto | Stack | Anti-patterns encontrados |
|---|---|---|
| code-smells-project | Python/Flask | 19 |
| ecommerce-api-legacy | Node.js/Express | 14 |
| task-manager-api | Python/Flask | 26 |

### Comparação antes/depois — estrutura de arquivos

**code-smells-project** (antes: 4 arquivos monolíticos → depois: 15+ arquivos em 7 camadas)

```
ANTES                          DEPOIS
app.py (~100 LOC)              config/settings.py, config/database.py, config/logger.py
models.py (~315 LOC)           models/produto_model.py, models/usuario_model.py, models/pedido_model.py
controllers.py (~290 LOC)      controllers/ (5 arquivos)
database.py (~80 LOC)          services/ (2 arquivos), validators/, middlewares/, routes/
```

**ecommerce-api-legacy** (antes: 3 arquivos → depois: 14 arquivos em 6 camadas)

```
ANTES                          DEPOIS
src/app.js (14 LOC)            src/app.js (wiring only)
src/AppManager.js (142 LOC)    src/config/, src/controllers/ (3), src/models/ (6)
src/utils.js (25 LOC)          src/routes/, src/services/ (2), src/middlewares/
```

**task-manager-api** (antes: estrutura física existia, lógica misturada → depois: separação real de responsabilidades)

```
ANTES                          DEPOIS
routes/ com lógica de negócio  controllers/ com lógica de negócio extraída
models/ sem serialização limpa models/ com to_dict() sem campo senha
services/ com credentials      services/ limpos, credentials em config/settings.py
utils/ com funções mortas      utils/helpers.py enxuto, constantes usadas
```

### Checklist de validação

#### code-smells-project

- [x] Aplicação sobe sem erros (`python app.py`)
- [x] 17 endpoints respondem corretamente (GET, POST, PUT, DELETE)
- [x] `GET /health` não expõe `secret_key`, `db_path` ou `debug`
- [x] `GET /usuarios` não inclui campo `senha`
- [x] Queries parametrizadas (sem SQL injection por concatenação)
- [x] Senhas armazenadas com bcrypt
- [x] `SECRET_KEY` e `DEBUG` lidos de variáveis de ambiente
- [x] Endpoints `/admin/reset-db` e `/admin/query` removidos


#### ecommerce-api-legacy

- [x] Aplicação sobe sem erros (`npm start`)
- [x] `POST /api/checkout` (cartão válido) → 200 + enrollment_id
- [x] `POST /api/checkout` (cartão negado) → 400 + mensagem de erro
- [x] `POST /api/checkout` (campos ausentes) → 400 Bad Request
- [x] `GET /api/admin/financial-report` → 200 + dados corretos
- [x] `DELETE /api/users/:id` → 200 + cascade cleanup
- [x] Nenhum dado sensível (cartão, chave gateway) nos logs
- [x] Checkout wrapped em transação atômica (`db.transaction()`)
- [x] Senhas com bcryptjs (salt rounds 10)


#### task-manager-api

- [x] Aplicação sobe sem erros (`python app.py`)
- [x] Todos os 21 endpoints respondem (GET, POST, PUT, DELETE)
- [x] `GET /users` e `GET /users/<id>` não incluem campo `password_hash`
- [x] `POST /login` usa pbkdf2:sha256 (werkzeug) em vez de MD5
- [x] `SECRET_KEY` e credenciais SMTP lidos de variáveis de ambiente
- [x] Lógica de negócio extraída das routes para controllers
- [x] `is_overdue` centralizado em `Task.is_overdue()` (1 lugar)
- [x] N+1 eliminado com `joinedload` / `dynamic` relationships
- [x] `bare except` substituídos por `except Exception`
- [x] `print()` substituído por `logging`


### Relatórios de auditoria detalhados

Cada projeto gerou um relatório completo em formato Markdown na pasta `reports/` do respectivo projeto:

- [`reports/audit-code-smells-project.md`](reports/audit-code-smells-project.md)
- [`reports/audit-ecommerce-api-legacy.md`](reports/audit-ecommerce-api-legacy.md)
- [`reports/audit-task-manager.md`](reports/audit-task-manager.md)

---

## Como Executar

### Pré-requisitos

| Ferramenta | Versão mínima | Verificação |
|---|---|---|
| Python | 3.9+ | `python3 --version` |
| Node.js | 18+ | `node --version` |
| npm | 8+ | `npm --version` |
| Claude Code CLI | latest | `claude --version` |

### Executar a skill `refactor-arch` em um projeto

```bash
# No diretório do projeto que deseja refatorar:
cd <projeto>
claude
/refactor-arch
```

A skill perguntará confirmação antes de gravar qualquer arquivo.

### Rodar cada projeto refatorado

#### code-smells-project

```bash
cd code-smells-project
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edite se necessário
python app.py                  # sobe em http://localhost:5001
```

Validação rápida:
```bash
curl http://localhost:5001/health
curl http://localhost:5001/produtos
curl http://localhost:5001/usuarios   # campo senha ausente
```

#### ecommerce-api-legacy

```bash
cd ecommerce-api-legacy
npm install
cp .env.example .env          # edite se necessário
npm start                      # sobe em http://localhost:3000
```

Validação rápida:
```bash
# Checkout aprovado (cartão Visa)
curl -s -X POST http://localhost:3000/api/checkout \
  -H "Content-Type: application/json" \
  -d '{"user_id":1,"course_id":1,"card_number":"4111111111111111","email":"test@test.com"}' | jq .

# Relatório financeiro
curl http://localhost:3000/api/admin/financial-report | jq .
```

#### task-manager-api

```bash
cd task-manager-api
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # edite se necessário
python seed.py                 # popula o banco (rode antes do primeiro boot)
python app.py                  # sobe em http://localhost:5000
```

Validação rápida:
```bash
curl http://localhost:5000/health
curl http://localhost:5000/tasks
curl http://localhost:5000/users   # campo password_hash ausente
curl "http://localhost:5000/tasks/search?status=pending"
```

### Validar que a refatoração funcionou

Cada projeto expõe um endpoint `/health` que confirma que a aplicação está de pé sem expor configuração interna. Além disso, verifique:

1. **Sem secrets no código:** `grep -r "SECRET_KEY\s*=" */config/ */services/ */models/` não deve retornar valores literais.
2. **Sem senhas nas respostas:** `curl .../users | python3 -m json.tool | grep -i "senha\|password\|hash"` deve retornar vazio.
3. **Estrutura MVC presente:** cada projeto deve ter as pastas `models/`, `controllers/` (ou equivalente), `routes/`, `services/` e `config/`.
4. **Sem `print()` como logging:** `grep -r "^\s*print(" */controllers/ */services/ */models/` deve retornar vazio.
