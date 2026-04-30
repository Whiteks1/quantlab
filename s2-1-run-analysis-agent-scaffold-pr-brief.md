# PR Brief — S2.1 Run Analysis Agent Scaffold

## Branch

```
feat/agents-run-analysis-scaffold
```

## Prerequisite

Open (or reuse) one issue before branching, per `AGENTS.md`:
*"Do not start branch work without an issue unless the task is an urgent fix."*

Replace `<ISSUE>` in the PR body below with the actual issue number.

## Commits (battery)

Two logical commits, per `CONTRIBUTING.md` preferred pattern:

1. `feat(agents): scaffold run-analysis agent package`
   - `src/quantlab/agents/__init__.py` (new)
   - `src/quantlab/agents/run_analysis/__init__.py` (new)
2. `test(agents): add scaffold tests for run-analysis agent`
   - `test/test_run_analysis_agent_scaffold.py` (new)

If the split proves too expensive locally, a single coherent commit is
acceptable per `CONTRIBUTING.md`.

## PR Title

```
feat(agents): scaffold run-analysis agent package (S2.1)
```

## PR Body

```markdown
## Summary

Introduce the `quantlab.agents.run_analysis` package as a pure scaffold
for the Run Analysis Agent pilot. No runtime logic, no report emission,
no log emission. Closes #<ISSUE>.

## Why

Slice S2.1 of the agent-layer plan. The pilot spec
(`run-analysis-agent-pilot.md`) requires `files_written` to be exactly
`{report, log}` (invariant I2). A scaffold that wrote any partial subset
would contradict I2. This slice therefore introduces no runtime — only
import paths, docstrings anchoring contract references, and tests
verifying no side effects on import.

The pilot runtime contract (I1–I12) first becomes enforceable at S2.4,
when the emitter is introduced and both report and log are written in
the same execution.

## Scope

- New package: `src/quantlab/agents/`
  - `__init__.py` with a docstring that references
    `NNNN-agent-layer-scope.md` and contains the six non-goals keywords
    literally for grep-ability: `trading`, `risk`, `execution`,
    `brokers`, `pretrade`, `portfolio`.
- New subpackage: `src/quantlab/agents/run_analysis/`
  - `__init__.py` with a docstring that references
    `run-analysis-agent-pilot.md`, declares `Status: scaffold (S2.1)`,
    and states the I2-deferred-to-S2.4 anchor explicitly.
- New test: `test/test_run_analysis_agent_scaffold.py` with six cases
  (see Validation).

Explicitly out of scope for this PR:

- No `runner.py`, `errors.py`, `log_writer.py`, `__main__.py`.
- No `console_scripts` registration in `pyproject.toml`.
- No changes to `src/quantlab/{execution,brokers,pretrade,portfolio,cli,ui}/`.
- No changes to `.github/workflows/ci.yml`.
- No writes to `outputs/` in any code path (tests never touch it).

## Validation

Six pytest cases in `test/test_run_analysis_agent_scaffold.py`:

1. `import quantlab.agents` succeeds.
2. `import quantlab.agents.run_analysis` succeeds.
3. Importing either package performs no filesystem writes outside
   Python bytecode caches (tested against a `tmp_path` cwd).
4. `quantlab.agents.__doc__` contains the six non-goals keywords.
5. `quantlab.agents.run_analysis` exposes no runtime attributes
   (`run`, `main`, `runner`, `execute`).
6. `import quantlab.agents.run_analysis.__main__` raises
   `ModuleNotFoundError`.

Local run: `pytest test/test_run_analysis_agent_scaffold.py -v`.
Pre-existing 23 tests under `test/` remain green.

## Notes

- `pyproject.toml` is unchanged; the new package is auto-discovered via
  `[tool.setuptools.packages.find]`.
- The test file is placed at `test/` root, following the repo's flat
  convention (no `__init__.py`, unique file name).
- Diff ≤ ~100 LOC net.
- Follow-up slices, opened as issues after merge:
  - S2.2 — validator as a pure function, no I/O.
  - S2.3 — extractor as a pure function, no I/O.
  - S2.4 — emitter + runner wiring. First slice where the pilot runtime
    contract (I1–I12) is engaged end-to-end.
- References:
  - Spec: `run-analysis-agent-pilot.md`
  - ADR: `NNNN-agent-layer-scope.md`
```

## DoD Checklist (copy into the PR as a task list)

- [ ] `src/quantlab/agents/__init__.py` and
      `src/quantlab/agents/run_analysis/__init__.py` are the only
      non-test files added.
- [ ] No `runner.py`, `errors.py`, `log_writer.py`, `__main__.py` in
      the new package.
- [ ] `grep -R "trading\|risk\|execution\|brokers\|pretrade\|portfolio" src/quantlab/agents/__init__.py`
      returns all six terms.
- [ ] `grep -R "from quantlab.execution\|from quantlab.brokers\|from quantlab.pretrade\|from quantlab.portfolio" src/quantlab/agents/`
      returns empty.
- [ ] `git diff pyproject.toml` shows no changes.
- [ ] `find src/quantlab/agents -name "__main__.py"` returns empty.
- [ ] `find src/quantlab/agents -name "*.py" -not -name "__init__.py"`
      returns empty.
- [ ] All 6 scaffold tests pass; pre-existing 23 tests remain green.
- [ ] Diff ≤ ~100 LOC net.
- [ ] PR body references `run-analysis-agent-pilot.md` and
      `NNNN-agent-layer-scope.md` explicitly.
- [ ] Post-merge: issue opened for S2.2 (validator, pure function, no I/O).
- [ ] Post-merge: issue opened for S2.4 (emitter + runner wiring — first
      slice that engages I1–I12).

## Merge style

`Squash and merge`, per `CONTRIBUTING.md`.

## Post-merge

- Let GitHub delete the remote branch.
- Open the two follow-up issues (S2.2 and S2.4) referencing the merge
  commit of this PR.
