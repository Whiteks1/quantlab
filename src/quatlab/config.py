from dataclasses import dataclass
import os

@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade: float = float(os.getenv("RISK_PER_TRADE", "0.01"))

@dataclass(frozen=True)
class AppConfig:
    execution_mode: str = os.getenv("EXECUTION_MODE", "paper")  # paper/live
    risk: RiskConfig = RiskConfig()