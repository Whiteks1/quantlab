"""
errors.py — Centralized exception hierarchy for QuantLab.
Defines base and specific errors used to communicate failures to callers (e.g. CLI, Stepbit).
"""

class QuantLabError(Exception):
    """Base exception for all known QuantLab failures."""
    pass

class ConfigError(QuantLabError):
    """Raised when CLI arguments or JSON request parameters are invalid."""
    pass

class DataError(QuantLabError):
    """Raised when market data is missing, empty, or structurally invalid."""
    pass

class StrategyError(QuantLabError):
    """Raised when strategy logic fails, parameters are out of bounds, or simulation crashes."""
    pass
