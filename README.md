# Retail Demand Forecasting & Inventory Optimization

This project implements a retail analytics platform for demand forecasting and inventory optimization using the M5 Walmart sales dataset. It includes ETL scripts, dbt transformation models, forecasting pipelines, and a Streamlit dashboard for inventory managers.

## Project goals
- Forecast future demand at the store and department level
- Account for promotions, seasonality, and pricing dynamics
- Generate inventory restocking recommendations using service-level logic
- Expose insights through a dashboard for operations teams

## Tech stack
- Python
- SQL
- dbt
- BigQuery or Snowflake
- Prophet and LightGBM
- Streamlit

## Folder structure
- `src/data_pipeline/` — ETL, schema validation, and raw-to-processed pipeline
- `src/forecasting/` — forecasting models and output generation
- `src/inventory/` — replenishment recommendations
- `src/dashboard/` — Streamlit UI
- `dbt/` — warehouse transformation models
- `data/raw/` — raw M5 CSV files
- `data/processed/` — cleaned processed datasets

## Local setup
1. Create a virtual environment:
   python -m venv .venv
   source .venv/bin/activate
2. Install dependencies:
   pip install -r requirements.txt
3. Copy environment variables:
   cp .env.example .env
4. Download the M5 dataset to `data/raw/`.
5. Run the ETL pipeline:
   python -m src.data_pipeline.m5_etl
6. Run the forecasting models:
   python -m src.forecasting.forecast_models
7. Launch the dashbaord:
   streamlit run src/dashboard/app.py

## Data sources
The primary dataset is the M5 Forecasting Dataset (Walmart historical sales data). The pipeline expects the following files in `data/raw/`:
- `calendar.csv`
- `sell_prices.csv`
- `sales_train_validation.csv`
- `sales_train_evaluation.csv` (optional)
- `sample_submission.csv` (optional)

## Four-week delivery roadmap
### Week 1: Data Architecture & ETL
- Initialize the warehouse connection
- Load raw M5 data into the warehouse or local staged area
- Validate data quality and normalize dates, sales, and prices

### Week 2: Data Transformation with dbt
- Build staging models for sales, prices, and calendar data
- Create daily and weekly aggregate marts
- Document transformations and lineage

### Week 3: Forecasting
- Train Prophet for trend and holiday-aware demand estimates
- Train LightGBM for granular product-level demand forecasting
- Save forecast results back to a warehouse table

### Week 4: Dashboard & Reporting
- Create store and category filtering in Streamlit
- Show 30-day forecasts and inventory recommendations
- Simulate what-if demand scenarios

## Example usage
- Choose a store and department in the Streamlit app
- Review 30-day forecast and reorder points
- Test a price-drop scenario to estimate the demand impact
- Use the `replenishment` logic to decide an order quantity

## Notes
- The code is designed to work with either BigQuery or Snowflake via env variables.
- If `dbt` is configured, run `dbt deps` and `dbt build` from the `dbt/` directory.
- For a full production deployment, add access control, CI checks, and scheduling.
