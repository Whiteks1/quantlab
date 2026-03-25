"""
Broker-facing boundary package for future real execution work.

This package intentionally starts small in Stage D.0:
- broker-agnostic adapter contract
- execution intent model
- local safety policy and preflight validation
"""

from .boundary import (
    BrokerAdapter,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)
from .kraken import (
    KrakenAccountSnapshotReport,
    KrakenAuthPreflightReport,
    KrakenBalanceEntry,
    KrakenBrokerAdapter,
    KrakenDryRunAudit,
    KrakenIntentReadiness,
    KrakenOrderValidateReport,
    KrakenPreflightReport,
)

__all__ = [
    "BrokerAdapter",
    "ExecutionIntent",
    "ExecutionPolicy",
    "ExecutionPreflight",
    "KrakenAccountSnapshotReport",
    "KrakenBrokerAdapter",
    "KrakenAuthPreflightReport",
    "KrakenBalanceEntry",
    "KrakenDryRunAudit",
    "KrakenIntentReadiness",
    "KrakenOrderValidateReport",
    "KrakenPreflightReport",
    "validate_execution_intent",
]
