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
from .kraken import KrakenBrokerAdapter, KrakenDryRunAudit, KrakenPreflightReport

__all__ = [
    "BrokerAdapter",
    "ExecutionIntent",
    "ExecutionPolicy",
    "ExecutionPreflight",
    "KrakenBrokerAdapter",
    "KrakenDryRunAudit",
    "KrakenPreflightReport",
    "validate_execution_intent",
]
