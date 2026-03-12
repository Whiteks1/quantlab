import csv
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

class RunRegistry:
    """
    Manage the global/central registry of all runs.
    """
    DEFAULT_COLUMNS = (
    "run_id",
    "created_at",
    "mode",
    "strategy",
    "ticker",
    "start_date",
    "end_date",
    "status",
    "total_return",
    "sharpe",
    "max_drawdown",
    "trades",
    "win_rate",
    "tags",
)
    
    def __init__(self, registry_path: str = "outputs/runs/registry.csv"):
        self.registry_path = Path(registry_path)
        
    def append_run(self, summary: Dict[str, Any]) -> None:
        """
        Append a run summary to the registry CSV. 
        Creates the file and header if it doesn't exist.
        """
        # Ensure directory exists
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_exists = self.registry_path.exists()
        
        with open(self.registry_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=self.DEFAULT_COLUMNS, extrasaction="ignore")
            
            if not file_exists:
                writer.writeheader()
                
            # Fill missing required columns with None to avoid errors
            row = {col: summary.get(col) for col in self.DEFAULT_COLUMNS}
            writer.writerow(row)
            
    def get_all_runs(self) -> List[Dict[str, Any]]:
        """Return all runs in the registry as a list of dicts."""
        if not self.registry_path.exists():
            return []
            
        with open(self.registry_path, "r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            return list(reader)
