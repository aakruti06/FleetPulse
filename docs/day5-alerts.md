# Day 5: Live temperature alerts

Flow: device -> IoT Core -> rule (temperature_c > 44) -> Lambda -> SNS -> email

- SNS topic: fleetpulse-alerts (email subscription, confirmed)
- Lambda: fleetpulse-alert (Python 3.12), topic ARN passed in the SNS_TOPIC_ARN environment variable
- Lambda role: inline policy allowing sns:Publish on that one topic only
- IoT rule: fleetpulse_hot_alert
  - SQL: SELECT * FROM 'fleetpulse/+/telemetry' WHERE temperature_c > 44
  - Action: invoke the Lambda
- The storage rule (fleetpulse_to_s3) is unchanged and runs in parallel.

## Threshold
44 C. The simulator draws temperatures between 20 and 45, so a lower threshold would send many emails per run.

## Testing
1. Lambda console test event with a sample hot reading.
2. Manual publish from the MQTT test client to fleetpulse/fleetpulse-device-001/telemetry.
3. Real simulator runs.

## Known limitations
- No cooldown, so a device stuck above the threshold sends one email per message.
- The threshold lives in the rule SQL, not in per-device config.
- No unit tests or dead-letter queue yet.
