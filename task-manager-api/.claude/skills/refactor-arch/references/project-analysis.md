# Project Analysis — Heurísticos de Detecção

Este arquivo fornece os sinais que a Fase 1 usa para detectar **linguagem, framework, storage e arquitetura atual** em qualquer projeto — sem depender de conhecimento prévio da stack.

A regra geral: comece pelo manifesto de dependências. Ele é o documento mais confiável do projeto porque foi declarado pelo dev. Depois confirme com imports reais.

## Sumário

- [Detecção de linguagem](#detecção-de-linguagem)
- [Detecção de framework web](#detecção-de-framework-web)
- [Detecção de storage / banco de dados](#detecção-de-storage--banco-de-dados)
- [Mapeamento de arquitetura atual](#mapeamento-de-arquitetura-atual)
- [Inferência de domínio](#inferência-de-domínio)
- [Detecção do comando de boot](#detecção-do-comando-de-boot)

---

## Detecção de linguagem

Procure por manifesto + extensões dominantes:

| Manifesto | Linguagem | Extensões típicas |
|---|---|---|
| `package.json` | JavaScript / TypeScript | `.js` `.mjs` `.cjs` `.ts` `.tsx` |
| `requirements.txt`, `pyproject.toml`, `Pipfile`, `setup.py` | Python | `.py` |
| `Gemfile`, `*.gemspec` | Ruby | `.rb` `.erb` |
| `go.mod` | Go | `.go` |
| `pom.xml`, `build.gradle(.kts)` | Java / Kotlin | `.java` `.kt` |
| `Cargo.toml` | Rust | `.rs` |
| `composer.json` | PHP | `.php` |
| `*.csproj`, `*.sln` | C# | `.cs` |
| `mix.exs` | Elixir | `.ex` `.exs` |

Para TypeScript vs JavaScript, verifique `tsconfig.json` e a presença de `typescript` nas devDependencies.

Para a **versão da linguagem**, procure em:
- `.python-version`, `.nvmrc`, `.ruby-version`, `.tool-versions`
- campos como `engines` em package.json, `python_requires` em setup.py, `go` em go.mod.

## Detecção de framework web

O framework é geralmente **a dependência mais óbvia** no manifesto. Imports no entry point confirmam.

### Node.js / TypeScript

| Dep no package.json | Framework |
|---|---|
| `express` | Express |
| `fastify` | Fastify |
| `koa` | Koa |
| `@nestjs/core` | NestJS |
| `next` | Next.js (full-stack) |
| `hapi` / `@hapi/hapi` | Hapi |

### Python

| Dep | Framework |
|---|---|
| `flask` | Flask |
| `django` | Django |
| `fastapi` | FastAPI |
| `starlette` | Starlette |
| `pyramid` | Pyramid |
| `tornado` | Tornado |
| `bottle` | Bottle |

### Ruby, Go, Java, PHP, C#

| Linguagem | Dependência / sinal | Framework |
|---|---|---|
| Ruby | `rails`, gem `rails` em Gemfile | Rails |
| Ruby | `sinatra` | Sinatra |
| Go | `github.com/gin-gonic/gin` | Gin |
| Go | `github.com/labstack/echo` | Echo |
| Go | `github.com/gofiber/fiber` | Fiber |
| Go | apenas `net/http` no stdlib | Biblioteca padrão |
| Java | `spring-boot-starter-web` | Spring Boot |
| PHP | `laravel/framework` | Laravel |
| PHP | `symfony/symfony` | Symfony |
| C# | `Microsoft.AspNetCore.*` | ASP.NET Core |

**Entry point típico por stack** (bom para confirmar o framework):

- Node: `app.js`, `server.js`, `index.js`, `src/main.ts`, `src/app.ts`
- Python: `app.py`, `main.py`, `wsgi.py`, `asgi.py`, `manage.py`
- Ruby: `config.ru`, `config/application.rb`
- Go: `main.go`, `cmd/<name>/main.go`
- Java: classe anotada com `@SpringBootApplication`
- PHP: `public/index.php`, `artisan`
- C#: `Program.cs`

## Detecção de storage / banco de dados

### Drivers comuns no manifesto

| Stack | Dependência | Storage |
|---|---|---|
| Node | `pg`, `postgres` | PostgreSQL |
| Node | `mysql2`, `mysql` | MySQL |
| Node | `sqlite3`, `better-sqlite3` | SQLite |
| Node | `mongodb`, `mongoose` | MongoDB |
| Node | `redis`, `ioredis` | Redis |
| Python | `psycopg2`, `psycopg` | PostgreSQL |
| Python | `pymysql`, `mysqlclient` | MySQL |
| Python | stdlib `sqlite3` (sem dep declarada) | SQLite |
| Python | `pymongo`, `motor` | MongoDB |
| Python | `sqlalchemy`, `flask-sqlalchemy` | ORM (agnóstico) |
| Ruby | `pg`, `mysql2`, `sqlite3` gems | idem |
| Go | `lib/pq`, `jackc/pgx` | PostgreSQL |
| Go | `go-sql-driver/mysql` | MySQL |

### Confirmar no código

Mesmo sem manifesto claro, procure por:

- **Connection strings**: `postgres://`, `mysql://`, `mongodb://`, caminho `.db` ou `.sqlite`.
- **Arquivos de schema**: `schema.sql`, `*.sql`, `migrations/`, `db/migrate/`, `prisma/schema.prisma`, classes com `class Meta: db_table`, decorators `@Entity`.
- **Chamadas de conexão**: `sqlite3.connect(...)`, `createConnection(...)`, `connectDB(...)`, `new Sequelize(...)`, `db.Open(...)`.

Liste as **tabelas/coleções detectadas** no resumo da Fase 1 (ex: `produtos, usuarios, pedidos`). Isso ancora a Fase 2 e deixa o usuário validar rapidamente.

## Mapeamento de arquitetura atual

Classifique o projeto em uma das três categorias:

### Monolítico (≤ 5 arquivos-fonte no topo)

Sinais:
- Poucos arquivos grandes no diretório raiz (200+ linhas cada).
- Nenhuma pasta `models/`, `routes/`, `controllers/`, `services/`.
- Um arquivo que contém rotas, acesso a banco e lógica de negócio simultaneamente.

### Camadas parciais

Sinais:
- Existem pastas `models/`, `routes/`, `controllers/`, `services/`, `utils/` — mas com responsabilidades trocadas (ex: queries dentro de routes, lógica de negócio dentro de models).
- Ausência de camada de configuração (secrets hardcoded).
- Falta error-handling central (try/except pulverizado).

### Estruturado

Sinais:
- Camadas bem separadas com responsabilidades consistentes.
- Config isolada, error middleware central, DI ou composition root claro.
- Se o projeto já está aqui, a skill provavelmente tem pouco a fazer além de ajustes pontuais.

### Como medir rapidamente

1. `ls` no diretório raiz e nas pastas `src/` / `app/`.
2. Conte arquivos-fonte: `find . -name '*.<ext>' | wc -l` (ignorando `node_modules`, `venv`, `.git`).
3. Abra o entry point e os 2–3 arquivos maiores. Eles dizem muito: se eles concentram rota + SQL + regra de negócio, é monolito.

## Inferência de domínio

O domínio é uma **frase de 1 linha** descrevendo o que a aplicação faz. Extraia de:

1. **Nomes de tabelas/modelos**: `produtos + pedidos + usuarios` → "E-commerce / marketplace API". `courses + enrollments + payments` → "LMS / plataforma de cursos". `tasks + users + categories` → "task manager / productivity".
2. **Nomes de rotas**: `/checkout`, `/cart`, `/enrollments`, `/tasks/<id>/complete` — revelam o fluxo principal.
3. **README ou comentários** do projeto, se existirem (sem assumir que são verdade — código é a fonte).

Seja específico mas sucinto. "API REST" não é descrição de domínio; "API REST de e-commerce com catálogo de produtos e pedidos" é.

## Detecção do comando de boot

Necessário para validar a Fase 3. Procure em:

- Node: script `start` em `package.json`, ou `node <entry>`.
- Python/Flask: `flask run` se `FLASK_APP` está definido, ou `python app.py`.
- Python/Django: `python manage.py runserver`.
- Python/FastAPI: `uvicorn <module>:app`.
- Ruby/Rails: `rails server` ou `bin/rails s`.
- Go: `go run .` ou `go run ./cmd/<name>`.
- Java/Spring: `./mvnw spring-boot:run` ou `./gradlew bootRun`.
- PHP/Laravel: `php artisan serve`.
- Genérico: README, `Makefile`, `Procfile`, `docker-compose.yml` — todos costumam listar o comando.

Se não houver indicação clara, pergunte ao usuário.
