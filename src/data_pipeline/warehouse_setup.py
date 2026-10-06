from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def get_warehouse_config() -> dict:
    warehouse_type = os.getenv("WAREHOUSE_TYPE", "bigquery").lower()
    if warehouse_type == "bigquery":
        return {
            "type": "bigquery",
            "project": os.getenv("PROJECT_ID", "demo-project"),
            "dataset": os.getenv("DATASET_ID", "retail_demand"),
        }
    if warehouse_type == "snowflake":
        return {
            "type": "snowflake",
            "account": os.getenv("SNOWFLAKE_ACCOUNT", "demo-account"),
            "user": os.getenv("SNOWFLAKE_USER", "demo-user"),
            "password": os.getenv("SNOWFLAKE_PASSWORD", "demo-password"),
            "database": os.getenv("SNOWFLAKE_DATABASE", "retail_demand"),
            "schema": os.getenv("SNOWFLAKE_SCHEMA", "analytics"),
            "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE", "compute_wh"),
        }
    raise ValueError(f"Unsupported warehouse type: {warehouse_type}")


def ensure_directory(path: str | Path) -> Path:
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


if __name__ == "__main__":
    print(get_warehouse_config())
