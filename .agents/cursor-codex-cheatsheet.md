# Chuleta: Cursor + Codex en QuantLab

Guía rápida para el flujo de trabajo en este repo. No sustituye a `AGENTS.md`, `.agents/implementation-rules.md` ni `.agents/prompts/codex-master-prompt.md`.

## Regla base

- Cursor analiza alcance y revisa diffs.
- Codex propone plan mínimo, ejecuta y valida.
- No uses ambos editando el mismo archivo a la vez.
- En broker, execution, submit o tooling de seguridad: plan primero, scope mínimo.

## Prompt canónico

Para trabajo directo en el repo, usa:

- `.agents/prompts/codex-master-prompt.md`

Ese prompt define la versión larga del flujo de dos fases.

## 1. Cursor: análisis

```text
Read AGENTS.md and the relevant .agents files first:
- .agents/project-brief.md
- .agents/implementation-rules.md
- .agents/current-state.md
- .agents/cursor-codex-cheatsheet.md
- .agents/prompts/codex-master-prompt.md
- .cursor/rules/ and .cursor/mcp.json if relevant

Task:
Explain the exact scope of this change in QuantLab.

Output only:
- files involved
- architectural boundaries / what must not change
- risks
- smallest safe next step

Do not edit files.
```

## 2. Codex: plan

```text
Read these files first:
- AGENTS.md
- .agents/project-brief.md
- .agents/implementation-rules.md
- .agents/current-state.md
- .agents/cursor-codex-cheatsheet.md
- .agents/prompts/codex-master-prompt.md
- <target file(s)>

Task:
Propose the smallest safe change for this request.

Constraints:
- no edits yet
- no unrelated changes
- preserve backward compatibility unless explicitly noted
- keep scope narrow

Output only:
- goal
- exact files to change
- what must not change
- minimal plan
- validation commands
- suggested PR title + 4-line body
```

## 3. Codex: ejecución

```text
Execute the approved plan.

Constraints:
- change only the listed files
- no unrelated cleanup
- preserve compatibility
- run the validation commands
- show exact files changed
- show a compact diff summary
```

## 4. Cursor: revisión final

```text
Review the exact diff for this change.

Tell me:
1. whether scope stayed narrow
2. whether compatibility was preserved
3. any risk or caveat
4. whether this is ready to commit

Do not make edits.
```

## Validation matrix

- `docs/` or `.agents/` markdown only:
  - `git diff --check`
  - human read-through
- `desktop/` or `*.mjs` MCP work:
  - `node --check <file>`
  - `git diff --check`
- `src/quantlab/` or tests:
  - focused `pytest`
  - `python main.py --check` when CLI/runtime behavior changes
  - `git diff --check`

## Uso recomendado

- Cambio pequeño en `desktop/` o MCP: Cursor → Codex plan → Codex execute → Cursor
- Cambio CLI o contrato visible: Cursor → Codex plan → Codex execute → Cursor
- Broker / execution sensible: Cursor primero; Codex solo en subtareas muy acotadas

## Reglas de branch y PR

- Usa ramas `codex/…`
- 1 issue = 1 branch = 1 PR
- PR breve: Summary | Scope | Validation | Notes
- Evita `git add .`

