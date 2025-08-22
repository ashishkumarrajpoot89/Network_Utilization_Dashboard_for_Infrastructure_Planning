import os
import pandas as pd
from sqlalchemy import create_engine, text

def _dsn_from_env() -> str:
    dialect = os.getenv("DB_DIALECT", "postgresql")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "telecom")
    user = os.getenv("DB_USER", "user")
    pw   = os.getenv("DB_PASS", "pass")
    if dialect.startswith("postgres"):
        return f"postgresql+psycopg2://{user}:{pw}@{host}:{port}/{name}"
    elif dialect.startswith("mysql"):
        return f"mysql+pymysql://{user}:{pw}@{host}:{port}/{name}"
    else:
        raise ValueError(f"Unsupported DB_DIALECT: {dialect}")

def get_connection():
    dsn = _dsn_from_env()
    engine = create_engine(dsn, pool_pre_ping=True)
    return engine

def fetch_sample_usage(engine):
    # Adjust table/columns to your schema. Return columns matching REQUIRED_COLS.
    q = text("""
        SELECT
            timestamp,
            region,
            city,
            site_id,
            cell_id,
            tech,
            capacity_mbps,
            throughput_mbps,
            CASE
                WHEN capacity_mbps > 0 THEN throughput_mbps * 100.0 / capacity_mbps
                ELSE NULL
            END AS utilization_pct,
            latency_ms,
            packet_loss_pct,
            users_active
        FROM network_usage
        ORDER BY timestamp DESC
        LIMIT 200000
    """)
    with engine.connect() as conn:
        df = pd.read_sql(q, conn)
    return df
