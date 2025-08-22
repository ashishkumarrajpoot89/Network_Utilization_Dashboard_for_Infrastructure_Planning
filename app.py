import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import streamlit as st
import altair as alt

# Allow importing from ./src
ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.append(str(SRC))

from analyze_network import compute_aggregations
try:
    from db_connection import get_connection, fetch_sample_usage
except Exception:
    get_connection = None
    fetch_sample_usage = None

st.set_page_config(page_title="Network Utilization Dashboard", layout="wide")
st.title("📡 Network Utilization Dashboard for Infrastructure Planning")

REQUIRED_COLS = {
    "timestamp","region","city","site_id","cell_id","tech",
    "capacity_mbps","throughput_mbps","utilization_pct",
    "latency_ms","packet_loss_pct","users_active"
}

# --- Helpers ---
def _apply_aliases(df: pd.DataFrame) -> pd.DataFrame:
    """Optional aliasing if upstream feeds use different names."""
    aliases = {
        "timestamp": ["timestamp", "time", "datetime", "event_time", "date_time"],
    }
    for canonical, alts in aliases.items():
        if canonical not in df.columns:
            for a in alts:
                if a in df.columns:
                    df.rename(columns={a: canonical}, inplace=True)
                    break
    return df

def read_network_csv(file_or_path, required_cols: set) -> pd.DataFrame:
    """Safer CSV loader: check headers, then parse timestamp, fail fast with clear errors."""
    df = pd.read_csv(file_or_path)
    df = _apply_aliases(df)
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(
            "Your CSV is missing required network columns.\n"
            f"Missing: {sorted(list(missing))}\n"
            f"Expected at least: {sorted(list(required_cols))}"
        )
    # Parse timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    if df["timestamp"].isna().all():
        raise ValueError(
            "Could not parse any valid datetimes in 'timestamp'. "
            "Use ISO-like formats (e.g., 2025-08-22 19:05:00)."
        )
    # Basic hygiene
    numeric_cols = [
        "capacity_mbps","throughput_mbps","utilization_pct",
        "latency_ms","packet_loss_pct","users_active"
    ]
    for c in numeric_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    # Optional: compute utilization if missing/NaN
    if "utilization_pct" in df.columns:
        need_util = df["utilization_pct"].isna()
        if need_util.any():
            with np.errstate(divide="ignore", invalid="ignore"):
                calc = (df["throughput_mbps"] / df["capacity_mbps"]) * 100.0
                df.loc[need_util, "utilization_pct"] = calc.clip(lower=0, upper=100)
    return df

# --- Data Source Choice ---
with st.sidebar:
    st.header("Data Source")
    source = st.radio("Choose data source", ["CSV (local/upload)", "Database (optional)"])

    default_csv = ROOT / "data" / "network_usage_sample.csv"
    uploaded = None
    df = None

    if source == "CSV (local/upload)":
        uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
        if uploaded is not None:
            try:
                df = read_network_csv(uploaded, REQUIRED_COLS)
            except Exception as e:
                st.error(str(e))
                st.stop()
        else:
            if default_csv.exists():
                st.caption(f"Using default CSV: {default_csv}")
                try:
                    df = read_network_csv(default_csv, REQUIRED_COLS)
                except Exception as e:
                    st.error(str(e))
                    st.stop()
            else:
                st.error("No CSV found. Please upload one.")
                st.stop()
    else:
        st.caption("Set env vars to connect:")
        st.code(
            "DB_DIALECT=postgresql | mysql\n"
            "DB_HOST=localhost\nDB_PORT=5432\nDB_NAME=telecom\n"
            "DB_USER=youruser\nDB_PASS=yourpass",
            language="bash"
        )
        if st.button("Fetch from Database", type="primary"):
            if get_connection is None:
                st.error("Database utilities not available.")
            else:
                try:
                    engine = get_connection()
                    df = fetch_sample_usage(engine)
                    # Validate/normalize DB output as well
                    df = _apply_aliases(df)
                    missing = REQUIRED_COLS - set(df.columns)
                    if missing:
                        st.error(f"DB result missing columns: {sorted(list(missing))}")
                        st.stop()
                    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
                    st.success(f"Fetched {len(df):,} rows from DB.")
                except Exception as e:
                    st.exception(e)

if df is None or df.empty:
    st.stop()

# Ensure timestamp is datetime and drop invalid
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
df = df.dropna(subset=["timestamp"])

# --- Required columns check ---
missing = REQUIRED_COLS - set(df.columns)
if missing:
    st.error(f"Missing required columns: {sorted(list(missing))}")
    st.stop()

# --- Filters ---
with st.sidebar:
    st.header("Filters")

    min_d = df["timestamp"].min().date()
    max_d = df["timestamp"].max().date()

    date_range = st.date_input(
        "Date range",
        (min_d, max_d),
        min_value=min_d,
        max_value=max_d
    )

    techs = st.multiselect("Tech", sorted(df["tech"].dropna().unique()), default=None)
    regions = st.multiselect("Region", sorted(df["region"].dropna().unique()), default=None)
    cities = st.multiselect("City", sorted(df["city"].dropna().unique()), default=None)
    sites = st.multiselect("Site", sorted(df["site_id"].dropna().unique()), default=None)
    util_threshold = st.slider("Congestion threshold (%)", 50, 100, 80)

# Convert date range to pandas.Timestamp for comparison
start_date = pd.to_datetime(date_range[0])
end_date = pd.to_datetime(date_range[1]) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)

# Apply filters
mask = (df["timestamp"] >= start_date) & (df["timestamp"] <= end_date)
if techs:   mask &= df["tech"].isin(techs)
if regions: mask &= df["region"].isin(regions)
if cities:  mask &= df["city"].isin(cities)
if sites:   mask &= df["site_id"].isin(sites)

df_f = df.loc[mask].copy()
if df_f.empty:
    st.warning("No data after applying filters.")
    st.stop()

# --- KPIs (robust) ---
def safe_metric(val, fmt="{:.1f}"):
    try:
        if pd.isna(val):
            return "—"
        return fmt.format(val)
    except Exception:
        return str(val)

kpi_cols = st.columns(5)
kpi_cols[0].metric("Rows", f"{len(df_f):,}")
kpi_cols[1].metric("Avg Utilization (P95 proxy)",
                   safe_metric(np.percentile(df_f["utilization_pct"].dropna(), 95), "{:.1f}%"))
kpi_cols[2].metric("Peak Utilization",
                   safe_metric(df_f["utilization_pct"].max(), "{:.1f}%"))
kpi_cols[3].metric("Avg Latency (ms)",
                   safe_metric(df_f["latency_ms"].mean()))
kpi_cols[4].metric("Active Users (avg)",
                   safe_metric(df_f["users_active"].mean()))

# --- Charts ---
st.subheader("Utilization Over Time")
util_chart = alt.Chart(df_f).mark_line().encode(
    x=alt.X('timestamp:T', title='Time'),
    y=alt.Y('utilization_pct:Q', title='Utilization (%)'),
    color=alt.Color('site_id:N', title='Site')
).properties(height=300)
st.altair_chart(util_chart.interactive(), use_container_width=True)

st.subheader("Hour-of-Day vs Avg Utilization (by Tech)")
df_f["hour"] = df_f["timestamp"].dt.hour
hod = df_f.groupby(["hour","tech"], as_index=False)["utilization_pct"].mean()
hod_chart = alt.Chart(hod).mark_line(point=True).encode(
    x=alt.X('hour:O', title='Hour'),
    y=alt.Y('utilization_pct:Q', title='Avg Utilization (%)'),
    color='tech:N'
).properties(height=280)
st.altair_chart(hod_chart.interactive(), use_container_width=True)

st.subheader(f"Prime-Time Congestion (19:00–23:00, threshold {util_threshold}%)")
prime = df_f[(df_f["hour"]>=19) & (df_f["hour"]<=23)]
congested = prime[prime["utilization_pct"] >= util_threshold].copy()
congested_view = congested[["timestamp","region","city","site_id","cell_id","tech","utilization_pct","latency_ms"]]\
    .sort_values(["utilization_pct","latency_ms"], ascending=[False, False])
st.dataframe(congested_view, use_container_width=True, hide_index=True)

# --- Analysis tables + downloads ---
st.subheader("Analysis Tables")
tables = compute_aggregations(df_f)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["site_hour","site_day","busy_hour","congested_cells","hour_of_day"])
with tab1:
    st.dataframe(tables["site_hour"].head(100), use_container_width=True, hide_index=True)
    st.download_button("Download site_hour.csv", tables["site_hour"].to_csv(index=False).encode('utf-8'), "site_hour.csv", "text/csv")
with tab2:
    st.dataframe(tables["site_day"].head(100), use_container_width=True, hide_index=True)
    st.download_button("Download site_day.csv", tables["site_day"].to_csv(index=False).encode('utf-8'), "site_day.csv", "text/csv")
with tab3:
    st.dataframe(tables["busy_hour"].head(100), use_container_width=True, hide_index=True)
    st.download_button("Download busy_hour.csv", tables["busy_hour"].to_csv(index=False).encode('utf-8'), "busy_hour.csv", "text/csv")
with tab4:
    st.dataframe(tables["congested_cells"].head(100), use_container_width=True, hide_index=True)
    st.download_button("Download congested_cells.csv", tables["congested_cells"].to_csv(index=False).encode('utf-8'), "congested_cells.csv", "text/csv")
with tab5:
    st.dataframe(tables["hour_of_day"].head(100), use_container_width=True, hide_index=True)
    st.download_button("Download hour_of_day.csv", tables["hour_of_day"].to_csv(index=False).encode('utf-8'), "hour_of_day.csv", "text/csv")

st.caption("Tip: Use the sidebar filters to focus on a region/site or to move the congestion threshold.")
