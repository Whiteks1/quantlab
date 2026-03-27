from __future__ import annotations

import json
import types

import pytest

from quantlab.cli.pretrade import handle_pretrade_commands
from quantlab.errors import ConfigError
from quantlab.pretrade.artifacts import (
    PRETRADE_EXECUTION_BRIDGE_FILENAME,
    PRETRADE_INPUT_FILENAME,
    PRETRADE_PLAN_FILENAME,
    PRETRADE_SUMMARY_FILENAME,
)
from quantlab.pretrade.bridge import build_execution_policy, build_pretrade_execution_bridge
from quantlab.pretrade.calculator import build_pretrade_plan
from quantlab.pretrade.models import PretradeRequest


def _make_args(**kwargs):
    defaults = {
        "pretrade_plan": False,
        "pretrade_sessions_root": None,
        "pretrade_session_id": None,
        "pretrade_symbol": None,
        "pretrade_venue": None,
        "pretrade_side": None,
        "pretrade_capital": None,
        "pretrade_risk_percent": None,
        "pretrade_entry_price": None,
        "pretrade_stop_price": None,
        "pretrade_target_price": None,
        "pretrade_estimated_fees": 0.0,
        "pretrade_estimated_slippage": 0.0,
        "pretrade_account_id": None,
        "pretrade_strategy_id": None,
        "pretrade_notes": None,
        "pretrade_bridge_to_execution": False,
        "pretrade_broker_target": None,
        "pretrade_policy_max_notional": None,
        "pretrade_policy_allowed_symbols": None,
        "pretrade_policy_kill_switch": False,
        "pretrade_policy_allow_missing_account_id": False,
        "pretrade_execution_request_id": None,
    }
    defaults.update(kwargs)
    return types.SimpleNamespace(**defaults)


def test_build_pretrade_plan_buy_side():
    request = PretradeRequest(
        symbol="ETH-USD",
        venue="demo",
        side="buy",
        capital=1000.0,
        risk_percent=1.0,
        entry_price=2000.0,
        stop_price=1950.0,
        target_price=2100.0,
        estimated_fees=1.0,
        estimated_slippage=0.5,
        session_id="demo_pretrade_case",
    )

    plan = build_pretrade_plan(request)

    assert plan.session_id == "demo_pretrade_case"
    assert plan.risk_amount == pytest.approx(10.0)
    assert plan.position_size == pytest.approx(0.2)
    assert plan.notional == pytest.approx(400.0)
    assert plan.max_loss_at_stop == pytest.approx(11.5)
    assert plan.net_profit_at_target == pytest.approx(18.5)
    assert plan.risk_reward_ratio == pytest.approx(18.5 / 11.5)


def test_handle_pretrade_commands_writes_artifacts(tmp_path, capsys):
    args = _make_args(
        pretrade_plan=True,
        pretrade_sessions_root=str(tmp_path),
        pretrade_session_id="session_demo_001",
        pretrade_symbol="BTC-USD",
        pretrade_venue="paper_demo",
        pretrade_side="long",
        pretrade_capital=5000.0,
        pretrade_risk_percent=2.0,
        pretrade_entry_price=100000.0,
        pretrade_stop_price=98000.0,
        pretrade_target_price=104000.0,
        pretrade_estimated_fees=5.0,
        pretrade_estimated_slippage=2.0,
    )

    result = handle_pretrade_commands(args, project_root=tmp_path)

    assert isinstance(result, dict)
    session_dir = tmp_path / "session_demo_001"
    assert session_dir.exists()
    assert (session_dir / PRETRADE_INPUT_FILENAME).exists()
    assert (session_dir / PRETRADE_PLAN_FILENAME).exists()
    assert (session_dir / PRETRADE_SUMMARY_FILENAME).exists()
    assert (session_dir / "plan.md").exists()

    plan_payload = json.loads((session_dir / PRETRADE_PLAN_FILENAME).read_text(encoding="utf-8"))
    assert plan_payload["machine_contract"]["contract_type"] == "quantlab.pretrade.plan"
    assert plan_payload["request"]["side"] == "buy"
    assert plan_payload["policy_checks"]["accepted"] is True

    output = capsys.readouterr().out
    assert "Pre-trade plan created" in output
    assert "session_demo_001" in output


def test_build_pretrade_execution_bridge_rejects_missing_account():
    request = PretradeRequest(
        symbol="ETH-USD",
        venue="demo",
        side="buy",
        capital=1000.0,
        risk_percent=1.0,
        entry_price=2000.0,
        stop_price=1950.0,
        target_price=2100.0,
        session_id="bridge_case_001",
    )
    plan = build_pretrade_plan(request)
    policy = build_execution_policy(max_notional_per_order=1000.0)

    bridge = build_pretrade_execution_bridge(
        plan,
        broker_target="kraken",
        policy=policy,
    )

    assert bridge.execution_preflight.allowed is False
    assert "missing_account_id" in bridge.execution_preflight.reasons


def test_handle_pretrade_commands_writes_execution_bridge(tmp_path):
    args = _make_args(
        pretrade_plan=True,
        pretrade_sessions_root=str(tmp_path),
        pretrade_session_id="session_bridge_001",
        pretrade_symbol="ETH-USD",
        pretrade_venue="kraken",
        pretrade_side="buy",
        pretrade_capital=1000.0,
        pretrade_risk_percent=1.0,
        pretrade_entry_price=2000.0,
        pretrade_stop_price=1950.0,
        pretrade_target_price=2100.0,
        pretrade_account_id="account_demo_001",
        pretrade_bridge_to_execution=True,
        pretrade_broker_target="kraken",
        pretrade_policy_max_notional=1000.0,
        pretrade_policy_allowed_symbols="ETH-USD,BTC-USD",
        pretrade_execution_request_id="req_bridge_001",
    )

    result = handle_pretrade_commands(args, project_root=tmp_path)

    session_dir = tmp_path / "session_bridge_001"
    bridge_path = session_dir / PRETRADE_EXECUTION_BRIDGE_FILENAME
    assert bridge_path.exists()
    bridge_payload = json.loads(bridge_path.read_text(encoding="utf-8"))
    assert bridge_payload["execution_preflight"]["allowed"] is True
    assert bridge_payload["draft_execution_intent"]["broker_target"] == "kraken"
    assert bridge_payload["draft_execution_intent"]["request_id"] == "req_bridge_001"
    assert result["pretrade_execution_bridge_path"] == str(bridge_path)


def test_handle_pretrade_commands_rejects_invalid_setup(tmp_path):
    args = _make_args(
        pretrade_plan=True,
        pretrade_sessions_root=str(tmp_path),
        pretrade_symbol="ETH-USD",
        pretrade_venue="demo",
        pretrade_side="buy",
        pretrade_capital=1000.0,
        pretrade_risk_percent=1.0,
        pretrade_entry_price=2000.0,
        pretrade_stop_price=2050.0,
    )

    with pytest.raises(ConfigError):
        handle_pretrade_commands(args, project_root=tmp_path)
