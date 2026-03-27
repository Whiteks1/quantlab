from __future__ import annotations

from pathlib import Path

from quantlab.errors import ConfigError
from quantlab.pretrade import (
    build_quantlab_handoff_validation,
    load_quantlab_handoff_artifact,
    write_quantlab_handoff_validation,
)


def handle_pretrade_handoff_commands(args) -> dict[str, object] | bool:
    source_path_value = getattr(args, "pretrade_handoff_validate", None)
    if not source_path_value:
        return False

    source_path = Path(source_path_value).resolve()
    payload = load_quantlab_handoff_artifact(source_path)
    validation = build_quantlab_handoff_validation(
        payload,
        source_artifact_path=source_path,
    )

    outdir_value = getattr(args, "pretrade_handoff_validation_outdir", None)
    outdir = Path(outdir_value).resolve() if isinstance(outdir_value, str) and outdir_value.strip() else source_path.parent
    artifact_path = write_quantlab_handoff_validation(validation, outdir=outdir)

    print("\nPre-trade handoff validation completed:\n")
    print(f"  source_artifact_path          : {source_path}")
    print(f"  validation_artifact_path      : {artifact_path}")
    print(f"  accepted                      : {validation['accepted']}")
    print(
        f"  ready_for_draft_execution     : "
        f"{validation['quantlab_boundary']['ready_for_draft_execution_intent']}"
    )
    print(f"  symbol                        : {validation['pretrade_context']['symbol']}")
    print(f"  venue                         : {validation['pretrade_context']['venue']}")
    print(f"  side                          : {validation['pretrade_context']['side']}")

    if not validation["accepted"]:
        reasons = ", ".join(validation["reasons"]) or "unknown_validation_error"
        raise ConfigError(
            "Pre-trade handoff validation failed. "
            f"Reasons: {reasons}. Validation artifact: {artifact_path}"
        )

    return {
        "status": "success",
        "mode": "pretrade_handoff",
        "artifact_path": str(artifact_path),
        "accepted": validation["accepted"],
        "handoff_id": validation["handoff_contract"]["handoff_id"],
        "ready_for_draft_execution_intent": validation["quantlab_boundary"][
            "ready_for_draft_execution_intent"
        ],
        "symbol": validation["pretrade_context"]["symbol"],
        "venue": validation["pretrade_context"]["venue"],
        "side": validation["pretrade_context"]["side"],
    }
