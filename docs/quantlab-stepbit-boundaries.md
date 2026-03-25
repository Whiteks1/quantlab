# QuantLab × Stepbit: Boundaries And Integration Principles

This document defines the intended architectural relationship between QuantLab and Stepbit.

Its purpose is to remove ambiguity about authority, ownership, and integration scope.

## Core Decision

The authoritative design is:

- QuantLab is autonomous
- Stepbit does not govern QuantLab
- Stepbit is not the control plane of QuantLab
- QuantLab may consume AI capabilities from Stepbit
- the connection between both systems is optional and reversible
- the QuantLab MCP surface exists to expose a clean integration boundary, not to cede operational authority

## Authority Model

The correct relationship is:

```text
QuantLab -> consumes -> Stepbit capabilities
```

or, at the system level:

```text
QuantLab <-> Stepbit
```

with a strict authority rule:

- functional authority over QuantLab lives in QuantLab
- Stepbit provides external services and cognitive capabilities
- if Stepbit is unavailable, QuantLab must still make sense and remain useful on its own

## QuantLab-First Principle

QuantLab remains the primary product in its own domain.

That means its roadmap is not subordinated to Stepbit.

QuantLab should continue to evolve according to its own priorities, including:

- research reliability
- paper-trading discipline
- execution safety
- broker dry-run integration
- supervised live trading
- controlled automation

## Role Of Stepbit

Stepbit is an optional augmentation layer.

It can add value through:

- reasoning-assisted analysis
- workflow automation
- interpretation of research outputs
- intelligent task proposals
- MCP-based querying and interaction

It must not become the sovereign owner of QuantLab's internal behavior.

## Integration Rule

The integration must be:

- useful
- reversible
- contract-based
- narrow at the boundary
- non-constitutive of QuantLab's identity

If Stepbit disappears, QuantLab should still remain a coherent research, paper-trading, and future execution system.

## MCP Design Principle

The MCP surface should be treated as a boundary interface, not an invasion channel.

### Good MCP responsibilities

- execute well-scoped QuantLab actions
- expose run artifacts and reports
- return machine-readable contracts
- support external analysis of QuantLab outputs
- provide access to stable health and execution surfaces

### Bad MCP responsibilities

- owning QuantLab's internal session lifecycle
- owning QuantLab's risk policy
- relocating QuantLab's core trading logic into Stepbit
- controlling strategy promotion as a sovereign external authority
- turning Stepbit into the runtime owner of QuantLab

## Roadmap Consequence

Because QuantLab is sovereign, the main roadmap priority should remain inside QuantLab itself.

That means:

- the next primary QuantLab stage is `Stage C.1 - Paper Trading Operationalization`
- `Stage O.1 - Integration Hardening` is secondary and reactive
- integration work should only drive QuantLab-side changes when it improves the boundary without compromising autonomy

## Golden Rules

Two compact rules define the relationship:

> Stepbit can amplify QuantLab, but not define it.

> The integration must be useful, reversible, and not constitutive.

## Practical Decision Framework

When deciding whether a change belongs in QuantLab:

- accept it if it improves QuantLab directly
- accept it if it improves the external integration boundary without compromising QuantLab autonomy
- reject or isolate it if it exists only to make QuantLab subordinate to Stepbit

When deciding whether a capability belongs in Stepbit:

- place it in Stepbit if it is optional AI augmentation, orchestration, reasoning, or external workflow support
- do not move it there if it is core trading logic, risk authority, or internal operational ownership of QuantLab
