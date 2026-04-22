================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript + Express
Files:   3 analyzed | ~180 lines of code
Date:    2026-04-21

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 3 | LOW: 3

## Findings

### [CRITICAL] Hardcoded Secrets / Credentials
File: src/utils.js:1-7
Description: Objeto `config` contém credenciais de banco (`dbUser`, `dbPass`), chave de gateway de pagamento (`pk_live_1234567890abcdef`) e credenciais SMTP como strings literais no código-fonte. Qualquer pessoa com acesso ao repositório tem as chaves de produção.
Impact: Comprometimento total de credenciais de banco, gateway de pagamento e email. Rotação exige redeploy e auditoria de uso indevido.
Recommendation: Mover para variáveis de ambiente lidas em `src/config/index.js` via `process.env`. Ver padrão 1 do playbook.

### [CRITICAL] Weak / Broken Cryptography
File: src/utils.js:14-18
Description: Função `badCrypto` gera "hash" de senha fazendo loop de 10.000 iterações de `Buffer.from(pwd).toString('base64').substring(0,2)` — é apenas Base64 repetido e truncado. Não é hash criptográfico, não tem salt, é trivialmente reversível.
Impact: Todas as senhas no banco são recuperáveis em texto puro por qualquer atacante com acesso ao banco. Rainbow tables nem são necessárias — basta reverter o Base64.
Recommendation: Substituir por `bcrypt` com salt automático e custo ≥ 10. Ver padrão 3 do playbook.

### [CRITICAL] Sensitive Data Exposure (Payment Card Logging)
File: src/AppManager.js:41
Description: `console.log` imprime o número do cartão de crédito (`cc`) e a chave do gateway de pagamento (`config.paymentGatewayKey`) em texto puro nos logs.
Impact: Violação de PCI-DSS. Qualquer pessoa com acesso aos logs obtém números de cartão e chave do gateway. Em ambiente cloud, logs são frequentemente indexados e persistidos.
Recommendation: Nunca logar dados de cartão. Mascarar com últimos 4 dígitos se necessário para debug. Remover chave do gateway dos logs.

### [CRITICAL] Unprotected Admin Endpoint
File: src/AppManager.js:68-107
Description: Rota `GET /api/admin/financial-report` retorna relatório financeiro completo (receita, alunos, valores pagos) sem qualquer middleware de autenticação ou autorização.
Impact: Qualquer cliente externo acessa dados financeiros sensíveis da plataforma. Exposição de receita, nomes e emails de alunos.
Recommendation: Adicionar middleware de autenticação + verificação de role admin antes do handler. Ver padrão 5 do playbook.

### [CRITICAL] Unprotected Destructive Endpoint (User Deletion)
File: src/AppManager.js:109-115
Description: Rota `DELETE /api/users/:id` apaga usuários sem autenticação, sem autorização e sem limpar dados relacionados (matrículas e pagamentos ficam órfãos — o próprio código admite isso no response).
Impact: Qualquer cliente pode apagar qualquer usuário. Dados órfãos corrompem relatórios e integridade referencial.
Recommendation: Adicionar auth middleware, verificar permissões, implementar soft-delete ou cascade com transaction.

### [HIGH] God Class (AppManager)
File: src/AppManager.js:1-141
Description: Classe `AppManager` concentra conexão com banco, DDL/schema, seed de dados, roteamento HTTP, lógica de checkout (pagamento + matrícula), relatório financeiro e deleção de usuários — tudo em um único arquivo de 141 linhas.
Impact: Impossível testar qualquer funcionalidade isoladamente. Qualquer mudança em uma rota arrisca quebrar todas as outras. Merge conflicts garantidos em equipe.
Recommendation: Separar em camadas: models (acesso a dados), controllers (orquestração), routes (roteamento). Ver padrão 5 do playbook.

### [HIGH] Business Logic in Route Handlers (Fat Controller)
File: src/AppManager.js:30-66
Description: O handler de `POST /api/checkout` contém toda a lógica de negócio inline: busca de curso, busca/criação de usuário, decisão de pagamento, criação de matrícula, registro de pagamento e audit log — tudo dentro de callbacks aninhados no route handler.
Impact: Lógica de checkout não é reutilizável (CLI, worker, teste unitário). Impossível testar regra de pagamento sem subir HTTP.
Recommendation: Extrair para `controllers/checkoutController.js` e `services/paymentService.js`. Ver padrão 6 do playbook.

### [HIGH] Missing Transactions in Multi-Step Checkout
File: src/AppManager.js:47-63
Description: O fluxo de checkout executa 3 INSERTs sequenciais (enrollment → payment → audit_log) sem transaction. Se o INSERT de payment falha, a matrícula já foi criada sem pagamento correspondente.
Impact: Dados inconsistentes no banco: matrículas sem pagamento, pagamentos sem audit log. Impossível reconciliar financeiramente.
Recommendation: Envolver os INSERTs em `db.run("BEGIN")` / `db.run("COMMIT")` com rollback em caso de erro, ou migrar para driver com suporte a promises + transactions.

### [HIGH] Global Mutable State
File: src/utils.js:9-10
Description: `globalCache` (objeto mutável) e `totalRevenue` (contador numérico) são variáveis de módulo exportadas e mutadas por handlers. Em ambiente com múltiplos requests concorrentes, o estado vaza entre requests.
Impact: Race conditions, dados de um usuário vazando para outro, testes flaky, memory leak no cache sem bound.
Recommendation: Eliminar estado global. Se cache for necessário, usar Redis ou LRU com TTL. Receita total deve ser calculada via query, não acumulador global.

### [MEDIUM] N+1 Queries in Financial Report
File: src/AppManager.js:75-103
Description: Para cada curso, faz query de enrollments; para cada enrollment, faz query de user + query de payment. Com C cursos, E matrículas: 1 + C + 2E queries.
Impact: Com 100 cursos e 1000 matrículas, são ~2101 queries para um único request de relatório. Timeout garantido em produção.
Recommendation: Substituir por JOIN único: `SELECT courses.title, users.name, payments.amount, payments.status FROM courses JOIN enrollments ... JOIN users ... JOIN payments ...`. Ver padrão 10 do playbook.

### [MEDIUM] Weak Input Validation (Payment Logic)
File: src/AppManager.js:43
Description: Decisão de aprovar/negar pagamento é baseada em `cc.startsWith("4")` — se o número do cartão começa com "4", aprova; senão, nega. Não há integração real com gateway, não há validação de formato do cartão.
Impact: Qualquer string começando com "4" é tratada como pagamento válido. Sem validação de Luhn, sem verificação de expiração, sem CVV.
Recommendation: Integrar com gateway de pagamento real ou, no mínimo, extrair para um service com interface clara que possa ser substituída. Validar formato do cartão.

### [MEDIUM] Missing Pagination on Financial Report
File: src/AppManager.js:72-73
Description: `SELECT * FROM courses` e queries subsequentes carregam todos os registros sem LIMIT. O endpoint retorna o dataset inteiro em uma única resposta.
Impact: Com crescimento de dados, o endpoint se torna progressivamente mais lento e pode causar OOM no servidor.
Recommendation: Adicionar parâmetros `page`/`limit` com defaults razoáveis. Ver padrão 12 do playbook.

### [LOW] Deprecated API: sqlite3 Callback Style
File: src/AppManager.js:1-141
Description: Todo o acesso ao banco usa a API de callbacks do `sqlite3` (`db.get(sql, cb)`, `db.all(sql, cb)`, `db.run(sql, cb)`). Esta API é legada e leva ao callback hell observado no código.
Impact: Código difícil de ler, manter e compor. Erros facilmente engolidos em callbacks aninhados.
Recommendation: Migrar para `better-sqlite3` (síncrono, mais simples) ou wrapper `sqlite` com promises/async-await. Ver padrão 14 do playbook.

### [LOW] Print-Based Logging
File: src/AppManager.js:41, src/utils.js:12, src/app.js:12
Description: Uso de `console.log` para logging de operações (checkout, cache, boot). Sem níveis (info/warn/error), sem contexto estruturado, sem destino configurável.
Impact: Impossível filtrar logs por severidade em produção. Logs de cartão de crédito misturados com logs de boot.
Recommendation: Substituir por logger estruturado como `pino` ou `winston` com níveis e formatação JSON.

### [LOW] Inconsistent Naming and Response Format
File: src/AppManager.js:30-115
Description: Respostas misturam formatos: `res.send("string")` vs `res.json({...})`. Variáveis usam abreviações inconsistentes (`u`, `e`, `p`, `cid`, `cc` vs `userId`, `course`, `courseData`). Mensagens em português e inglês misturadas.
Impact: API imprevisível para consumidores. Código difícil de ler devido a nomes crípticos.
Recommendation: Padronizar respostas como JSON com shape consistente `{ success, data, error }`. Usar nomes descritivos para variáveis.

================================
Total: 15 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
