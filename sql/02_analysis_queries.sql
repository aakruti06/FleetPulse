-- Messages per device
SELECT device_id, COUNT(*) AS messages
FROM fleetpulse.telemetry_raw
GROUP BY device_id
ORDER BY device_id;

-- Temperature and battery summary per device
SELECT device_id,
       ROUND(AVG(temperature_c), 2) AS avg_temp,
       MAX(temperature_c) AS max_temp,
       MIN(battery_pct) AS lowest_battery
FROM fleetpulse.telemetry_raw
GROUP BY device_id
ORDER BY avg_temp DESC;

-- Readings that would trigger an alert
SELECT device_id,
       from_unixtime(ts) AS reading_time,
       temperature_c
FROM fleetpulse.telemetry_raw
WHERE temperature_c > 40
ORDER BY ts DESC
LIMIT 20;
