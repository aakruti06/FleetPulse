# Day 9: Resilience, tests and data quality

## Resilience
The simulator buffers readings (bounded at 500) while disconnected, reconnects with backoff (1 to 30 seconds) and sends the buffered readings in order after the connection returns. Readings keep their original timestamp. The endpoint is read from the FLEETPULSE_ENDPOINT environment variable.

Test: switched Wi-Fi off for about 30 seconds mid-run. The device buffered 16 readings and delivered them all after reconnecting.

## Tests
Run with: python3 -m pytest
- tests/test_telemetry.py: payload fields and ranges, battery floor, interval validation
- tests/test_api_lambda.py: API key check, sorting, online or stale status, number conversion (uses a fake DynamoDB table, no AWS needed)

## Data-quality checks
sql/03_quality_checks.sql: duplicates, nulls and out-of-range values, gaps between readings, timestamps in the future. All clean on the current data.

## Limitations
- The buffer is in memory, so it is lost if the device restarts
- Duplicates are detected but not removed
