import os
import pandas as pd
from pathlib import Path
from core.data_loader import load_csv


class DatasetRegistry:

    def __init__(self, data_dir: str = "data"):
        self.data_dir = Path(data_dir)

    def list_datasets(self) -> list[str]:
        """Return names of all CSV files in the data directory."""
        if not self.data_dir.exists():
            return []
        return [
            f.name for f in self.data_dir.iterdir()
            if f.suffix.lower() == ".csv"
        ]

    def load(self, filename: str):
        """Load a dataset by filename. Returns LoadResult."""
        path = self.data_dir / filename
        if not path.exists():
            from core.data_loader import LoadResult
            return LoadResult(
                success=False,
                error=f"Dataset '{filename}' not found in {self.data_dir}"
            )
        return load_csv(str(path))

    def dataset_path(self, filename: str) -> Path:
        return self.data_dir / filename