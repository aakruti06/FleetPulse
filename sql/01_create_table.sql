CREATE DATABASE fleetpulse;

CREATE EXTERNAL TABLE IF NOT EXISTS fleetpulse.telemetry_raw (
  device_id string,
  ts bigint,
  temperature_c double,
  battery_pct double,
  vibration double
)
ROW FORMAT SERDE 'org.openx.data.jsonserde.JsonSerDe'
LOCATION 's3://fleetpulse-raw-fp-26/raw/';
