"""
Broker-facing boundary package for future real execution work.

This package intentionally starts small in Stage D.0:
- broker-agnostic adapter contract
- execution intent model
- local safety policy and preflight validation
"""

from .boundary import (
    BrokerAdapter,
    ExecutionContext,
    ExecutionIntent,
    ExecutionPolicy,
    ExecutionPreflight,
    validate_execution_intent,
)
from .hyperliquid import (
    HyperliquidAccountReadinessReport,
    HyperliquidBrokerAdapter,
    HyperliquidPreflightReport,
    HyperliquidResolvedExecutionContext,
    HyperliquidSignedActionReport,
)
from .kraken import (
    KrakenAccountSnapshotReport,
    KrakenAuthPreflightReport,
    KrakenBalanceEntry,
    KrakenBrokerAdapter,
    KrakenDryRunAudit,
    KrakenIntentReadiness,
    KrakenOrderReconciliationReport,
    KrakenOrderStatusReport,
    KrakenOrderSubmitReport,
    KrakenOrderValidateReport,
    KrakenPreflightReport,
)

__all__ = [
    "BrokerAdapter",
    "ExecutionContext",
    "ExecutionIntent",
    "ExecutionPolicy",
    "ExecutionPreflight",
    "HyperliquidAccountReadinessReport",
    "HyperliquidBrokerAdapter",
    "HyperliquidPreflightReport",
    "HyperliquidResolvedExecutionContext",
    "HyperliquidSignedActionReport",
    "KrakenAccountSnapshotReport",
    "KrakenBrokerAdapter",
    "KrakenAuthPreflightReport",
    "KrakenBalanceEntry",
    "KrakenDryRunAudit",
    "KrakenIntentReadiness",
    "KrakenOrderReconciliationReport",
    "KrakenOrderStatusReport",
    "KrakenOrderSubmitReport",
    "KrakenOrderValidateReport",
    "KrakenPreflightReport",
    "validate_execution_intent",
]
