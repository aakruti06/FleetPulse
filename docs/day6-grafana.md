# Day 6: Grafana dashboard on Athena

Flow: S3 raw data -> Athena table fleetpulse.telemetry_raw -> Grafana (Docker) panels

## Why not Timestream
Timestream for LiveAnalytics is closed to new customers, and Timestream for InfluxDB needs a paid VPC instance. Athena reads the S3 data directly and costs almost nothing at this scale.

## Run Grafana
docker run -d --name grafana -p 3000:3000 \
  --env-file ~/FleetPulse/.env \
  -e GF_INSTALL_PLUGINS=grafana-athena-datasource \
  --restart unless-stopped \
  -v grafana-data:/var/lib/grafana \
  grafana/grafana-oss

The .env file holds the read-only AWS key and is ignored by Git.

## Data source settings
Amazon Athena data source, access and secret key login, region ap-south-1, catalog AwsDataCatalog, database fleetpulse, workgroup primary, output location s3://fleetpulse-raw-fp-26/athena-results/

## IAM
Dedicated user fleetpulse-grafana-reader. Policy allows Athena queries, Glue read, S3 read on the data bucket, and S3 write only under athena-results/.

## Panels (dashboards/fleetpulse-dashboard.json)
1. Messages per device (bar chart)
2. Temperature by device (time series)
3. Hot readings above 44 C (table)

## Problem solved
Athena returned 0 rows because the IoT rule's S3 key started with leading spaces, so files landed under a different prefix. Fixed the key and verified 90 rows (3 devices x 30 messages).

## Limitations
- Athena queries take seconds and are billed by data scanned
- One JSON file per message, no partitions or Parquet yet
- Not real time
