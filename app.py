from pathlib import Path
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Smart Retail Analytics",
    page_icon="ðŸ“Š",
    layout="wide"
)

ROOT = Path(__file__).resolve().parent

def load_csv(candidates):
    for candidate in candidates:
        path = ROOT / candidate
        if path.exists():
            try:
                return pd.read_csv(path), str(path.relative_to(ROOT))
            except Exception as exc:
                st.warning(f"Could not read {path.name}: {exc}")
    return None, None

valid, valid_path = load_csv([
    "data/processed/valid_sales.csv",
    "data/valid_sales.csv",
])
invalid, invalid_path = load_csv([
    "data/quarantine/invalid_sales.csv",
    "data/invalid_sales.csv",
])
anomalies, anomalies_path = load_csv([
    "data/processed/sales_anomalies.csv",
    "data/sales_anomalies.csv",
])

st.title("ðŸ“Š Smart Retail Sales Analytics")
st.caption("Data quality â€¢ Sales overview â€¢ Anomaly monitoring")

if valid is None:
    st.error("Could not find valid_sales.csv. Check that it is saved under data/processed/valid_sales.csv.")
    st.info("Expected project structure: app.py, data/processed/valid_sales.csv, data/quarantine/invalid_sales.csv, data/processed/sales_anomalies.csv")
    st.stop()

# Normalize column names for flexible matching.
valid.columns = [str(c).strip() for c in valid.columns]
cols_lower = {c.lower().replace(" ", "_"): c for c in valid.columns}

def find_col(*names):
    for name in names:
        key = name.lower().replace(" ", "_")
        if key in cols_lower:
            return cols_lower[key]
    return None

qty_col = find_col("quantity", "qty")
price_col = find_col("unit_price", "unit price", "price")
store_col = find_col("store_id", "store id", "store")
product_col = find_col("product_id", "product id", "product")
date_col = find_col("transaction_date", "sales_date", "date")
sales_col = find_col("total_sales", "sales", "amount", "revenue")

if sales_col is None and qty_col and price_col:
    valid["_dashboard_total_sales"] = (
        pd.to_numeric(valid[qty_col], errors="coerce") *
        pd.to_numeric(valid[price_col], errors="coerce")
    )
    sales_col = "_dashboard_total_sales"

total_sales = float(pd.to_numeric(valid[sales_col], errors="coerce").fillna(0).sum()) if sales_col else 0
valid_count = len(valid)
invalid_count = len(invalid) if invalid is not None else 0
anomaly_count = len(anomalies) if anomalies is not None else 0

c1, c2, c3, c4 = st.columns(4)
c1.metric("Valid transactions", f"{valid_count:,}")
c2.metric("Total sales", f"{total_sales:,.2f}" if sales_col else "N/A")
c3.metric("Invalid records", f"{invalid_count:,}")
c4.metric("Detected anomalies", f"{anomaly_count:,}")

st.divider()

left, right = st.columns(2)
with left:
    st.subheader("Sales by store")
    if store_col and sales_col:
        chart_df = valid[[store_col, sales_col]].copy()
        chart_df[sales_col] = pd.to_numeric(chart_df[sales_col], errors="coerce")
        chart_df = chart_df.dropna().groupby(store_col, as_index=False)[sales_col].sum()
        if not chart_df.empty:
            st.bar_chart(chart_df.set_index(store_col)[sales_col])
        else:
            st.info("No usable store sales values were found.")
    else:
        st.info("A store ID and a sales/price/quantity column are needed for this chart.")

with right:
    st.subheader("Sales by product")
    if product_col and sales_col:
        chart_df = valid[[product_col, sales_col]].copy()
        chart_df[sales_col] = pd.to_numeric(chart_df[sales_col], errors="coerce")
        chart_df = chart_df.dropna().groupby(product_col, as_index=False)[sales_col].sum()
        if not chart_df.empty:
            st.bar_chart(chart_df.set_index(product_col)[sales_col])
        else:
            st.info("No usable product sales values were found.")
    else:
        st.info("A product ID and a sales/price/quantity column are needed for this chart.")

if date_col and sales_col:
    st.subheader("Sales over time")
    trend = valid[[date_col, sales_col]].copy()
    trend[date_col] = pd.to_datetime(trend[date_col], errors="coerce")
    trend[sales_col] = pd.to_numeric(trend[sales_col], errors="coerce")
    trend = trend.dropna().groupby(date_col, as_index=False)[sales_col].sum().sort_values(date_col)
    if not trend.empty:
        st.line_chart(trend.set_index(date_col)[sales_col])

st.divider()
st.subheader("Data quality review")
tab1, tab2, tab3 = st.tabs(["Valid sales", "Invalid records", "Anomalies"])
with tab1:
    st.caption(f"Source: {valid_path}")
    st.dataframe(valid, use_container_width=True)
with tab2:
    if invalid is not None:
        st.caption(f"Source: {invalid_path}")
        st.dataframe(invalid, use_container_width=True)
    else:
        st.info("Invalid records CSV was not found; the rest of the dashboard can still run.")
with tab3:
    if anomalies is not None:
        st.caption(f"Source: {anomalies_path}")
        st.dataframe(anomalies, use_container_width=True)
    else:
        st.info("Anomalies CSV was not found; the rest of the dashboard can still run.")

st.caption("Built for the Smart Retail Sales Data Quality & Anomaly Detection Pipeline.")
st.subheader("Store-Wise Sales")

store_sales = valid.groupby("store_id")["quantity"].sum()

st.bar_chart(store_sales)