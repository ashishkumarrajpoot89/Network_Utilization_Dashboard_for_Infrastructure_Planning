-- Schema: network utilization
CREATE TABLE IF NOT EXISTS dim_site (
    site_id        VARCHAR(16) PRIMARY KEY,
    region         VARCHAR(16),
    city           VARCHAR(32)
);

CREATE TABLE IF NOT EXISTS dim_cell (
    cell_id        VARCHAR(32) PRIMARY KEY,
    site_id        VARCHAR(16) REFERENCES dim_site(site_id),
    azimuth_deg    INT
);

CREATE TABLE IF NOT EXISTS fact_network_usage (
    usage_id           BIGSERIAL PRIMARY KEY,
    ts                 TIMESTAMP NOT NULL,
    cell_id            VARCHAR(32) REFERENCES dim_cell(cell_id),
    tech               VARCHAR(8) CHECK (tech IN ('4G','5G')),
    capacity_mbps      NUMERIC(10,2),
    throughput_mbps    NUMERIC(10,2),
    utilization_pct    NUMERIC(5,2),
    latency_ms         NUMERIC(6,2),
    packet_loss_pct    NUMERIC(5,2),
    users_active       INT
);

-- Helpful indexes
CREATE INDEX IF NOT EXISTS idx_usage_ts ON fact_network_usage(ts);
CREATE INDEX IF NOT EXISTS idx_usage_cell ON fact_network_usage(cell_id);
CREATE INDEX IF NOT EXISTS idx_usage_site ON dim_cell(site_id);
