-- Check 1: duplicates (QoS 1 can deliver a message twice)
SELECT device_id, ts, COUNT(*) AS copies
FROM fleetpulse.telemetry_raw
GROUP BY device_id, ts
HAVING COUNT(*) > 1
ORDER BY copies DESC
LIMIT 20;

-- Check 2: missing or out-of-range values (all counts except total_rows should be 0)
SELECT COUNT(*) AS total_rows,
  COUNT_IF(device_id IS NULL OR ts IS NULL OR temperature_c IS NULL
           OR battery_pct IS NULL OR vibration IS NULL) AS rows_with_nulls,
  COUNT_IF(temperature_c < 20 OR temperature_c > 45) AS temp_out_of_range,
  COUNT_IF(battery_pct < 0 OR battery_pct > 100) AS battery_out_of_range,
  COUNT_IF(vibration < 0 OR vibration > 1) AS vibration_out_of_range
FROM fleetpulse.telemetry_raw;

-- Check 3: gaps of 30 s to 10 min between consecutive readings of one device
SELECT device_id,
       from_unixtime(prev_ts) AS gap_start,
       from_unixtime(ts) AS gap_end,
       ts - prev_ts AS gap_sec
FROM (
  SELECT device_id, ts,
         LAG(ts) OVER (PARTITION BY device_id ORDER BY ts) AS prev_ts
  FROM fleetpulse.telemetry_raw
)
WHERE ts - prev_ts BETWEEN 30 AND 600
ORDER BY gap_end DESC
LIMIT 20;

-- Check 4: timestamps in the future (bad device clock)
SELECT device_id, ts, from_unixtime(ts) AS reading_time
FROM fleetpulse.telemetry_raw
WHERE ts > to_unixtime(current_timestamp) + 300
LIMIT 20;
