# Day 3: IoT rule to S3

Every telemetry message is copied into S3 by an AWS IoT rule.

- Rule name: fleetpulse_to_s3
- Region: ap-south-1
- SQL: SELECT * FROM 'fleetpulse/+/telemetry'
- Action: S3 bucket fleetpulse-raw-fp-26
- Key: raw/${parse_time("yyyy-MM-dd", timestamp())}/${topic(2)}/${timestamp()}.json
- Role: fleetpulse-iot-s3-role (write access to this bucket only)
- Bucket: public access blocked

## Result
Files appear as raw/<date>/<device-id>/<timestamp>.json, about 30 per device per simulator run.

## Known limitation
One file per message. Production would batch with Kinesis Data Firehose and write Parquet.
