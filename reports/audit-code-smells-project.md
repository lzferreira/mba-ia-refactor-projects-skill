================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-04-21

## Summary
CRITICAL: 7 | HIGH: 4 | MEDIUM: 5 | LOW: 3

## Findings

### [CRITICAL-01] SQL Injection via String Concatenation (models.py — generalizado)
File: models.py:30,38-41,49-51,62-64,80,93-95,101-103,113,121-124,128-131,134-136,148,155-157,175,183-186,246-251
Description: Praticamente **todas** as queries do projeto são construídas por concatenação de strings com valores vindos do request (`"SELECT * FROM produtos WHERE id = " + str(id)`, `"... WHERE email = '" + email + "' AND senha = '" + senha + "'"`, etc.). Isso se repete em ~15 funções distintas.
Impact: Um atacante consegue ler, modificar ou apagar qualquer tabela do banco via input malicioso. No login, permite bypass de autenticação (`' OR '1'='1`). É a vulnerabilidade mais explorada da web.
Recommendation: Substituir toda concatenação por placeholders parametrizados (`cursor.execute("SELECT * FROM produtos WHERE id = ?", (id,))`). Ver padrão 2 do playbook.

### [CRITICAL-02] Arbitrary SQL Execution Endpoint
File: app.py:56-72
Description: O endpoint `POST /admin/query` recebe SQL arbitrário no body (`dados.get("sql")`) e executa diretamente via `cursor.execute(query)` sem qualquer filtro ou autenticação.
Impact: Qualquer cliente HTTP consegue executar `DROP TABLE`, `SELECT * FROM usuarios` (com senhas em claro), ou qualquer DDL/DML. É equivalente a dar acesso direto ao banco para a internet.
Recommendation: Remover este endpoint completamente. Se necessário para debug local, proteger com autenticação + flag de ambiente que desabilita em produção.

### [CRITICAL-03] Unprotected Admin Endpoints (reset-db e query)
File: app.py:44-54,56-72
Description: Os endpoints `/admin/reset-db` e `/admin/query` não possuem nenhum middleware de autenticação ou autorização. Qualquer request HTTP anônimo pode resetar o banco inteiro ou executar SQL arbitrário.
Impact: Perda total de dados em produção com um único `curl -X POST /admin/reset-db`. Exfiltração completa do banco via `/admin/query`.
Recommendation: Remover endpoints destrutivos ou protegê-los com middleware de autenticação + verificação de role admin + flag de ambiente.

### [CRITICAL-04] Hardcoded Secret Key
File: app.py:8
Description: `SECRET_KEY` é definida como string literal (`"minha-chave-super-secreta-123"`) no código-fonte.
Impact: Qualquer pessoa com acesso ao repositório pode forjar sessões Flask, assinar cookies e fazer replay de tokens. A chave precisa ser rotacionada após qualquer leak do repo.
Recommendation: Mover para variável de ambiente (`os.environ.get("SECRET_KEY")`) lida em um módulo `config/settings.py`. Ver padrão 1 do playbook.

### [CRITICAL-05] Debug Mode Hardcoded em Produção
File: app.py:9,87
Description: `app.config["DEBUG"] = True` e `app.run(debug=True)` estão hardcoded. O debugger Werkzeug do Flask expõe um console interativo que permite **execução remota de código** em produção.
Impact: RCE (Remote Code Execution) via debugger pin. Stack traces completos expostos a qualquer cliente.
Recommendation: Ler `DEBUG` de variável de ambiente, default `False`. Nunca usar `debug=True` em produção.

### [CRITICAL-06] Senhas Armazenadas em Texto Puro (Sem Hash)
File: database.py:62-66, models.py:93-95,101-103
Description: Senhas dos usuários são armazenadas e comparadas como texto puro (`"admin123"`, `"123456"`, `"senha123"`). O login faz `WHERE senha = '<senha>'` — comparação direta sem hash.
Impact: Qualquer acesso ao banco (via SQL injection, backup vazado, ou o próprio `/admin/query`) expõe todas as senhas em claro. Violação de LGPD/GDPR.
Recommendation: Usar `bcrypt` ou `argon2` para hash com salt. Alterar `criar_usuario` para hashear e `login_usuario` para verificar com `bcrypt.checkpw()`. Ver padrão 3 do playbook.

### [CRITICAL-07] Sensitive Data Exposure — Senhas e Secrets em Responses
File: models.py:72-78 (get_todos_usuarios), models.py:82-90 (get_usuario_por_id), controllers.py:253-268 (health_check)
Description: `get_todos_usuarios` e `get_usuario_por_id` retornam o campo `senha` no JSON de resposta. O endpoint `/health` retorna `secret_key`, `db_path` e `debug` na response.
Impact: Qualquer chamada a `GET /usuarios` ou `GET /health` vaza senhas em claro e a secret key da aplicação.
Recommendation: Remover `senha` da serialização de usuários. Remover dados sensíveis do health check (manter apenas `status` e contagens).

---

### [HIGH-01] God Module — models.py
File: models.py:1-314
Description: Arquivo único de 314 linhas concentra 4 domínios (produtos, usuários, pedidos, relatório de vendas) misturando queries SQL, mapeamento de dados e regras de negócio (cálculo de desconto, verificação de estoque).
Impact: Impossível testar um domínio isoladamente. Qualquer mudança em produtos pode quebrar pedidos. Merge conflicts frequentes em equipe.
Recommendation: Separar em `models/produto_model.py`, `models/usuario_model.py`, `models/pedido_model.py`. Ver padrão 5 do playbook.

### [HIGH-02] God Module — controllers.py
File: controllers.py:1-292
Description: Arquivo único de 292 linhas com controllers de 4 domínios distintos (produtos, usuários, pedidos, relatório). Mesmo problema do models.py.
Impact: Acoplamento entre domínios, dificuldade de manutenção e testes.
Recommendation: Separar em `controllers/produto_controller.py`, `controllers/usuario_controller.py`, `controllers/pedido_controller.py`. Ver padrão 5 do playbook.

### [HIGH-03] Business Logic in Models (Fat Models)
File: models.py:108-145 (criar_pedido), models.py:199-228 (relatorio_vendas)
Description: `criar_pedido` verifica estoque, calcula total, baixa estoque e insere em múltiplas tabelas — tudo dentro do model. `relatorio_vendas` calcula faixas de desconto (regra de negócio) dentro do model.
Impact: Regras de negócio acopladas à camada de dados. Impossível reusar a lógica de desconto ou de criação de pedido fora do contexto SQL.
Recommendation: Extrair lógica de negócio para `services/pedido_service.py` e `services/relatorio_service.py`. Models devem fazer apenas CRUD.

### [HIGH-04] Global Mutable State — Conexão SQLite Singleton
File: database.py:4-5
Description: `db_connection = None` como variável global mutável, com `check_same_thread=False` no SQLite. A conexão é compartilhada entre todos os requests.
Impact: Race conditions em ambiente multi-thread (Werkzeug com threads). Dados de um request podem vazar para outro. Conexão corrompida afeta toda a aplicação.
Recommendation: Usar `flask.g` para conexão per-request ou connection pool. Fechar conexão no `teardown_appcontext`.

---

### [MEDIUM-01] N+1 Queries em Listagem de Pedidos
File: models.py:148-175 (get_pedidos_usuario), models.py:177-197 (get_todos_pedidos)
Description: Para cada pedido, faz uma query para buscar itens, e para cada item, faz outra query para buscar o nome do produto. 1 pedido com 3 itens = 7 queries. 100 pedidos com 3 itens cada = 401 queries.
Impact: Timeout e degradação severa de performance sob carga. Invisível em dev com poucos dados.
Recommendation: Usar JOIN único (`pedidos JOIN itens_pedido JOIN produtos`) retornando tudo em uma query. Ver padrão 10 do playbook.

### [MEDIUM-02] Missing Pagination / Unbounded Results
File: models.py:5 (get_todos_produtos), models.py:68 (get_todos_usuarios), models.py:177 (get_todos_pedidos), models.py:230 (buscar_produtos)
Description: Todas as listagens fazem `SELECT * FROM <tabela>` sem `LIMIT`. Nenhum endpoint aceita parâmetros de paginação.
Impact: Com milhares de registros, a resposta pode consumir toda a memória do servidor ou travar o cliente.
Recommendation: Adicionar parâmetros `page` e `per_page` com defaults razoáveis (ex: 20). Aplicar `LIMIT ? OFFSET ?` nas queries.

### [MEDIUM-03] Broad Exception Handlers com Stack-Trace Leakage
File: controllers.py:8,17,50,73,84,96,107,119,135,145,157,175,185,195,207,230,243,268
Description: Todos os controllers usam `except Exception as e: return jsonify({"erro": str(e)})`. Isso vaza mensagens internas de erro (stack traces, nomes de tabelas, paths do sistema) para o cliente.
Impact: Informações internas expostas facilitam ataques direcionados. Bugs silenciosos — erros inesperados são engolidos e retornados como 500 genérico.
Recommendation: Criar middleware de error handling centralizado. Logar o erro completo internamente, retornar mensagem genérica ao cliente. Ver padrão 12 do playbook.

### [MEDIUM-04] Duplicated Validation (criar_produto / atualizar_produto)
File: controllers.py:22-48 (criar_produto), controllers.py:55-72 (atualizar_produto)
Description: A validação de campos obrigatórios (`nome`, `preco`, `estoque`), limites de tamanho e categorias válidas é duplicada quase identicamente entre `criar_produto` e `atualizar_produto`.
Impact: Regras divergem quando uma é atualizada e a outra não. A lista `categorias_validas` está hardcoded inline em `criar_produto` mas ausente em `atualizar_produto`.
Recommendation: Extrair validação para função reutilizável (`validators/produto_validator.py` ou método no service). Ver padrão 11 do playbook.

### [MEDIUM-05] Side Effects in Controllers (Notificações Inline)
File: controllers.py:175-177 (criar_pedido), controllers.py:207-210 (atualizar_status_pedido)
Description: `criar_pedido` faz `print("ENVIANDO EMAIL...")`, `print("ENVIANDO SMS...")`, `print("ENVIANDO PUSH...")` inline no handler. `atualizar_status_pedido` faz o mesmo para notificações de status.
Impact: Quando notificações reais forem implementadas, estarão acopladas ao request HTTP, bloqueando a resposta. Impossível desabilitar notificações sem alterar o controller.
Recommendation: Extrair para `services/notificacao_service.py`. Em produção, usar fila assíncrona (Celery, RQ, etc.).

---

### [LOW-01] Print-Based Logging
File: controllers.py:8,50,84,100,135,157,175-177,207-210,253, app.py:53,80-83
Description: Todo o logging é feito via `print()` com strings ALL-CAPS (`"ERRO CRITICO"`, `"!!! BANCO DE DADOS RESETADO !!!"`, `"ENVIANDO EMAIL"`). Sem níveis, sem timestamps, sem contexto estruturado.
Impact: Impossível filtrar logs por severidade em produção. Sem integração com ferramentas de monitoramento.
Recommendation: Substituir por módulo `logging` do Python com configuração centralizada. Ver padrão 13 do playbook.

### [LOW-02] Magic Numbers / Magic Strings
File: models.py:211-216 (faixas de desconto: 10000, 5000, 1000, 0.1, 0.05, 0.02), controllers.py:44 (categorias_validas inline), controllers.py:204 (lista de status inline)
Description: Faixas de desconto são números literais sem nome. Listas de categorias e status válidos são strings inline repetidas em locais diferentes.
Impact: Difícil entender a intenção. Mudança de regra exige buscar todos os locais onde o valor aparece.
Recommendation: Extrair para constantes nomeadas em módulo de configuração ou no model correspondente.

### [LOW-03] Dead Import
File: models.py:2
Description: `import sqlite3` é importado mas nunca usado diretamente (toda interação com SQLite é via `get_db()` que retorna a conexão já configurada).
Impact: Ruído no código. Indica decaimento de cuidado.
Recommendation: Remover o import não utilizado.

================================
Total: 19 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
