from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.data_pipeline.config import SETTINGS
from src.forecasting.forecast_models import build_prophet_frame, load_processed_data, run_prophet_forecast
from src.inventory.replenishment import suggest_replenishment

st.set_page_config(page_title="Retail Demand Forecasting", layout="wide")


@st.cache_data
def load_dashboard_data():
    df = load_processed_data()
    return df


st.title("Retail Demand Forecasting & Inventory Optimization")

sales_df = load_dashboard_data()

store_options = sorted(sales_df["store_id"].dropna().unique().tolist())
item_options = sorted(sales_df["item_id"].dropna().unique().tolist())

with st.sidebar:
    st.header("Filters")
    selected_store = st.selectbox("Store", options=store_options)
    selected_item = st.selectbox("Item", options=item_options)
    forecast_days = st.slider("Forecast horizon (days)", 7, 90, 30)
    price_drop = st.slider("Simulated price drop (%)", 0, 25, 0)

filtered = sales_df[(sales_df["store_id"] == selected_store) & (sales_df["item_id"] == selected_item)]
prophet_df = build_prophet_frame(filtered)
forecast = run_prophet_forecast(prophet_df, periods=forecast_days)

if not forecast.empty:
    forecast["adjusted_yhat"] = forecast["yhat"] * (1 - (price_drop / 100.0))
    recommendation = suggest_replenishment(float(forecast["adjusted_yhat"].mean()), float(filtered["sales"].sum() * 0.2))
else:
    recommendation = suggest_replenishment(0.0, 0.0)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Avg forecast demand", f"{forecast['adjusted_yhat'].mean():,.1f}")
col2.metric("Safety stock", f"{recommendation.safety_stock:,.1f}")
col3.metric("Reorder point", f"{recommendation.reorder_point:,.1f}")
col4.metric("Recommended order qty", f"{recommendation.recommended_order_qty:,.1f}")

st.subheader("30-day demand forecast")
st.line_chart(forecast.set_index("ds")[["yhat", "adjusted_yhat"]])

st.subheader("Historical sales behavior")
chart_df = filtered[["date", "sales", "sell_price"]].groupby("date", as_index=False).sum()
st.area_chart(chart_df.set_index("date")["sales"])

st.caption("Scenario assumption: price drop modifies demand forecast by reducing demand proportionally.")
