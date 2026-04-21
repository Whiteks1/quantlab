# Learned-Model Artifact Contract

Status: proposed
Issue: #438
Stage: N.0 - Neural Research Foundations

This document defines the minimum artifact contract and evaluation discipline required before QuantLab supports learned-model research.

It is intentionally documentary. It does not add training loops, ML dependencies, model serving, paper promotion, or execution use.

## Strategic Rule

Neural Track = research discipline expansion, not product repositioning.

QuantLab may evolve from validating explicit strategies toward validating explicit strategies and learned models, but learned models must meet the same or stricter evidence standards as rule-based strategies.

QuantLab must not be reframed as an AI trading platform.

## Authority Model

QuantLab remains the evidence authority for:

- dataset definition
- feature definition
- model configuration
- training metadata
- evaluation logic
- baseline comparison
- promotion criteria
- canonical artifacts

Stepbit may later orchestrate learned-model workflows, but it must not own model validity, artifact contracts, or promotion decisions.

Quant Pulse may later provide upstream hypotheses, signal context, or candidate research prompts, but it must not certify learned-model validity.

## Contract Root

Learned-model experiments should use a dedicated artifact root so they do not blur rule-based run outputs or paper-session outputs.

Proposed canonical root:

```text
outputs/model_runs/<model_run_id>/
```

Minimum artifact set:

```text
outputs/model_runs/<model_run_id>/
  dataset_manifest.json
  feature_manifest.json
  model_config.json
  training_summary.json
```

Optional future artifacts may include:

```text
outputs/model_runs/<model_run_id>/
  validation_summary.json
  model_risk_report.json
  checkpoints/
  predictions.csv
  downstream_backtest/
```

Those optional artifacts are not part of this first slice.

## Required Artifacts

### `dataset_manifest.json`

Purpose:

- make the training/evaluation dataset traceable and reproducible
- prevent silent data changes from invalidating comparisons

Required fields:

- `schema_version`
- `artifact_type`
- `model_run_id`
- `created_at`
- `dataset_id`
- `source`
- `universe`
- `time_range`
- `rows`
- `target`
- `split`
- `data_hash`
- `generation_command`

Expected shape:

```json
{
  "schema_version": "1.0",
  "artifact_type": "quantlab.learned_model.dataset_manifest",
  "model_run_id": "model_20260421_001",
  "created_at": "2026-04-21T00:00:00Z",
  "dataset_id": "btc_usd_1h_v1",
  "source": {
    "kind": "local",
    "path": "data/BTC_USD_1h.csv"
  },
  "universe": ["BTC/USD"],
  "time_range": {
    "start": "2023-01-01",
    "end": "2025-12-31",
    "timezone": "UTC"
  },
  "rows": 0,
  "target": {
    "name": "forward_return",
    "horizon": "24h",
    "definition": "future close-to-close return over the configured horizon"
  },
  "split": {
    "method": "temporal",
    "train": {"start": "2023-01-01", "end": "2024-06-30"},
    "validation": {"start": "2024-07-01", "end": "2024-12-31"},
    "test": {"start": "2025-01-01", "end": "2025-12-31"}
  },
  "data_hash": "",
  "generation_command": ""
}
```

### `feature_manifest.json`

Purpose:

- make feature generation explicit and reviewable
- prevent untracked feature changes from producing incomparable model runs

Required fields:

- `schema_version`
- `artifact_type`
- `model_run_id`
- `dataset_id`
- `feature_set_id`
- `features`
- `lookback`
- `normalization`
- `leakage_guards`
- `feature_hash`
- `generation_command`

Expected shape:

```json
{
  "schema_version": "1.0",
  "artifact_type": "quantlab.learned_model.feature_manifest",
  "model_run_id": "model_20260421_001",
  "dataset_id": "btc_usd_1h_v1",
  "feature_set_id": "technical_v1",
  "features": [
    {
      "name": "rsi_14",
      "source": "indicator",
      "parameters": {"period": 14}
    }
  ],
  "lookback": {
    "max_bars": 200,
    "uses_future_data": false
  },
  "normalization": {
    "method": "train_split_only",
    "fit_scope": "train"
  },
  "leakage_guards": [
    "features must be computed without access to validation or test future values",
    "normalization statistics must be fitted on train split only"
  ],
  "feature_hash": "",
  "generation_command": ""
}
```

### `model_config.json`

Purpose:

- make model identity and hyperparameters reproducible
- separate model configuration from training outcomes

Required fields:

- `schema_version`
- `artifact_type`
- `model_run_id`
- `model_family`
- `model_name`
- `library`
- `hyperparameters`
- `random_seed`
- `training_objective`
- `input_shape`
- `output`

Expected shape:

```json
{
  "schema_version": "1.0",
  "artifact_type": "quantlab.learned_model.model_config",
  "model_run_id": "model_20260421_001",
  "model_family": "baseline_ml",
  "model_name": "logistic_regression",
  "library": {
    "name": "not_implemented",
    "version": null
  },
  "hyperparameters": {},
  "random_seed": 42,
  "training_objective": "classification",
  "input_shape": {
    "features": 0,
    "window": null
  },
  "output": {
    "kind": "probability",
    "target": "forward_return_positive"
  }
}
```

### `training_summary.json`

Purpose:

- make training and evaluation results auditable
- preserve enough metadata to reproduce or reject a model run
- make model metrics comparable with downstream market metrics

Required fields:

- `schema_version`
- `artifact_type`
- `model_run_id`
- `status`
- `started_at`
- `finished_at`
- `duration_seconds`
- `dataset_manifest_path`
- `feature_manifest_path`
- `model_config_path`
- `metrics`
- `baseline_comparison`
- `reproducibility`
- `promotion_assessment`

Expected shape:

```json
{
  "schema_version": "1.0",
  "artifact_type": "quantlab.learned_model.training_summary",
  "model_run_id": "model_20260421_001",
  "status": "completed",
  "started_at": "2026-04-21T00:00:00Z",
  "finished_at": "2026-04-21T00:00:00Z",
  "duration_seconds": 0,
  "dataset_manifest_path": "dataset_manifest.json",
  "feature_manifest_path": "feature_manifest.json",
  "model_config_path": "model_config.json",
  "metrics": {
    "train": {},
    "validation": {},
    "test": {},
    "downstream_market": {}
  },
  "baseline_comparison": {
    "required": true,
    "rule_based_baseline": null,
    "classical_ml_baseline": null,
    "result": "not_comparable_yet"
  },
  "reproducibility": {
    "random_seed": 42,
    "code_version": "",
    "data_hash": "",
    "feature_hash": ""
  },
  "promotion_assessment": {
    "eligible_for_paper": false,
    "blocking_reasons": [
      "N.0 defines contracts only; no learned-model promotion is allowed."
    ]
  }
}
```

## Evaluation Discipline

Learned-model experiments must use temporal validation by default.

Minimum requirements:

- train, validation, and test splits must be explicit
- validation and test periods must occur after the train period
- random seeds must be recorded
- data source and dataset hash must be recorded
- feature set and feature hash must be recorded
- target definition and prediction horizon must be explicit
- headline predictive metrics are insufficient without downstream market evaluation
- learned models must be compared against rule-based and classical ML baselines before any promotion claim

## Leakage Rules

The contract must make leakage review possible.

Minimum leakage guards:

- no feature may use future values relative to the prediction timestamp
- normalization must be fitted on train data only unless explicitly justified
- target construction must be separated from feature construction
- temporal split windows must be preserved in artifacts
- any rolling retraining policy must be explicit before it is used

## Relationship to `report.json`

Existing run-producing workflows use `outputs/runs/<run_id>/report.json` as the canonical public artifact.

Learned-model experiments should not replace that contract.

For N.0:

- learned-model artifacts live under `outputs/model_runs/<model_run_id>/`
- `training_summary.json` is the primary learned-model summary artifact
- future downstream strategy/backtest evaluation may produce normal QuantLab `report.json` artifacts
- any model-to-strategy conversion must create reviewable intermediate artifacts before it can affect paper or execution paths

## Non-Promotion Rules

No learned model can be promoted to paper mode unless all of the following are true:

- dataset and feature manifests exist
- model configuration and random seed are recorded
- temporal train/validation/test splits are explicit
- leakage checks are reviewable
- rule-based baseline comparison exists
- classical ML baseline comparison exists when N.1 is available
- downstream market metrics are evaluated, not just predictive metrics
- model outputs are translated into reviewable strategy or execution hypotheses
- paper, broker, safety, and supervised execution gates remain intact

No learned model may:

- become an `ExecutionIntent` directly from raw prediction scores
- bypass paper trading
- bypass broker safety preflight
- bypass operator review
- weaken the supervised execution roadmap

## Out of Scope for N.0

This contract does not implement:

- PyTorch
- TensorFlow
- scikit-learn baselines
- model training loops
- checkpoint persistence
- model registry
- model serving
- live inference
- paper promotion for learned models
- Stepbit orchestration of training workflows
- Quant Pulse feature ingestion

## Future Stages

This document enables later stages, but does not implement them:

- N.1 - classical ML baselines
- N.2 - simple neural baselines
- N.3 - temporal validation and market realism
- N.4 - model-to-strategy translation
- N.5 - paper promotion for learned models
- N.6 - orchestrated learned-model research

Each future stage must preserve QuantLab's authority over evidence, artifacts, and promotion discipline.
