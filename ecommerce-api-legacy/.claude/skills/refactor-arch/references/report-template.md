# Template do Relatório de Auditoria

Referência da **Fase 2**. Este é o formato exato do relatório — impresso no
terminal e salvo em `reports/` — seguindo a convenção de nome que já existir no
diretório (ex.: `audit-project-1.md`) ou, se não houver, `audit-<nome-do-projeto>.md`.

## Regras de preenchimento

- Um bloco `###` por finding, ordenados **CRITICAL → HIGH → MEDIUM → LOW**.
- `File:` sempre com caminho relativo à raiz do projeto **e** linha(s):
  `models.py:28` (uma linha), `models.py:139-166` (bloco), `routes/task_routes.py:30-39,71-80` (ocorrências múltiplas).
- `Description:` diz o que **está** no código, citando o identificador ou o
  trecho. Nada de descrição genérica tipo "código mal escrito".
- `Impact:` diz o que quebra na prática — não repita a descrição.
- `Recommendation:` uma ação concreta, que a Fase 3 consiga executar.
- `Anti-pattern:` o ID do catálogo (AP-xx), para rastreabilidade.
- Contagens do `Summary` têm que bater com o número de blocos.

## Template

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome do diretório do projeto>
Stack:   <Linguagem> + <Framework versão>
Files:   <N> analyzed | ~<N> lines of code
Date:    <YYYY-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### [CRITICAL] <Nome do anti-pattern>
- **Anti-pattern:** AP-xx
- **File:** `<caminho>:<linhas>`
- **Description:** <o que existe no código, com o trecho ou identificador>
- **Impact:** <consequência prática>
- **Recommendation:** <ação concreta>

### [HIGH] <Nome do anti-pattern>
...

### [MEDIUM] <Nome do anti-pattern>
...

### [LOW] <Nome do anti-pattern>
...

## Deprecated APIs
| API | File:Line | Substituir por |
|---|---|---|
| <api> | `<arquivo>:<linha>` | <substituto> |

(ou "Nenhuma API deprecated detectada.")

## Preserved Contract
Rotas que precisam continuar respondendo igual após a Fase 3:

| Método | Path | Status codes |
|---|---|---|
| GET | /exemplo | 200, 404 |

================================
Total: <N> findings
================================
```

## Seção adicionada ao final da Fase 3

Depois da refatoração, acrescente ao mesmo arquivo:

```markdown
## Refactoring Result

### Estrutura final
<árvore de diretórios>

### Findings resolvidos
| ID | Anti-pattern | Severidade | Como foi resolvido |
|---|---|---|---|
| AP-xx | <nome> | CRITICAL | <transformação aplicada> |

### Findings não resolvidos
| ID | Motivo | Risco residual |
|---|---|---|

(ou "Nenhum — todos os findings foram resolvidos.")

### Mudanças intencionais de contrato
Uma entrada por mudança, com a rota afetada e o motivo. Quando o RF-15 for
aplicado, o 401 das rotas sensíveis entra aqui — rota por rota, com o nome da
variável que restaura o contrato original.

### Classificação de rotas (só quando o RF-15 for aplicado)
| Rota | Classificação | Critério |
|---|---|---|
| GET /exemplo | sensível | agregado do negócio |
| GET /health | aberta | health check |

A tabela cobre **todas** as rotas, inclusive as abertas — é o que permite revisar
a decisão.

### Validação
- Boot: <resultado>
- Endpoints: <N>/<N> respondendo conforme o contrato
- Autorização (RF-15): resultado nos dois modos, `AUTH_ENFORCED` true e false
- Varredura final: <CRITICAL/HIGH remanescentes>
```

## Erros comuns a evitar

| Erro | Correção |
|---|---|
| "File: models.py" sem linha | sempre incluir a linha |
| Intervalo chutado (`1-350` num arquivo de 314 linhas) | conferir o total de linhas antes |
| Summary divergente da contagem de blocos | recontar antes de imprimir |
| Findings fora de ordem de severidade | reordenar |
| Mesmo anti-pattern repetido em 6 blocos do mesmo arquivo | agrupar em um bloco listando as linhas |
| Recomendação vaga ("melhorar o código") | ação executável |
