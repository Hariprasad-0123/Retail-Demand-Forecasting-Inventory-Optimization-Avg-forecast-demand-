from __future__ import annotations

from src.data_pipeline.m5_etl import main as run_etl
from src.forecasting.forecast_models import main as run_forecast


if __name__ == "__main__":
    run_etl()
    run_forecast()
    print("Retail demand forecasting pipeline completed.")
