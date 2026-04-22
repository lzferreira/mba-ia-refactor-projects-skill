# Audit Report Template

Formato obrigatório do relatório gerado pela Fase 2. O objetivo é que qualquer revisor leia o resultado em 5 minutos, entenda a magnitude do problema e consiga ir direto ao código referenciado.

## Arquivo de saída

Grave o relatório em `reports/audit-<project-slug>.md` na raiz do projeto-alvo, onde `<project-slug>` é o nome do diretório (ex: `audit-project-1.md`, `audit-my-api.md`). Crie a pasta `reports/` se não existir.

Imprima também o mesmo conteúdo no chat durante a fase, para o usuário revisar em linha.

## Template (siga exatamente)

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do projeto>
Stack:   <linguagem> + <framework>
Files:   <N> analyzed | ~<LOC> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Título curto>
File: <path>:<linha ou intervalo>
Description: <O que o código faz e por que é um problema, em 1–3 linhas.>
Impact: <O dano concreto — não "é ruim", mas "permite a qualquer cliente apagar o banco".>
Recommendation: <A transformação sugerida — referencie o padrão do playbook se aplicável.>

### [CRITICAL] <próximo finding>
...

### [HIGH] <finding>
...

### [MEDIUM] <finding>
...

### [LOW] <finding>
...

================================
Total: <N> findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Regras de preenchimento

### Ordenação

Agrupe por severidade, CRITICAL primeiro, LOW por último. Dentro de cada severidade, ordene por impacto percebido (o pior primeiro) — não é preciso ser matematicamente rigoroso, use bom senso.

### File:linha

Sempre arquivo + linha(s). Formatos aceitos:
- Linha única: `src/app.py:42`
- Intervalo: `src/app.py:42-67`
- Múltiplas linhas do mesmo arquivo: `src/app.py:42,58,91`

Use paths relativos à raiz do projeto. Não invente linhas — se o problema é o arquivo inteiro, cite o intervalo completo (ex: `models.py:1-350`).

### Description

Uma frase dizendo **o que** o código faz, uma dizendo **por que** é problema. Evite jargão sem contexto; evite "isso é ruim" sem explicar. Ex:

- Ruim: "SQL mal escrito."
- Bom: "Query concatena input do usuário diretamente na string SQL, permitindo injeção."

### Impact

Foque em consequências **operacionais/visíveis**: perda de dados, escalonamento de privilégio, stack trace vazado, endpoint lento, bug em produção sob carga. Se o impacto for puramente estético (ex: magic number), diga isso mesmo — é honesto e calibra a prioridade.

### Recommendation

Aponte o padrão a ser aplicado, não uma receita de 20 linhas — o playbook tem o código pronto. Ex:

- "Extrair para `config/settings.py` lendo de `os.environ`. Ver padrão 1 do playbook."
- "Substituir por query parametrizada (`?` placeholders). Ver padrão 2 do playbook."

## Exemplo resumido

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: sample-api
Stack:   Python + Flask
Files:   4 analyzed | ~800 lines of code
Date:    2026-04-21

## Summary
CRITICAL: 3 | HIGH: 2 | MEDIUM: 2 | LOW: 1

## Findings

### [CRITICAL] Hardcoded Secret Key
File: app.py:7
Description: `SECRET_KEY` é definida como string literal no código-fonte. Qualquer pessoa com acesso ao repositório tem a chave usada para assinar sessões.
Impact: Comprometimento de sessões, forja de cookies, replay de tokens. Rotação exige redeploy.
Recommendation: Mover para variável de ambiente lida em `config/settings.py`. Ver padrão 1 do playbook.

### [CRITICAL] SQL Injection via String Concatenation
File: models.py:28, models.py:109-111
Description: Queries montam SQL concatenando valores do request (`"... WHERE email = '" + email + "'"`).
Impact: Atacante consegue ler qualquer tabela, alterar dados, executar comandos arbitrários no banco.
Recommendation: Usar placeholders parametrizados (`?` com tuple de valores). Ver padrão 2 do playbook.

### [HIGH] God Module
File: models.py:1-315
Description: Arquivo único concentra 4 domínios (produtos, usuários, pedidos, relatório) misturando SQL, mapeamento e regra de negócio.
Impact: Impossível testar isoladamente, mudança em um domínio afeta os outros, merge conflicts frequentes.
Recommendation: Quebrar em `models/<dominio>_model.py` + `controllers/<dominio>_controller.py`. Ver padrão 5 do playbook.

### [MEDIUM] N+1 em listagem de pedidos
File: controllers.py:187-199
Description: Loop de pedidos faz uma query por item + uma query por produto dentro do loop.
Impact: 1 pedido = 1 query; 100 pedidos = ~300 queries. Timeout sob carga.
Recommendation: JOIN em uma única query ou `joinedload` do ORM. Ver padrão 10 do playbook.

### [LOW] Print como logging
File: controllers.py:8, 161, 219
Description: Uso de `print(...)` para logging em ALL-CAPS misturado com logs normais.
Impact: Sem níveis, sem contexto, sem destino estruturado — inútil em produção.
Recommendation: Substituir por `logging` configurado via `config/logger.py`. Ver padrão 13 do playbook.

================================
Total: 8 findings
================================
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Checklist antes de enviar o relatório

- [ ] Cabeçalho preenchido com stack, quantidade de arquivos, LOC aproximado.
- [ ] Summary com contagem por severidade.
- [ ] Cada finding tem arquivo e linha exatos.
- [ ] Findings ordenados CRITICAL → LOW.
- [ ] Pelo menos 1 finding CRITICAL ou HIGH (se o projeto for grande o bastante para ter um).
- [ ] Se houver APIs deprecated detectadas, elas estão no relatório (obrigatório pelo desafio).
- [ ] Relatório gravado em `reports/audit-<project>.md`.
- [ ] Pergunta de confirmação `[y/n]` ao final — a skill **não pode** avançar sem resposta.
