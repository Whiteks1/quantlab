You are working in the QuantLab repository.

Core rule:
QuantLab is the downstream validation layer. It consumes upstream research intents, not editorial news.
QuantLab should only act on upstream signals when they improve:
- research
- validation
- risk control
- product priorities

Mission:
Convert research intents into reproducible quantitative tests, paper discipline, and execution safety.

Primary responsibilities:
- validate hypotheses
- compare strategies
- run `run`
- run `forward_eval`
- support paper trading
- maintain operational discipline before broker execution

Non-goals:
- do not become an editorial or news aggregation layer
- do not absorb Quant Pulse logic
- do not accept broad ad hoc strategy growth without a clear contract
- do not expand live execution before paper discipline, safety, and observability are mature

Quant Pulse intake rule:
Only consume a Quant Pulse signal if it can be translated into at least one of:
- a testable research hypothesis
- a risk filter
- a product or instrumentation priority

Recommended hypothesis families:
- trend
- mean reversion
- event-driven
- regime filter
- rotation

Strategy backlog priority:
1. strategy registry/factory
2. minimal trend family
3. minimal mean reversion family

Expected mapping:
- continuity / momentum / confirmed flows -> trend family
- overextension / rumor / post-event reversal -> mean reversion family
- hack / venue stress / liquidity deterioration -> risk filter or regime gating
- repeated signal patterns exposing workflow gaps -> instrumentation or workflow priority

Operational rule:
Quant Pulse is allowed to influence QuantLab only when it produces testable research, clear risk controls, or a product priority.
If it cannot be tested, filtered, or instrumented in QuantLab, it should not drive the roadmap.

Change constraints:
- keep changes small and scoped
- do not mix refactors, new features, and architecture changes in one task
- preserve separation between Quant Pulse and QuantLab
- do not add many strategies at once
- do not couple new strategies directly into the core flow if a registry/factory is required first

Validation requirements:
- add focused tests for the touched area
- run `git diff --check`
- run relevant CLI or artifact checks when behavior changes

Output requirements:
- exact files changed
- compact summary of the implementation
- residual limitations
- next logical slice
