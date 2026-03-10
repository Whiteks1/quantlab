import json
import math
import datetime
from typing import Any, Dict, List, Union

def _sanitize_value(obj: Any) -> Any:
    """
    Recursively convert non-finite floats (NaN, Inf) to None.
    Converts datetime objects to ISO strings.
    """
    if isinstance(obj, dict):
        return {str(k): _sanitize_value(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_sanitize_value(x) for x in obj]
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            return None
    elif isinstance(obj, (datetime.date, datetime.datetime)):
        return obj.isoformat()
    return obj

def to_json(obj: Any, indent: int = 2) -> str:
    """
    Serialize object to a JSON string with deterministic key ordering and
    handling of non-finite floats and datetimes.
    """
    sanitized = _sanitize_value(obj)
    return json.dumps(
        sanitized,
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
        allow_nan=False
    )

def save_json(obj: Any, path: Any) -> None:
    """
    Serialize object and save to a file path.
    """
    content = to_json(obj)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
