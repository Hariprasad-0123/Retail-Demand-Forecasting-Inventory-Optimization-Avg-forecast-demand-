from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from .config import SETTINGS

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


REQUIRED_FILES = {
    "calendar.csv",
    "sell_prices.csv",
    "sales_train_validation.csv",
}


def generate_demo_m5_data(raw_dir: Path) -> dict[str, pd.DataFrame]:
    """Create a lightweight M5-like sample dataset so the project can run without Kaggle downloads."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    dates = pd.date_range("2019-01-01", "2020-12-31", freq="D")
    stores = [f"CA_{i}" for i in range(1, 4)]
    departments = ["FOODS_1", "HOUSEHOLD_1", "HOBBIES_1"]
    items = [f"{dept}_{i:03d}" for dept in departments for i in range(1, 6)]

    calendar = pd.DataFrame({
        "date": dates,
        "d": range(1, len(dates) + 1),
        "wm_yr_wk": dates.strftime("%Y%W").str.replace("0", "", regex=False),
        "weekday": dates.day_name(),
        "wday": dates.weekday,
        "month": dates.month,
        "year": dates.year,
    })
    calendar["wm_yr_wk"] = calendar["wm_yr_wk"].astype(str)
    calendar["event_name_1"] = ""
    calendar["event_type_1"] = ""
    calendar["event_name_2"] = ""
    calendar["event_type_2"] = ""

    sell_prices = []
    for store in stores:
        for item in items:
            base = 2.0 + (hash(item) % 30) / 10.0
            for week in sorted(calendar["wm_yr_wk"].unique()[:50]):
                sell_prices.append({
                    "store_id": store,
                    "item_id": item,
                    "wm_yr_wk": week,
                    "sell_price": round(base * (1 + (hash(week + item) % 9) / 100.0), 2),
                })
    sell_prices_df = pd.DataFrame(sell_prices)

    rows = []
    for store in stores:
        for item in items:
            seasonal = 1 + 0.5 * ((pd.Series(pd.date_range("2019-01-01", periods=len(dates), freq="D")).dt.dayofyear / 365.0).values)
            trend = 1 + 0.1 * (pd.Series(range(len(dates))).values / len(dates))
            day_effect = 1 + (pd.Series(range(len(dates))).values % 7 == 5).astype(float) * 0.25
            base_demand = (seasonal * trend * day_effect) * (0.8 + (hash(f"{store}-{item}") % 100) / 250.0)
            for idx, date in enumerate(dates):
                demand = max(0, round(float(base_demand[idx]) * (1 + (idx % 12) / 30.0)))
                rows.append({
                    "id": f"{store}_{item}_validation",
                    "item_id": item,
                    "dept_id": item.split("_")[0],
                    "cat_id": item.split("_")[0],
                    "store_id": store,
                    "state_id": store.split("_")[0],
                    "d": idx + 1,
                    "sales": demand,
                    "date": date,
                })

    sales = pd.DataFrame(rows)
    sales = sales.pivot_table(index=["id", "item_id", "dept_id", "cat_id", "store_id", "state_id"], columns="d", values="sales", aggfunc="sum").reset_index()
    sales.columns = [col if not isinstance(col, int) else f"d_{col}" for col in sales.columns]
    sales = sales.rename(columns={"index": "id"}) if "index" in sales.columns else sales

    calendar.to_csv(raw_dir / "calendar.csv", index=False)
    sell_prices_df.to_csv(raw_dir / "sell_prices.csv", index=False)
    sales.to_csv(raw_dir / "sales_train_validation.csv", index=False)
    return {
        "calendar": calendar,
        "sell_prices": sell_prices_df,
        "sales": sales,
    }


def ensure_raw_data() -> None:
    raw_dir = Path(SETTINGS.raw_data_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)

    required_present = all((raw_dir / name).exists() for name in REQUIRED_FILES)
    if not required_present:
        logger.warning("Missing M5 files in %s. Creating synthetic demo dataset for local pipeline execution.", raw_dir)
        generate_demo_m5_data(raw_dir)

    calendar_path = raw_dir / "calendar.csv"
    if calendar_path.exists():
        calendar = pd.read_csv(calendar_path)
        if "d" not in calendar.columns:
            logger.warning("Calendar payload missing M5 'd' column. Regenerating synthetic demo dataset.")
            generate_demo_m5_data(raw_dir)

    for filename in REQUIRED_FILES:
        if not (raw_dir / filename).exists():
            raise FileNotFoundError(f"Missing required file: {raw_dir / filename}")
    logger.info("Validated raw data files in %s", raw_dir)


def load_raw_data() -> dict[str, pd.DataFrame]:
    ensure_raw_data()
    raw_dir = Path(SETTINGS.raw_data_dir)
    data = {
        "calendar": pd.read_csv(raw_dir / "calendar.csv"),
        "sell_prices": pd.read_csv(raw_dir / "sell_prices.csv"),
        "sales": pd.read_csv(raw_dir / "sales_train_validation.csv"),
    }
    return data


def clean_dataframes(data: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
    logger.info("Normalizing date columns and numeric fields.")

    calendar = data["calendar"].copy()
    sell_prices = data["sell_prices"].copy()
    sales = data["sales"].copy()

    if "d" not in calendar.columns:
        calendar["d"] = range(1, len(calendar) + 1)

    calendar["date"] = pd.to_datetime(calendar["date"], errors="coerce")
    calendar["wm_yr_wk"] = pd.to_numeric(calendar["wm_yr_wk"], errors="coerce")
    calendar["d"] = pd.to_numeric(calendar["d"], errors="coerce")
    calendar["event_name_1"] = calendar["event_name_1"].fillna("")
    calendar["event_type_1"] = calendar["event_type_1"].fillna("")
    calendar["event_name_2"] = calendar["event_name_2"].fillna("")
    calendar["event_type_2"] = calendar["event_type_2"].fillna("")

    sales_columns = [col for col in sales.columns if col.startswith("d_")]
    if not sales_columns:
        raise ValueError("The sales dataset doesn't include numeric day columns in the expected M5 format.")
    id_cols = [col for col in sales.columns if col not in sales_columns]
    sales_melt = sales.melt(id_vars=id_cols, value_vars=sales_columns, var_name="d", value_name="sales")
    sales_melt["d"] = sales_melt["d"].str.replace("d_", "", regex=False).astype(int)
    sales_melt["sales"] = pd.to_numeric(sales_melt["sales"], errors="coerce").fillna(0)

    sell_prices["wm_yr_wk"] = pd.to_numeric(sell_prices["wm_yr_wk"], errors="coerce")
    sell_prices["sell_price"] = pd.to_numeric(sell_prices["sell_price"], errors="coerce")

    sales_features = sales_melt.merge(calendar[["date", "wm_yr_wk", "weekday", "wday", "month", "year", "d"]], on="d", how="left")
    sales_features = sales_features.merge(sell_prices, on=["store_id", "item_id", "wm_yr_wk"], how="left")
    sales_features["sell_price"] = sales_features["sell_price"].fillna(0)
    sales_features["sales"] = sales_features["sales"].clip(lower=0)

    return {
        "calendar": calendar,
        "sell_prices": sell_prices,
        "sales": sales_features,
    }


def save_processed_data(data: dict[str, pd.DataFrame]) -> None:
    out_dir = Path(SETTINGS.processed_data_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for name, df in data.items():
        out_path = out_dir / f"{name}.parquet"
        df.to_parquet(out_path, index=False)
        logger.info("Saved processed dataset to %s", out_path)


def main() -> None:
    raw_data = load_raw_data()
    cleaned = clean_dataframes(raw_data)
    save_processed_data(cleaned)
    logger.info("ETL pipeline completed successfully.")


if __name__ == "__main__":
    main()
