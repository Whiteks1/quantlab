# Supervised Broker Runbook

This runbook explains how to operate QuantLab's current supervised broker corridors as a bounded, artifact-first workflow.

It is intentionally short.

The goal is not to describe every CLI flag.
The goal is to make the current happy path and failure path repeatable for a human operator.

## 1. Operating Rule

QuantLab's current broker work should be treated as:

- supervised
- artifact-first
- conservative
- evidence-producing

It should not be treated as:

- autonomous live trading
- retry-happy execution
- a UI-driven workflow

The key discipline is:

1. build or inspect the local artifact
2. confirm the gate
3. submit once
4. reconcile before acting again

If state becomes ambiguous, stop widening actions and inspect the artifacts already written.

## 2. Promotion Floor Before Broker Work

Before using a broker-facing corridor, the candidate should already have:

- a paper-backed result worth promoting
- a clearly chosen symbol, side, quantity, and notional
- a deliberately small first size
- an operator willing to review the resulting artifacts

Practical rule:

- paper is still the promotion floor
- broker work begins only after the operator is comfortable that the paper result is worth a tightly supervised real-world check

## 2.5. Readiness Check Before The First Evidence Pass

Before attempting the first supervised broker evidence run, generate a readiness artifact:

```bash
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence
```

If you already know which corridor you want to exercise first, make it explicit:

```bash
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence --broker-evidence-corridor kraken
python main.py --broker-evidence-readiness-outdir outputs/broker_evidence --broker-evidence-corridor hyperliquid
```

Use this check to fail early on:

- missing broker credentials
- missing Hyperliquid execution identity inputs
- missing runbook/documentation continuity

The command writes `broker_evidence_readiness.json` even when the corridor is not ready yet.

## 3. Happy Path: Kraken Supervised Corridor

This is the current narrow Kraken path under `outputs/broker_order_validations/`.

### Step 1: create a validation session

```bash
python main.py --kraken-order-validate-session --broker-symbol ETH-USD --broker-side buy --broker-quantity 0.25 --broker-notional 500 --broker-account-id acct_demo
```

This writes a canonical validation session under:

```text
outputs/broker_order_validations/<session_id>/
```

### Step 2: inspect the validation result

```bash
python main.py --broker-order-validations-show outputs/broker_order_validations/<session_id>
```

### Step 3: approve the session locally

```bash
python main.py --broker-order-validations-approve outputs/broker_order_validations/<session_id> --broker-approval-reviewer marce --broker-approval-note "Approved after validate-only review"
```

### Step 4: materialize the pre-submit bundle

```bash
python main.py --broker-order-validations-bundle outputs/broker_order_validations/<session_id>
```

### Step 5: materialize the supervised submit gate

```bash
python main.py --broker-order-validations-submit-gate outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-note "Ready for supervised submit review"
```

### Step 6: perform the first real supervised submit

```bash
python main.py --broker-order-validations-submit-real outputs/broker_order_validations/<session_id> --broker-submit-reviewer marce --broker-submit-confirm --broker-submit-live --broker-submit-note "First supervised live submit"
```

### Step 7: reconcile if needed

```bash
python main.py --broker-order-validations-reconcile outputs/broker_order_validations/<session_id>
```

### Step 8: refresh normalized post-submit status

```bash
python main.py --broker-order-validations-status outputs/broker_order_validations/<session_id>
```

### Step 9: inspect operator pulse over the full root

```bash
python main.py --broker-order-validations-health outputs/broker_order_validations
python main.py --broker-order-validations-alerts outputs/broker_order_validations
```

## 4. Failure Path: Kraken

Stop the corridor at the first failing gate.

### Validation rejected

Meaning:

- the exchange-side validate-only path did not accept the order shape

What to do:

- inspect `broker_order_validate.json`
- adjust size, symbol, side, or account assumptions
- do not approve the session just to continue the flow

### Local approval not granted

Meaning:

- the session is not yet fit for submission

What to do:

- stop
- record the reason in the approval note or session review context
- do not bundle or gate a session that should not pass human review

### Submit becomes ambiguous

Meaning:

- a real submit was attempted but the effective remote state is still unclear

What to do:

1. inspect `broker_submit_response.json`
2. run `--broker-order-validations-reconcile`
3. run `--broker-order-validations-status`
4. inspect `broker_order_status.json`
5. inspect `--broker-order-validations-health` and `--broker-order-validations-alerts`

Do not:

- blindly re-submit
- create a second session just to “try again”
- assume absence of a clean local success message means the exchange never saw the order

## 5. Happy Path: Hyperliquid Supervised Corridor

This is the current narrow Hyperliquid path under `outputs/hyperliquid_submits/`.

### Step 1: preflight and readiness

```bash
python main.py --hyperliquid-preflight-outdir outputs/broker_preflight/hyperliquid_demo --broker-symbol ETH --execution-transport-preference websocket
python main.py --hyperliquid-account-readiness-outdir outputs/broker_preflight/hyperliquid_account_demo --execution-account-id 0x0000000000000000000000000000000000000000
```

### Step 2: build and sign the action locally

```bash
python main.py --hyperliquid-signed-action-outdir outputs/broker_preflight/hyperliquid_signed_action_demo --broker-symbol ETH --broker-side buy --broker-quantity 0.25 --broker-notional 500 --execution-account-id 0x0000000000000000000000000000000000000000 --execution-signer-id 0xSIGNER_ADDRESS --hyperliquid-private-key-env HYPERLIQUID_PRIVATE_KEY
```

### Step 3: create a canonical supervised submit session

```bash
python main.py --hyperliquid-submit-session outputs/broker_preflight/hyperliquid_signed_action_demo/hyperliquid_signed_action.json --hyperliquid-submit-reviewer marce --hyperliquid-submit-confirm --hyperliquid-submit-sessions-root outputs/hyperliquid_submits
```

### Step 4: refresh post-submit visibility

```bash
python main.py --hyperliquid-submit-sessions-status outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-reconcile outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-fills outputs/hyperliquid_submits/<session_id>
python main.py --hyperliquid-submit-sessions-supervise outputs/hyperliquid_submits/<session_id>
```

### Step 5: inspect operator pulse over the full root

```bash
python main.py --hyperliquid-submit-sessions-health outputs/hyperliquid_submits
python main.py --hyperliquid-submit-sessions-alerts outputs/hyperliquid_submits
```

### Step 6: use cancel only as an explicit supervised action

```bash
python main.py --hyperliquid-submit-sessions-cancel outputs/hyperliquid_submits/<session_id> --hyperliquid-cancel-reviewer marce --hyperliquid-cancel-confirm
```

## 6. Failure Path: Hyperliquid

### Readiness or signer mismatch

Meaning:

- the account/signer arrangement is not yet trustworthy for submission

What to do:

- inspect `hyperliquid_account_readiness.json`
- inspect `hyperliquid_signed_action.json`
- stop if `readiness_allowed` is false or if `signature_state` is not `signed`

Do not submit an unsigned or mismatched artifact.

### Post-submit state remains unclear

Meaning:

- the session exists, but the effective lifecycle is still not obvious from a single artifact

What to do:

1. inspect `hyperliquid_submit_response.json`
2. run `--hyperliquid-submit-sessions-status`
3. run `--hyperliquid-submit-sessions-reconcile`
4. run `--hyperliquid-submit-sessions-fills`
5. run `--hyperliquid-submit-sessions-supervise`
6. inspect `--hyperliquid-submit-sessions-health` and `--hyperliquid-submit-sessions-alerts`

Do not:

- generate a second signed action just to “see if it lands”
- treat lack of immediate fill evidence as proof the order is gone
- use cancel until you have inspected the latest session state

## 7. Artifacts Worth Preserving

For a supervised broker run worth keeping, the minimum evidence pack is:

- source paper session id or rationale for promotion
- the first validation or signed-action artifact
- the approval or reviewer identity
- the first submit response artifact
- the latest reconciliation or status artifact
- the latest health and alerts snapshot for the root

This is the minimum useful pack for post-mortem review.

## 8. Minimal Operator Loop

When operating one supervised corridor:

1. choose the smallest realistic candidate worth promoting
2. create the first local broker artifact
3. inspect before approving or submitting
4. submit once
5. reconcile and refresh status before taking any second action
6. read root-level health and alerts
7. keep the artifact pack if the run is worth learning from

## 9. Boundary Notes

- these corridors are still supervised, not autonomous
- the current priority is not adding more surface area, but producing evidence and hardening the exact failure point that appears in real use
- paper, broker, and Hyperliquid surfaces should be treated as one promotion ladder, not as unrelated demos

## 10. Related Documents

- [README.md](../README.md)
- [cli.md](./cli.md)
- [paper-session-runbook.md](./paper-session-runbook.md)
- [broker-safety-boundary.md](./broker-safety-boundary.md)
- [roadmap.md](./roadmap.md)
