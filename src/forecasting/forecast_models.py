from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

try:
    from prophet import Prophet
except Exception:  # pragma: no cover
    Prophet = None

try:
    import lightgbm as lgb
except Exception:  # pragma: no cover
    lgb = None

from src.data_pipeline.config import SETTINGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def load_processed_data() -> pd.DataFrame:
    data_path = Path(SETTINGS.processed_data_dir) / "sales.parquet"
    if not data_path.exists():
        raise FileNotFoundError(f"Processed sales data not found: {data_path}. Run ETL first.")
    return pd.read_parquet(data_path)


def build_prophet_frame(df: pd.DataFrame, item_id: str | None = None, store_id: str | None = None) -> pd.DataFrame:
    frame = df.copy()
    if item_id:
        frame = frame[frame["item_id"] == item_id]
    if store_id:
        frame = frame[frame["store_id"] == store_id]
    frame = frame[["date", "sales"]].rename(columns={"date": "ds", "sales": "y"})
    frame = frame.groupby("ds", as_index=False)["y"].sum()
    frame = frame.sort_values("ds")
    return frame


def run_prophet_forecast(df: pd.DataFrame, periods: int = 30) -> pd.DataFrame:
    if Prophet is None:
        raise ImportError("prophet is not installed. Install requirements.txt before running forecast models.")
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(df)
    future = model.make_future_dataframe(periods=periods, freq="D")
    forecast = model.predict(future)
    return forecast[["ds", "yhat", "yhat_lower", "yhat_upper"]].tail(periods)


def train_lightgbm_model(df: pd.DataFrame) -> dict:
    if lgb is None:
        raise ImportError("lightgbm is not installed. Install requirements.txt before running forecast models.")

    feature_df = df[["date", "sales", "store_id", "item_id", "month", "year", "wday", "sell_price"]].copy()
    feature_df["date"] = pd.to_datetime(feature_df["date"])
    feature_df["day_of_week"] = feature_df["date"].dt.dayofweek
    feature_df["is_weekend"] = feature_df["day_of_week"].isin([5, 6]).astype(int)
    feature_df["date_numeric"] = (feature_df["date"].astype("int64") // 10**9)
    feature_df = pd.get_dummies(feature_df, columns=["store_id", "item_id"], drop_first=True)

    target = feature_df["sales"]
    features = feature_df.drop(columns=["sales", "date"]).fillna(0)

    train_data = lgb.Dataset(features, label=target)
    params = {
        "objective": "regression",
        "metric": "rmse",
        "learning_rate": 0.05,
        "num_leaves": 31,
        "verbose": -1,
    }
    model = lgb.train(params, train_data, num_boost_round=100)
    return {"model": model, "features": features.columns.tolist()}


def main() -> None:
    sales_df = load_processed_data()
    prophet_frame = build_prophet_frame(sales_df)
    prophet_forecast = run_prophet_forecast(prophet_frame)
    logger.info("Prophet forecast sample:\n%s", prophet_forecast.head())

    model_info = train_lightgbm_model(sales_df)
    logger.info("LightGBM feature set: %s", model_info["features"][:10])
    logger.info("Forecasting pipeline executed successfully.")


if __name__ == "__main__":
    main()
