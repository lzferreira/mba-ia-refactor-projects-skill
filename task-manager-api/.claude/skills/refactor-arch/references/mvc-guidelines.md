# MVC Guidelines — Alvo Arquitetural

Este arquivo define o **alvo** da Fase 3: a forma que o projeto deve ter ao final da refatoração. O objetivo não é dogma — é aplicar separação de responsabilidades para que cada mudança futura custe menos.

## Princípio único

Cada camada tem **uma razão para mudar**. Se você consegue imaginar dois tipos de mudança (ex: "mudei a regra de desconto" e "mudei o banco de Postgres para MongoDB") afetando o mesmo arquivo, a separação está errada.

## Estrutura-alvo

A estrutura é adaptada à convenção da linguagem, mas as camadas são as mesmas. Exemplos:

**Python/Flask, FastAPI, Django-lite:**
```
src/ (ou pacote raiz)
├── config/
│   └── settings.py
├── models/
│   └── <dominio>_model.py
├── views/ (ou routes/)
│   └── <dominio>_routes.py
├── controllers/
│   └── <dominio>_controller.py
├── services/           # opcional
│   └── <regra>_service.py
├── middlewares/
│   └── error_handler.py
└── app.py              # composition root
```

**Node.js/Express, NestJS-lite:**
```
src/
├── config/
│   └── index.js
├── models/
│   └── <domain>.model.js
├── routes/ (ou views/)
│   └── <domain>.routes.js
├── controllers/
│   └── <domain>.controller.js
├── services/
│   └── <rule>.service.js
├── middlewares/
│   └── errorHandler.js
└── app.js              # composition root
```

**Go/Gin:**
```
.
├── config/
├── internal/
│   ├── models/
│   ├── handlers/       # equiv. a routes + controllers
│   ├── services/
│   └── middleware/
└── cmd/<name>/main.go  # composition root
```

**Ruby/Rails já segue esse padrão** (`app/models`, `app/controllers`, `app/views`, `config/`). Não reinvente — complete o que falta.

## Responsabilidades de cada camada

### config/

**Única responsabilidade:** carregar configuração de fora do código (env vars, arquivos de config externos) e expor para o resto da aplicação via objeto/struct/módulo imutável.

**Pertence aqui:**
- Leitura de `os.environ`, `process.env`, `os.Getenv`, `System.getenv`.
- Defaults seguros (não secrets — só valores inofensivos como porta, nível de log).
- Validação de que variáveis obrigatórias foram fornecidas (falhar rápido no boot).

**Não pertence:**
- Secrets literais no código.
- Lógica de negócio condicional em cima de config (isso pode ir no composition root, mas não aqui).

### models/

**Única responsabilidade:** representar dados e persistência. Um model sabe se mapear para/de linhas de banco e nada mais.

**Pertence aqui:**
- Definição do schema / classe de entidade.
- Queries de acesso (`find_by_id`, `list_active`) — parametrizadas.
- Serializadores que produzem uma representação segura (ex: `to_dict()` sem campos sensíveis).

**Não pertence:**
- Regras de negócio ("se estoque < 10, marcar como low stock" — isso é service).
- I/O externo (email, SMS, webhooks).
- Decisões de HTTP (status codes, redirects).

**Regra prática:** se você consegue testar o model com um banco SQLite em memória e sem subir HTTP, a fronteira está certa.

### views/ (ou routes/)

**Única responsabilidade:** mapear HTTP para chamadas do controller e voltar.

**Pertence aqui:**
- Definição de rotas (`app.get('/users/:id', ...)`, `@app.route('/users/<id>')`, etc.).
- Desserialização do request (extrair params, body, headers) e passagem para o controller.
- Serialização da resposta (JSON, status code, headers) a partir do que o controller retornou.
- Middleware de autenticação aplicada à rota (se o framework usa esse estilo).

**Não pertence:**
- `if user.role != 'admin'` (isso é checagem de autorização — middleware ou controller).
- Queries ao banco diretamente.
- Regras de negócio.

**Teste de sanidade:** a camada de routes deve ser "burra". Se você removesse todos os handlers e chamasse os controllers de outro transport (CLI, worker de fila), o comportamento da aplicação deveria ser o mesmo.

### controllers/

**Única responsabilidade:** orquestrar o fluxo de uma ação: receber input já desserializado, chamar os models/services na ordem correta, lidar com erros previsíveis, retornar a representação do resultado.

**Pertence aqui:**
- Coordenação ("busca user → checa permissão → chama service de checkout → persiste no model → retorna").
- Tratamento de casos de negócio ("se user não existe, retornar 404").
- Chamadas a services para regras complexas.

**Não pertence:**
- SQL direto (vai pelo model).
- Detalhes HTTP além de status code e shape do response (headers, parsing de body — isso é da view).
- Regra de negócio complexa reutilizada em vários lugares (extraia para service).

**Tamanho saudável:** um controller handler típico tem 5–30 linhas. Se está passando de 50, considere se há regra de negócio que deveria estar em service.

### services/ (opcional mas recomendado)

**Quando criar:** sempre que a mesma regra de negócio aparece em dois ou mais controllers, ou quando a regra é complexa o bastante para merecer testes isolados.

**Pertence aqui:**
- Regras de domínio puras ("calcular desconto escalonado", "validar transição de status de pedido", "gerar relatório de produtividade").
- Orquestração entre múltiplos models quando faz sentido ("criar pedido + baixar estoque + registrar pagamento" como uma unidade transacional).

**Não pertence:**
- Conhecimento de HTTP.
- Leitura de config (receba por injeção de dependência).

**Dica:** se você já tem o model e o controller enxutos, talvez não precise de service. Não crie services só para satisfazer uma sigla.

### middlewares/

**Única responsabilidade:** cross-cutting concerns — coisas que se aplicam transversalmente a muitas rotas.

**Exemplos típicos:**
- `error_handler` — captura exceções não tratadas, loga, e devolve uma resposta JSON padrão sem vazar stack trace.
- `auth` — valida token, popula `request.user`, rejeita se inválido.
- `request_logger` — loga cada request (método, path, status, duração).
- `rate_limit` — limita requests por IP/user.

### Entry point (composition root)

**Única responsabilidade:** instanciar dependências e conectar as camadas. É o único lugar que sabe sobre todas elas.

**Pertence aqui:**
- Criar a app do framework.
- Carregar config.
- Criar conexão com banco.
- Registrar middlewares.
- Registrar blueprints/routers/routes.
- Iniciar o servidor (ou expor um `app` para o servidor ASGI/WSGI).

**Não pertence:**
- Handler de rota direto.
- Regra de negócio.
- Definição de modelo.

Idealmente é curto (20–60 linhas).

## Dependências entre camadas

Direção permitida do acoplamento (quem pode importar quem):

```
views/routes  →  controllers  →  services  →  models
       ↓              ↓            ↓
                 middlewares, config (usados via injeção)
```

**Regra:** camadas "de cima" conhecem as de baixo, nunca o contrário. Um `model` nunca importa de `controllers` ou `routes`. Um `service` não importa de `controllers`. Se isso acontece, a seta está no sentido errado — há um nome perdido esperando ser extraído.

## Estado e injeção de dependência

Evite:
- Conexão de banco como singleton mutável de módulo.
- `import db` em todo lugar.
- Variáveis globais compartilhadas entre requests.

Prefira:
- Criar a conexão no composition root e passá-la para onde ela é necessária (Flask: application factory + context; Express: middleware que injeta no `req`; Go: structs com campos de dependência).
- Funções de service que recebem o repositório/DB como argumento em vez de importá-lo.

Esse modelo torna testes triviais — passe um fake DB e pronto.

## Error handling

Centralize em um middleware. Padrão:

1. Exceções esperadas (ex: `NotFound`, `Unauthorized`, `ValidationError`) são classes próprias que o middleware traduz para HTTP apropriado.
2. Exceções inesperadas são logadas com stack trace completo no servidor e viram `500 Internal Server Error` com mensagem genérica no cliente — **nunca** `str(e)` no body.
3. Controllers fazem `raise NotFound(...)` em vez de `return {"error": "..."}`. Isso mantém o controller focado no caminho feliz.

## Logging

Use logger estruturado (não `print`). Configure no composition root:

- Nível padrão (INFO em prod, DEBUG em dev — vindo de config).
- Formato consistente (JSON em prod para agregadores).
- Campos contextuais: request_id, user_id quando disponível.

Logs em camadas:
- `models/` e `services/` logam eventos de domínio significativos, não debug ruidoso.
- `middlewares/` logam um resumo por request.
- `controllers/` geralmente não precisam logar — se precisam, provavelmente tem regra demais ali.

## Critérios de "bom o bastante"

Não persiga perfeição arquitetural — persiga correção. O projeto está OK quando:

1. Um dev novo consegue abrir `app.py`/`server.js` e entender onde cada coisa mora em < 5 minutos.
2. Adicionar um novo endpoint exige tocar em, no máximo, 3 arquivos (route + controller + model, ou variação).
3. Trocar o banco exige tocar em models e config — nada mais.
4. Não há secrets no código.
5. Erros inesperados não vazam stack trace no cliente.
6. A suite de testes (se existir) roda sem subir servidor HTTP real.

Se todos esses itens estão verdes, a refatoração fez o que precisava fazer.
