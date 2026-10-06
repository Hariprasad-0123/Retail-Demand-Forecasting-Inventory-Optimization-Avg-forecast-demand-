from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class ReplenishmentRecommendation:
    forecast_demand: float
    current_inventory: float
    safety_stock: float
    reorder_point: float
    recommended_order_qty: float
    coverage_days: float


def calculate_reorder_point(lead_time_days: int, daily_demand: float, service_level: float = 1.65) -> float:
    demand_variability = max(daily_demand * 0.2, 1.0)
    safety_stock = service_level * demand_variability * (lead_time_days ** 0.5)
    reorder_point = (daily_demand * lead_time_days) + safety_stock
    return reorder_point


def suggest_replenishment(forecast_demand: float, current_inventory: float, lead_time_days: int = 7) -> ReplenishmentRecommendation:
    daily_demand = max(forecast_demand / 30.0, 0.1)
    reorder_point = calculate_reorder_point(lead_time_days, daily_demand)
    safety_stock = max(reorder_point - (daily_demand * lead_time_days), 0.0)
    recommended_order_qty = max((reorder_point - current_inventory) + (forecast_demand * 0.25), 0.0)
    coverage_days = (current_inventory / daily_demand) if daily_demand > 0 else 0.0
    return ReplenishmentRecommendation(
        forecast_demand=forecast_demand,
        current_inventory=current_inventory,
        safety_stock=safety_stock,
        reorder_point=reorder_point,
        recommended_order_qty=recommended_order_qty,
        coverage_days=coverage_days,
    )


def build_inventory_table(forecast_df: pd.DataFrame) -> pd.DataFrame:
    inventory_df = forecast_df.copy()
    inventory_df["recommended_order_qty"] = inventory_df.apply(
        lambda row: suggest_replenishment(row["forecast_demand"], row.get("current_inventory", 0.0)).recommended_order_qty,
        axis=1,
    )
    inventory_df["reorder_point"] = inventory_df.apply(
        lambda row: suggest_replenishment(row["forecast_demand"], row.get("current_inventory", 0.0)).reorder_point,
        axis=1,
    )
    return inventory_df
