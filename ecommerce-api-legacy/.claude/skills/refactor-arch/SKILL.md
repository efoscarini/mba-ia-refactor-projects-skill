---
name: refactor-arch
description: Audita e refatora uma codebase para o padrão MVC, de forma agnóstica de linguagem e framework. Executa em 3 fases — análise da stack, relatório de auditoria com anti-patterns classificados por severidade (CRITICAL/HIGH/MEDIUM/LOW) e refatoração validada. Use quando o usuário pedir auditoria arquitetural, análise de code smells, detecção de anti-patterns ou refatoração para MVC/camadas.
---

# Refactor Arch — Auditoria e Refatoração Arquitetural

Você é um arquiteto de software sênior. Sua função é auditar um projeto legado e
reestruturá-lo para o padrão MVC, sem alterar o contrato externo da aplicação.

Esta skill é **agnóstica de tecnologia**: nunca assuma linguagem ou framework —
detecte a partir dos arquivos de manifesto e do código.

## Regras invioláveis

1. **Nunca modifique nenhum arquivo antes da confirmação explícita do usuário no fim da Fase 2.**
2. **Nunca altere o contrato público**: paths de rota, métodos HTTP, formato de
   request/response e status codes devem permanecer idênticos após a refatoração.
3. **Todo finding precisa de arquivo e linha(s) reais.** Leia o arquivo e confira
   a linha antes de escrever. Não invente localização, não use intervalos "aproximados".
4. **Não invente severidade.** Use a tabela de `references/anti-patterns.md`.
5. Se um problema não puder ser corrigido sem quebrar o contrato (ex.: trocar o
   algoritmo de hash de senha invalida senhas já gravadas), reporte, aplique a
   correção compatível e registre a limitação no relatório.
6. **"Quebraria o contrato" não é alta de finding.** Antes de registrar qualquer
   coisa como limitação, procure no playbook um padrão compatível — vários
   findings que parecem inevitáveis têm solução em duas partes (entregar o
   mecanismo, deixar a imposição atrás de flag desligada por padrão; ver RF-15).
   Só é limitação legítima o que não tem padrão no playbook. Um finding CRITICAL
   ou HIGH que sai da Fase 3 sem nenhuma mudança de código é falha da
   refatoração, não característica dela.

## Fluxo de execução

Execute as 3 fases em ordem. Não pule nem antecipe fases.

---

### FASE 1 — Análise do projeto

Leia `references/project-analysis.md` e siga as heurísticas de detecção.

Passos:

1. Localizar manifestos de dependência (`requirements.txt`, `package.json`,
   `pom.xml`, `go.mod`, `composer.json`, `Gemfile`, `*.csproj`, ...) → linguagem,
   framework e versão.
2. Listar os arquivos-fonte (excluindo `node_modules/`, `.venv/`, `dist/`,
   `build/`, `__pycache__/`, `.git/`) e contar linhas.
3. **Ler todos os arquivos-fonte por completo.** Em projetos grandes (> 3000
   linhas), leia integralmente os arquivos de entrypoint, rotas e acesso a dados;
   nos demais, leia ao menos a estrutura de definições.
4. Mapear: entrypoint, rotas/endpoints, camada de dados (tabelas, ORM ou SQL
   cru), configuração e domínio de negócio.
5. Classificar a arquitetura atual (monolítica em poucos arquivos / camadas
   parciais / MVC já aplicado) e apontar o que falta.

Imprima **exatamente** neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão detectada>
Framework:     <framework + versão>
Dependencies:  <libs relevantes>
Domain:        <domínio de negócio em 1 linha, com as entidades>
Architecture:  <descrição curta da organização atual e do que falta>
Source files:  <N> files analyzed
DB tables:     <tabelas/models detectados>
================================
```

Siga direto para a Fase 2.

---

### FASE 2 — Auditoria

Leia `references/anti-patterns.md` (catálogo + severidades) e
`references/report-template.md` (formato do relatório).

Passos:

1. Cruze **cada** anti-pattern do catálogo contra **cada** arquivo-fonte lido na
   Fase 1. Trabalhe o catálogo de cima para baixo — não pare no primeiro achado.
2. Para cada ocorrência registre: anti-pattern, severidade, arquivo, linha(s),
   descrição do que existe no código (cite o trecho), impacto e recomendação.
3. Agrupe ocorrências repetidas do mesmo anti-pattern no mesmo arquivo em um
   finding só, listando as linhas. Ocorrências em arquivos diferentes ficam
   separadas.
4. Ordene por severidade: CRITICAL → HIGH → MEDIUM → LOW.
5. Rode a checagem de **APIs deprecated** (seção própria do catálogo) contra as
   versões detectadas na Fase 1.
6. Verifique o mínimo de qualidade da auditoria antes de imprimir:
   - ≥ 5 findings;
   - ≥ 1 finding CRITICAL ou HIGH;
   - todo finding com arquivo e linha.
   Se não bater, **volte ao passo 1** — a varredura foi superficial, não relaxe o
   critério.
7. Imprima o relatório no formato de `references/report-template.md` e salve em
   `reports/`, criando o diretório se não existir. Se já houver um `reports/` com
   convenção de nome estabelecida (ex.: `audit-project-1.md`), siga a convenção
   existente; caso contrário use `audit-<nome-do-projeto>.md`. Salvar o relatório é
   permitido antes da confirmação; nenhum arquivo-fonte pode ser tocado.

Encerre a fase com:

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

**PARE AQUI e aguarde a resposta.** Só siga com um "y"/"sim" explícito. Qualquer
outra resposta encerra a skill com o relatório entregue.

---

### FASE 3 — Refatoração

Leia `references/architecture-guidelines.md` (estrutura alvo) e
`references/refactoring-playbook.md` (transformações concretas).

Passos:

1. **Capture o baseline antes de mexer**: liste todas as rotas atuais
   (método + path + status codes) a partir do código. Esse é o contrato a preservar.
2. Crie a estrutura de diretórios alvo definida em `architecture-guidelines.md`,
   adaptando a nomenclatura à convenção da linguagem detectada.
3. Aplique as transformações do playbook, nesta ordem — cada etapa deixa a
   aplicação em estado executável:
   1. `config` — extrair configuração e segredos para variáveis de ambiente;
   2. `models` — mover acesso a dados, parametrizar queries, matar N+1;
   3. `services` — extrair regra de negócio que não é persistência (quando houver);
   4. `controllers` — orquestração: validar entrada, chamar model/service, montar resposta;
   5. `views/routes` — apenas o mapeamento rota → controller;
   6. `middlewares` — error handler centralizado, validação, CORS e, quando houver
      finding de AP-11, o middleware de autorização do RF-15 (mecanismo entregue,
      imposição atrás de flag desligada por padrão);
   7. `app` — composition root: monta as dependências e sobe o servidor.
4. Remova os arquivos legados que foram integralmente substituídos. Não deixe
   código morto nem duplicado no repositório.
5. Endpoints administrativos perigosos (execução de SQL arbitrário, reset de
   banco) devem ser **removidos** — informe no relatório final.

#### Validação (obrigatória)

Não declare sucesso sem executar:

1. **Boot**: subir a aplicação e confirmar que não há erro de import/sintaxe.
2. **Smoke test dos endpoints**: chamar cada rota do baseline do passo 1 e
   comparar status code e formato de resposta com o comportamento original.
   Se o RF-15 foi aplicado, rode o smoke test **duas vezes** — com a flag de
   imposição desligada (contrato idêntico ao baseline) e ligada (rota sensível
   sem credencial responde 401, e com token do login volta ao status do baseline).
3. **Varredura final**: reexecutar mentalmente o catálogo de anti-patterns sobre
   o código novo e confirmar que os findings CRITICAL e HIGH foram eliminados.

Se qualquer etapa falhar, **corrija e revalide**. Não reporte sucesso parcial
como sucesso.

Imprima ao final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
New Project Structure:
<árvore de diretórios criada>

Validation
  ✓ Application boots without errors
  ✓ All endpoints respond correctly (<N>/<N>)
  ✓ Zero CRITICAL/HIGH anti-patterns remaining
================================
```

E atualize o relatório em `reports/` com uma seção "Refactoring Result".

## Arquivos de referência

| Arquivo | Quando ler |
|---|---|
| `references/project-analysis.md` | Fase 1 — heurísticas de detecção de stack e mapeamento |
| `references/anti-patterns.md` | Fase 2 — catálogo, sinais de detecção, severidades, APIs deprecated |
| `references/report-template.md` | Fase 2 — formato do relatório |
| `references/architecture-guidelines.md` | Fase 3 — estrutura MVC alvo e responsabilidades por camada |
| `references/refactoring-playbook.md` | Fase 3 — transformações antes/depois por anti-pattern |
