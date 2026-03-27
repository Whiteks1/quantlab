# Native Acceleration Strategy

QuantLab should remain a Python-first system.

That is still the right choice for:

- CLI and orchestration
- artifact generation and reporting
- broker and execution-venue adapters
- signing and request-shaping logic
- run/session lifecycle management
- local UI and control-surface work

The native-code question should therefore be framed narrowly:

- where do we have real computational hotspots?
- what is the smallest boundary that could benefit from acceleration?
- should the first step be `Numba`, `C++`, or `Rust`?

## Current Recommendation

The recommended path is:

1. keep QuantLab Python-first
2. profile before rewriting
3. extract only a measured hotspot into a small compute boundary
4. prefer `Numba` first for the earliest experiment
5. move to `C++` only if the hotspot proves stable, important, and insufficiently served by Numba
6. treat `Rust` as a later alternative for safety-focused native modules, not the first acceleration move

## Best Candidate Today

The first realistic hotspot candidate is:

- [src/quantlab/backtest/engine.py](../src/quantlab/backtest/engine.py)

Why this file is the best first candidate:

- it contains repeated row-wise state transitions
- it computes positions, trades, fees, and slippage in explicit loops
- it sits on the core research path used by runs, sweeps, and strategy comparison
- it is computational work, not integration plumbing

This is the kind of logic that can be extracted into a smaller array-based kernel without dragging the rest of the app into native-code complexity.

## Poor Candidates

These areas should stay Python-owned unless future evidence is overwhelming:

- `src/quantlab/cli/`
- `main.py`
- `src/quantlab/brokers/`
- `src/quantlab/runs/`
- `src/quantlab/reporting/`
- `src/quantlab/ui/`
- `src/quantlab/data/sources.py`

Reasons:

- the cost there is dominated by orchestration, I/O, HTTP, signing, serialization, or product logic
- native code would raise maintenance cost without changing the real bottleneck

## Language Choice

### Numba

Best first acceleration step when:

- the hotspot is numeric
- the boundary can be expressed as arrays
- fast iteration matters more than distribution polish
- we want to prove speedup before introducing a compiled toolchain

Pros for QuantLab:

- lowest migration cost
- stays close to the current Python code
- very good fit for loop-heavy backtest kernels
- avoids premature package/distribution complexity

Cons:

- less suitable for rich object graphs or mixed pandas-heavy code
- can become awkward if the kernel shape is not kept narrow

### C++

Best second-stage option when:

- the hotspot is stable and clearly measured
- latency or throughput matters enough to justify a compiled extension
- the kernel boundary is small and long-lived

Pros for QuantLab:

- strongest raw performance ceiling
- good fit for future order-book replay, tick processing, or deeper simulation kernels
- good ecosystem for Python bindings via `pybind11`

Cons:

- higher build and packaging complexity
- more friction for Windows contributors and CI
- easier to overuse in parts of the app that are not actually compute-bound

### Rust

Best considered when:

- native work expands beyond one tiny kernel
- safety and maintainability matter as much as speed
- the team is willing to own a second systems-language toolchain

Pros for QuantLab:

- safer native boundary than C++
- attractive for future protocol, signing, or streaming infrastructure if native code grows

Cons:

- steeper adoption cost than Numba
- less direct as a first optimization move for the current backtest engine
- introduces packaging/tooling complexity before it is clearly justified

## Recommended First Extraction Boundary

Do not rewrite the whole backtest module.

Instead, target a narrow kernel responsible for:

- position-state transitions
- trade detection
- fee/slippage accumulation
- net strategy return assembly

Keep these layers in Python:

- DataFrame preparation
- column naming and artifact shaping
- report generation
- strategy and CLI orchestration

In other words:

- Python owns the workflow
- the accelerated kernel only owns the inner numeric loop

## Proposed Rollout

### Step 1

Profile representative `run` and `sweep` workloads.

That profiling surface now exists via:

- [docs/backtest-profiling.md](./backtest-profiling.md)
- `python scripts/profile_backtest.py`

### Step 2

Refactor the backtest loop into a pure array-oriented helper with a stable contract.

### Step 3

Try `Numba` first on that helper.

### Step 4

If the speedup is not enough and the boundary remains stable, promote that helper to a compiled extension.

### Step 5

Only after that, consider deeper native work for:

- tick replay
- order-book simulation
- high-frequency market-data normalization

## Final Decision

For QuantLab today:

- `Python` remains the right application language
- `Numba` is the best first acceleration experiment
- `C++` is the best first serious native option if a measured hotspot outgrows Numba
- `Rust` is interesting, but not the best first move for the repo's current bottlenecks

So the practical answer is:

- do not move the app to C++
- do not add native code broadly
- target the backtest engine first
- validate with profiling
- escalate from Python -> Numba -> C++ only if the data justifies it
