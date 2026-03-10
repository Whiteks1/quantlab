# Decision Log - QuantLab

This file records important architectural, workflow, and project-scope decisions.

---

## 2026-03-10 — QuantLab is CLI-first
**Decision**  
QuantLab will be developed primarily as a CLI-first quantitative research laboratory.

**Reasoning**  
This keeps the project focused on research quality, reproducibility, and modularity without introducing premature platform complexity.

**Implications**
- no service layer by default
- no SaaS assumptions
- no frontend as a current priority

---

## 2026-03-10 — No service layer in the current roadmap
**Decision**  
Broker APIs, dashboards, multi-user features, and broader service layers are out of current scope.

**Reasoning**  
These features may become relevant later, but they should not drive architecture before the research core is mature.

**Implications**
- prioritize research core
- prioritize portfolio and risk logic
- preserve extensibility without implementing platform complexity now

---

## 2026-03-10 — Branch-first development workflow
**Decision**  
All significant work must be done in dedicated branches. `main` remains stable.

**Reasoning**  
This supports safer collaboration between ChatGPT planning, Antigravity execution, and user validation.

**Implications**
- no direct work on `main`
- one scoped task per branch
- clearer PR history

---

## 2026-03-10 — `.agents` as project memory
**Decision**  
The `.agents/` directory is the source of workflow continuity and project memory.

**Reasoning**  
It reduces context overload and improves continuity between sessions.

**Implications**
- workflows must be read before execution
- current state must be maintained
- session summaries should preserve continuity

---

## Template

### YYYY-MM-DD — [Decision Title]
**Decision**  
[What was decided]

**Reasoning**  
[Why it was decided]

**Implications**  
[What changes because of this]