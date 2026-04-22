# ecommerce-api-legacy

LMS API (com fluxo de checkout) em Node.js/Express usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
npm install
npm start
```

A aplicação sobe em `http://localhost:3000`. O banco SQLite é em memória e já carrega seeds automaticamente no boot.

Exemplos de requisições estão em `api.http`.

## New Project Structure

```
src/
├── app.js                          # Composition root (wiring only)
├── config/
│   └── index.js                    # Config via env vars (no hardcoded secrets)
├── controllers/
│   ├── checkoutController.js       # Checkout orchestration
│   ├── reportController.js         # Financial report orchestration
│   └── userController.js           # User management
├── middlewares/
│   └── errorHandler.js             # Central error handling (no stack leaks)
├── models/
│   ├── db.js                       # DB init + schema + seeds (better-sqlite3)
│   ├── auditLogModel.js            # Audit log persistence
│   ├── courseModel.js               # Course queries
│   ├── enrollmentModel.js           # Enrollment queries
│   ├── paymentModel.js              # Payment queries
│   └── userModel.js                 # User queries (with cascade delete)
├── routes/
│   └── index.js                    # Route definitions (thin layer)
└── services/
    ├── paymentService.js            # Checkout logic + transaction
    └── reportService.js             # Financial report (single JOIN)
```

## Validation

- Application boots without errors
- `POST /api/checkout` (valid card) → 200 + enrollment_id
- `POST /api/checkout` (denied card) → 400 + error message
- `POST /api/checkout` (missing fields) → 400 + Bad Request
- `GET /api/admin/financial-report` → 200 + correct report data
- `DELETE /api/users/:id` → 200 + cascade cleanup

## Findings Addressed

| Severidade | Finding | Solução |
|---|---|---|
| CRITICAL | Hardcoded secrets | Config via `process.env` (`src/config/index.js`) |
| CRITICAL | Weak crypto (Base64 loop) | `bcryptjs` com salt rounds 10 |
| CRITICAL | Card/key logging | Removido — nenhum dado sensível nos logs |
| HIGH | God Class (`AppManager`) | Separado em 14 arquivos across 6 camadas |
| HIGH | Fat controller (checkout inline) | Lógica extraída para `services/paymentService.js` |
| HIGH | Missing transactions | Checkout wrapped em `db.transaction()` |
| HIGH | Global mutable state | `globalCache` e `totalRevenue` eliminados |
| MEDIUM | N+1 queries (financial report) | Single JOIN em `services/reportService.js` |
| LOW | Deprecated sqlite3 callbacks | Migrado para `better-sqlite3` (sync) |
| LOW | Print logging | Error handler central, sem stack leaks ao client |
| LOW | Inconsistent responses | JSON everywhere com shape consistente |

## Not Addressed (by design)

| Severidade | Finding | Motivo |
|---|---|---|
| CRITICAL | Unprotected admin endpoint | Requer sistema de auth (JWT/session) não presente no projeto original |
| CRITICAL | Unprotected delete endpoint | Mesmo: necessita auth middleware |
| MEDIUM | Weak input validation | Simulação de pagamento mantida como placeholder para gateway real; extraída para service |
| MEDIUM | Missing pagination | Baixo esforço mas altera o contrato de resposta da API |
