from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv

load_dotenv()

WarehouseType = Literal["bigquery", "snowflake"]


@dataclass(frozen=True)
class Settings:
    warehouse_type: WarehouseType = os.getenv("WAREHOUSE_TYPE", "bigquery")  # type: ignore[assignment]
    project_id: str = os.getenv("PROJECT_ID", "demo-project")
    dataset_id: str = os.getenv("DATASET_ID", "retail_demand")
    raw_data_dir: Path = Path(os.getenv("M5_DATA_DIR", "./data/raw"))
    processed_data_dir: Path = Path(os.getenv("PROCESSED_DATA_DIR", "./data/processed"))
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    @property
    def warehouse(self) -> WarehouseType:
        w = self.warehouse_type.lower()
        if w not in {"bigquery", "snowflake"}:
            raise ValueError(f"Unsupported warehouse type: {self.warehouse_type}")
        return w


SETTINGS = Settings()
