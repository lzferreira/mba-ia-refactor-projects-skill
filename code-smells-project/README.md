# code-smells-project

API de E-commerce em Python/Flask usada como entrada do desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

A aplicação sobe em `http://localhost:5001`. O banco SQLite (`loja.db`) é criado automaticamente no primeiro boot, já com produtos e usuários de exemplo.

Variáveis de ambiente opcionais (veja `.env.example`):

| Variável     | Default                      | Descrição                |
|--------------|------------------------------|--------------------------|
| SECRET_KEY   | change-me-in-production      | Chave para sessões Flask |
| DEBUG        | false                        | Ativa modo debug         |
| DB_PATH      | loja.db                      | Caminho do banco SQLite  |
| HOST         | 0.0.0.0                      | Host do servidor         |
| PORT         | 5001                         | Porta do servidor        |

## Project Structure

```
.
├── config/
│   ├── settings.py            # Configuração via env vars (zero secrets hardcoded)
│   ├── database.py            # Conexão per-request via flask.g, seed com bcrypt
│   └── logger.py              # Logging estruturado em JSON
├── models/
│   ├── produto_model.py       # CRUD produtos — queries parametrizadas
│   ├── usuario_model.py       # CRUD usuarios — bcrypt hash, sem senha na serialização
│   └── pedido_model.py        # CRUD pedidos — JOIN único (sem N+1)
├── controllers/
│   ├── produto_controller.py  # Orquestração de produtos
│   ├── usuario_controller.py  # Orquestração de usuarios + login
│   ├── pedido_controller.py   # Orquestração de pedidos
│   ├── relatorio_controller.py
│   └── health_controller.py   # Sem dados sensíveis expostos
├── routes/
│   └── api_routes.py          # Blueprint com todas as rotas
├── services/
│   ├── pedido_service.py      # Lógica de criação de pedido com transação
│   └── relatorio_service.py   # Cálculo de desconto extraído do model
├── validators/
│   └── produto_validator.py   # Validação centralizada (criar + atualizar)
├── middlewares/
│   └── errors.py              # Error handler centralizado (404, 405, AppError, 500)
├── app.py                     # Composition root (~20 linhas)
├── requirements.txt
├── .env.example
└── reports/
    └── audit-code-smells-project.md
```

## Validation

- ✓ Application boots without errors
- ✓ All 11 endpoints respond correctly:
  - `GET /` — index
  - `GET /health` — health check
  - `GET /produtos` — listar produtos
  - `GET /produtos/<id>` — buscar produto
  - `GET /produtos/busca` — buscar por termo/categoria/preço
  - `POST /produtos` — criar produto
  - `PUT /produtos/<id>` — atualizar produto
  - `DELETE /produtos/<id>` — deletar produto
  - `GET /usuarios` — listar usuarios
  - `GET /usuarios/<id>` — buscar usuario
  - `POST /usuarios` — criar usuario
  - `POST /login` — autenticação
  - `POST /pedidos` — criar pedido
  - `GET /pedidos` — listar todos os pedidos
  - `GET /pedidos/usuario/<id>` — listar pedidos de um usuario
  - `PUT /pedidos/<id>/status` — atualizar status do pedido
  - `GET /relatorios/vendas` — relatório de vendas
- ✓ 17 de 19 anti-patterns eliminados, 2 restantes (LOW — aceitáveis para o escopo)

## Changes to External Contract

As seguintes mudanças foram feitas intencionalmente no contrato da API:

| Mudança | Motivo |
|---------|--------|
| Campo `senha` removido das respostas de `GET /usuarios` e `GET /usuarios/<id>` | Era vazamento de dados sensíveis (CRITICAL-07) |
| Campos `secret_key`, `db_path`, `debug`, `ambiente` removidos de `GET /health` | Exposição de configuração interna (CRITICAL-07) |
| Endpoints `POST /admin/reset-db` e `POST /admin/query` removidos | Vulnerabilidades críticas sem autenticação (CRITICAL-02, CRITICAL-03) |
| Senhas armazenadas com bcrypt hash | Antes estavam em texto puro (CRITICAL-06). Banco antigo incompatível — recriado com seed |
| Porta padrão alterada de 5000 para 5001 | Configurável via env var `PORT` |
