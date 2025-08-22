-- Example SQL: pull network usage data for last 30 days
SELECT u.ts, c.cell_id, c.site_id, s.city, s.region, u.tech,
       u.throughput_mbps, u.utilization_pct, u.latency_ms, u.packet_loss_pct, u.users_active
FROM fact_network_usage u
JOIN dim_cell c ON u.cell_id = c.cell_id
JOIN dim_site s ON c.site_id = s.site_id
WHERE u.ts >= NOW() - INTERVAL '30 days';

-- Peak hour (Busy Hour) per site by 95th percentile utilization
WITH hourly AS (
  SELECT
    DATE_TRUNC('hour', u.ts) AS hour_ts,
    c.site_id,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY u.utilization_pct) AS p95_util
  FROM fact_network_usage u
  JOIN dim_cell c ON u.cell_id = c.cell_id
  GROUP BY 1,2
)
SELECT site_id, hour_ts AS busy_hour_start, p95_util
FROM (
  SELECT *, ROW_NUMBER() OVER(PARTITION BY site_id ORDER BY p95_util DESC) AS rn
  FROM hourly
) x
WHERE rn = 1
ORDER BY p95_util DESC;

-- Top congested cells (average utilization between 19:00-23:00)
WITH prime AS (
  SELECT
    c.cell_id,
    AVG(u.utilization_pct) AS avg_util_prime
  FROM fact_network_usage u
  JOIN dim_cell c ON u.cell_id = c.cell_id
  WHERE EXTRACT(HOUR FROM u.ts) BETWEEN 19 AND 23
  GROUP BY 1
)
SELECT * FROM prime ORDER BY avg_util_prime DESC LIMIT 10;
