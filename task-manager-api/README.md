# task-manager-api

API REST de gerenciamento de tarefas em Python/Flask, refatorada para arquitetura MVC limpa pelo desafio `refactor-arch`.

## Como rodar

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # edite as variáveis conforme necessário
python seed.py              # popula o banco com dados de exemplo
python app.py               # sobe em http://localhost:5000
```

> O `seed.py` popula o banco SQLite (`tasks.db`) com usuários, categorias e tasks de exemplo — **rode-o antes do primeiro boot**, caso contrário os endpoints vão retornar listas vazias.

## Variáveis de ambiente

| Variável | Descrição | Default |
|---|---|---|
| `SECRET_KEY` | Chave secreta do Flask | `dev-secret-key-change-in-production` |
| `DATABASE_URI` | URI do banco de dados | `sqlite:///tasks.db` |
| `DEBUG` | Modo debug | `false` |
| `SMTP_HOST` | Host do servidor SMTP | `smtp.gmail.com` |
| `SMTP_PORT` | Porta SMTP | `587` |
| `SMTP_USER` | Usuário SMTP | (vazio) |
| `SMTP_PASSWORD` | Senha SMTP | (vazio) |

## Estrutura do projeto

```
├── .env.example                  # Template para variáveis de ambiente
├── app.py                        # Composition root — apenas wiring
├── database.py                   # Instância do SQLAlchemy
├── requirements.txt
├── seed.py
├── config/
│   └── settings.py               # Configuração lida de env vars
├── controllers/                  # Camada de lógica de negócio
│   ├── task_controller.py
│   ├── user_controller.py
│   ├── category_controller.py
│   └── report_controller.py
├── middlewares/                   # Cross-cutting concerns
│   └── error_handler.py
├── models/                       # Dados e acesso a storage
│   ├── task.py
│   ├── user.py
│   └── category.py
├── routes/                       # Roteamento fino (delegação para controllers)
│   ├── task_routes.py
│   ├── user_routes.py
│   ├── report_routes.py
│   └── category_routes.py
├── services/
│   └── notification_service.py
├── utils/
│   └── helpers.py
└── reports/
    └── audit-task-manager.md     # Relatório de auditoria arquitetural
```

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Info da API |
| GET | `/health` | Health check |
| GET | `/tasks` | Listar todas as tasks |
| GET | `/tasks/<id>` | Detalhe de uma task |
| POST | `/tasks` | Criar task |
| PUT | `/tasks/<id>` | Atualizar task |
| DELETE | `/tasks/<id>` | Deletar task |
| GET | `/tasks/search?q=&status=&priority=&user_id=` | Buscar tasks |
| GET | `/tasks/stats` | Estatísticas de tasks |
| GET | `/users` | Listar usuários |
| GET | `/users/<id>` | Detalhe de um usuário |
| POST | `/users` | Criar usuário |
| PUT | `/users/<id>` | Atualizar usuário |
| DELETE | `/users/<id>` | Deletar usuário |
| GET | `/users/<id>/tasks` | Tasks de um usuário |
| POST | `/login` | Autenticação |
| GET | `/categories` | Listar categorias |
| POST | `/categories` | Criar categoria |
| PUT | `/categories/<id>` | Atualizar categoria |
| DELETE | `/categories/<id>` | Deletar categoria |
| GET | `/reports/summary` | Relatório geral |
| GET | `/reports/user/<id>` | Relatório por usuário |

## Refatoração realizada

O projeto passou por auditoria arquitetural e refatoração MVC. Detalhes completos em [`reports/audit-task-manager.md`](reports/audit-task-manager.md).

### Anti-patterns corrigidos (21 de 26)

- **Segurança:** MD5 → werkzeug pbkdf2:sha256, SECRET_KEY e credenciais SMTP movidas para env vars, senha removida das respostas da API, SQL injection via LIKE corrigido
- **Arquitetura:** lógica de negócio extraída das routes para controllers, serialização centralizada nos models, lógica de overdue centralizada em `Task.is_overdue()`
- **Performance:** N+1 queries eliminadas com `joinedload` e `dynamic` relationships
- **Qualidade:** bare `except` substituídos por `except Exception`, `print()` substituído por `logging`, imports mortos removidos, `type()` → `isinstance()`, `datetime.utcnow()` → `datetime.now(timezone.utc)`
- **Organização:** rotas de Category extraídas para arquivo próprio, config centralizada, error handler middleware adicionado, cascade delete configurado no relationship

### Pendências (decisões arquiteturais)

| Finding | Descrição | Motivo |
|---|---|---|
| F-05 | Token JWT fake | Requer escolha de lib (PyJWT / flask-jwt-extended) |
| F-07 | Sem middleware de autenticação | Requer definição de estratégia de auth |
| F-20 | Sem paginação | Feature aditiva, baixo risco |
| F-22 | Marshmallow não utilizado | Feature aditiva, não bloqueante |
| F-26 | Notificações em memória | Decisão de design sobre persistência |
