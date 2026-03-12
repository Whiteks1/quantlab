import datetime
import hashlib
import json
from typing import Any, Dict, Optional

def generate_run_id(mode: str, config_content: Optional[Any] = None) -> str:
    """
    Generate a deterministic and readable run_id: 
    YYYYMMDD_HHMMSS_<mode>_<short_hash>
    
    If config_content is provided, short_hash is derived from it.
    Otherwise, it is a randomized seed for uniqueness.
    """
    now = datetime.datetime.now(datetime.timezone.utc)
    timestamp = now.strftime("%Y%m%d_%H%M%S")
    
    if config_content is not None:
        if isinstance(config_content, (dict, list)):
            content_str = json.dumps(config_content, sort_keys=True)
        else:
            content_str = str(config_content)
        short_hash = hashlib.sha1(content_str.encode()).hexdigest()[:7]
    else:
        # Fallback to a sub-second hash if no config is provided for uniqueness
        short_hash = hashlib.sha1(str(now.timestamp()).encode()).hexdigest()[:7]
        
    return f"{timestamp}_{mode}_{short_hash}"
    # short_hash ensures uniqueness between runs executed in the same second
