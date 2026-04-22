---
name: refactor-arch
description: Audita e refatora projetos backend legados para o padrão MVC de forma agnóstica à tecnologia (Python, Node.js, Ruby, Go, Java, PHP, etc.). Use SEMPRE que o usuário invocar `/refactor-arch`, pedir para "refatorar para MVC", "auditar arquitetura", "fazer audit report do projeto", "organizar código legado", "migrar monolito para camadas", "achar code smells e refatorar", ou quando o usuário estiver trabalhando em um projeto monolítico/desorganizado com violações claras de SOLID. Também dispare quando o usuário mencionar "God Class", "credenciais hardcoded", "SQL injection + refactor", "arquitetura bagunçada" — mesmo que não diga "MVC" explicitamente. A skill executa 3 fases sequenciais (Análise → Auditoria com confirmação → Refatoração com validação) e funciona em qualquer stack porque detecta a tecnologia em tempo de execução.
---

# refactor-arch

Transforma projetos legados em código MVC limpo através de três fases sequenciais: **Análise → Auditoria → Refatoração**.

Funciona em qualquer stack (Python/Flask/Django, Node/Express/NestJS, Ruby/Rails/Sinatra, Go/Gin/Echo, Java/Spring, PHP/Laravel, C#/ASP.NET, etc.) porque detecta a tecnologia em tempo de execução e aplica **princípios arquiteturais universais** — não sintaxe específica de uma linguagem.

## Princípios que guiam esta skill

1. **MVC e SOLID são universais.** As três camadas (modelo de dados, visualização/roteamento, controlador de fluxo) existem em toda stack. Muda o idioma, não a ideia. Detecte a forma da casa; não se prenda à sintaxe.
2. **Auditar antes de refatorar.** Nunca toque em um arquivo sem que o usuário tenha revisado e aprovado a lista de findings. A confiança vem de ver o mapa antes do trator.
3. **Segurança vem primeiro.** Credenciais em claro, injeção, hashing fraco e exposição de dados sensíveis são sempre CRITICAL — antecedem qualquer cosmética arquitetural. Uma refatoração que deixa uma senha vazando é uma falha, não uma melhoria.
4. **Preservar comportamento externo.** A aplicação deve iniciar e os endpoints originais devem responder da mesma forma depois da refatoração. Se o contrato de uma rota vai mudar, avise explicitamente antes.
5. **Respeitar o que já existe.** Projetos parcialmente organizados já escolheram convenções — mover `routes/` para `views/` só para seguir um template é churn. Complete o que falta; não renomeie o que já funciona.

## Invocação

A skill é tipicamente invocada via `/refactor-arch` com o diretório atual sendo o projeto-alvo. Se o usuário pedir "refatore este projeto para MVC" ou similar, siga o mesmo fluxo.

Antes de começar, confirme em 1–2 perguntas curtas:
- Qual é o projeto-alvo (geralmente `pwd`).
- Se existe um comando conhecido de boot/smoke-test que possa ser usado na Fase 3 (`npm start`, `flask run`, `python app.py`, `go run`, etc.). Se o usuário não souber, detecte a partir do manifesto de dependências.

## Fase 1 — Análise

**Objetivo:** entender o que existe antes de julgar.

Leia `references/project-analysis.md` para os heurísticos de detecção.

Passos:

1. **Detectar a stack** a partir do manifesto de dependências (package.json, requirements.txt, Gemfile, go.mod, pom.xml, Cargo.toml, composer.json, etc.) e das extensões dominantes.
2. **Identificar o framework web** pelas dependências e pelos imports no entry point.
3. **Identificar o storage** pelos drivers nas dependências e connection strings no código/config.
4. **Mapear a arquitetura atual** — listagem de pastas, tamanho de arquivos, existência (ou ausência) de camadas separadas. Um monolito tem ≤ 5 arquivos concentrando tudo; um projeto parcial tem pastas como `models/`, `routes/`, `services/` mas pode misturar responsabilidades.
5. **Inferir o domínio** lendo nomes de tabelas, modelos, rotas. Descreva em uma linha o que a aplicação faz.

Imprima o resumo **exatamente** neste formato (é o contrato de saída da fase):

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se detectável>
Framework:     <framework + versão>
Dependencies:  <principais libs relevantes>
Domain:        <1 linha descrevendo o que a app faz>
Architecture:  <monolítico | camadas parciais | estruturado>
Source files:  <N> files analyzed
DB/storage:    <tabelas detectadas ou tipo de storage>
================================
```

## Fase 2 — Auditoria

**Objetivo:** produzir uma lista de findings acionável e pedir confirmação antes de qualquer mudança.

Leia `references/anti-patterns-catalog.md` (o catálogo com sinais de detecção) e `references/report-template.md` (formato do relatório).

Passos:

1. Varra os arquivos-fonte cruzando cada anti-pattern do catálogo contra o código. Para cada ocorrência, registre **arquivo e linhas exatos** (`file.ext:linha` ou intervalo `file.ext:L-L`), descrição do problema, impacto concreto e recomendação. Arquivo e linha importam porque são o que permite ao usuário verificar em segundos.
2. Classifique pela severidade definida no catálogo (CRITICAL → HIGH → MEDIUM → LOW) e ordene o relatório nesta ordem. O usuário precisa ver o pior primeiro.
3. **Cubra obrigatoriamente**:
   - Segurança: credenciais hardcoded, SQL injection, hashing fraco, vazamento de secrets em responses, endpoints administrativos sem auth, debug mode em produção.
   - MVC/SOLID: God Class/Module, lógica de negócio em controllers, lógica de negócio em models, estado global mutável.
   - Performance: N+1, transações faltando, ausência de paginação.
   - Qualidade: `except:` engolindo erros, validação duplicada, magic numbers, logging via print, imports mortos.
   - **APIs deprecated**: identifique usos de APIs obsoletas e recomende o equivalente moderno (callbacks vs promises/async, `type(x) == list` vs `isinstance`, SHA1/MD5 para senha vs bcrypt/argon2, `datetime.utcnow()` vs timezone-aware, SDK calls descontinuadas).
4. Imprima o relatório completo na conversa no formato do template e **grave uma cópia** em `reports/audit-<nome-projeto>.md` (crie a pasta `reports/` se não existir). Esse arquivo é um entregável do desafio.
5. **Pause e peça confirmação explícita** antes de avançar:

   ```
   Total: <N> findings
   ================================
   Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
   ```

   **Não modifique arquivo algum** até o usuário responder `y` (ou equivalente). Se ele responder `n` ou pedir para revisar, pare aqui — o relatório já é um entregável valioso sozinho.

Por que pausar? Porque o usuário precisa de uma chance de discordar da priorização, vetar mudanças que não quer, ou simplesmente ficar só com o relatório. Refatorar sem consentimento é o pior tipo de agente.

## Fase 3 — Refatoração

**Objetivo:** reorganizar para MVC limpo e validar que a aplicação continua funcionando.

Leia `references/mvc-guidelines.md` (o alvo arquitetural) e `references/refactoring-playbook.md` (padrões concretos de transformação com exemplos antes/depois).

Passos:

1. **Crie a estrutura-alvo de diretórios** adequada à convenção da linguagem (`src/` no Node, pacote raiz no Python, `app/` no Rails, etc.). Camadas mínimas:
   - `config/` — configuração lida de variáveis de ambiente (nunca hardcoded).
   - `models/` — dados e acesso a storage, apenas.
   - `views/` ou `routes/` — roteamento, desserialização de request e serialização de response. Pode ser a mesma camada; depende do framework.
   - `controllers/` — orquestração: recebe do roteamento, chama models/services, devolve. Onde a lógica de aplicação vive.
   - `services/` (opcional) — regras de negócio reutilizáveis entre controllers. Crie quando a mesma regra aparece em 2+ controllers.
   - `middlewares/` — error handling, logging, autenticação, cross-cutting.
   - Entry point (`app.py`, `server.js`, `main.go`, etc.) como **composition root**: só faz wiring, não contém lógica.
2. **Aplique as transformações do playbook** para eliminar cada finding CRITICAL e HIGH. Trate MEDIUM/LOW oportunisticamente quando o esforço for baixo — não persiga 100% dos LOW se isso inflar o diff.
3. **Preserve o contrato externo**: mesmas rotas, mesmos verbos, mesmo shape de request/response. Se mudar algo (por exemplo, remover campo `password` de uma resposta), mencione explicitamente no resumo final.
4. **Valide o resultado**:
   - Inicie a aplicação com o comando detectado na Fase 1. Se falhar no boot, **pare e reporte**.
   - Chame os endpoints principais (use curl ou o comando de smoke-test combinado). Verifique que respondem com o mesmo status code e shape.
   - Se houver testes, rode-os.
5. Imprima o resumo final no formato do exemplo abaixo:

   ```
   ================================
   PHASE 3: REFACTORING COMPLETE
   ================================
   ## New Project Structure
   <árvore de diretórios>

   ## Validation
     ✓ Application boots without errors
     ✓ All endpoints respond correctly
     ✓ <N> anti-patterns eliminated, <M> remaining (justificativa)
   ================================
   ```

Se a validação falhar em qualquer ponto, **pare e reporte o erro** ao usuário em vez de tentar consertar com mais código cego. Mostre o stack trace ou o output do endpoint. O usuário decide o próximo passo.

## Quando o projeto já tem camadas parciais

Projetos que já têm pastas como `models/`, `routes/`, `services/` não precisam de reestruturação completa. Nesse caso o foco muda:

- Mova lógica de negócio para a camada correta (ela costuma escapar para dentro de route handlers).
- Remova duplicação entre camadas (ex: regra de "overdue" recalculada em 5 lugares).
- Adicione o que falta: módulo de config lendo env vars, error-handling middleware, logger estruturado.
- Corrija os problemas de segurança/qualidade da Fase 2, mesmo quando a estrutura de pastas já está OK.

Não invente pasta nova para cada problema e não renomeie convenções que já funcionam — respeitar a forma que o projeto escolheu reduz o diff e torna a refatoração revisável.

## Arquivos de referência

- `references/project-analysis.md` — heurísticos de detecção de linguagem, framework, storage e arquitetura. **Leia na Fase 1.**
- `references/anti-patterns-catalog.md` — catálogo de anti-patterns com sinais de detecção e severidade. **Leia na Fase 2.**
- `references/report-template.md` — formato obrigatório do relatório de auditoria. **Leia na Fase 2.**
- `references/mvc-guidelines.md` — responsabilidades de cada camada no alvo MVC. **Leia na Fase 3.**
- `references/refactoring-playbook.md` — padrões de transformação (antes/depois) para cada anti-pattern. **Leia na Fase 3.**
