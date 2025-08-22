import numpy as np
import pandas as pd

def compute_aggregations(df: pd.DataFrame):
    df = df.copy()
    df["date"] = df["timestamp"].dt.date
    if "hour" not in df.columns:
        df["hour"] = df["timestamp"].dt.hour

    site_hour = df.groupby(["site_id","hour"], as_index=False).agg(
        avg_util=("utilization_pct","mean"),
        p95_util=("utilization_pct", lambda s: np.percentile(s.dropna(), 95) if s.notna().any() else np.nan),
        avg_latency=("latency_ms","mean"),
        users=("users_active","mean")
    )

    site_day = df.groupby(["site_id","date"], as_index=False).agg(
        avg_util=("utilization_pct","mean"),
        peak_util=("utilization_pct","max"),
        avg_latency=("latency_ms","mean"),
        users=("users_active","mean")
    )

    # Busy hour per site: hour with max average utilization
    tmp = (df.groupby(["site_id","hour"], as_index=False)["utilization_pct"]
             .mean()
             .rename(columns={"utilization_pct":"hour_avg_util"}))
    busy_hour = (tmp.sort_values(["site_id","hour_avg_util"], ascending=[True, False])
                    .groupby("site_id", as_index=False).head(1))

    congested_cells = (df[df["utilization_pct"] >= 80]
                       .sort_values(["utilization_pct","latency_ms"], ascending=[False, False])
                       .loc[:, ["timestamp","region","city","site_id","cell_id","tech","utilization_pct","latency_ms"]])

    hour_of_day = df.groupby(["hour","tech"], as_index=False)["utilization_pct"].mean()

    return {
        "site_hour": site_hour,
        "site_day": site_day,
        "busy_hour": busy_hour,
        "congested_cells": congested_cells,
        "hour_of_day": hour_of_day,
    }
