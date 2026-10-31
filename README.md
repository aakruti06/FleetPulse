# FleetPulse

Device-to-cloud IoT fleet monitoring platform on AWS.

Simulated devices stream telemetry over MQTT to AWS IoT Core, where it is
stored, queried, visualized, and alerted on. Devices can be configured and
updated remotely. All infrastructure is managed with Terraform and deployed
through GitHub Actions.

**Status:** 🚧 Work in progress

## Planned features
- [x] Device simulator with X.509 authentication (MQTT)
- [x] Ingestion pipeline: IoT Core → Lambda/Firehose → S3, Timestream
- [x] Grafana dashboard and SNS alerts
- [x] Device shadow and fleet-status API
- [ ] OTA updates with IoT Jobs
- [ ] Terraform infrastructure and CI/CD

## Tech
Python · AWS IoT Core · Lambda · S3 · Timestream · Terraform · Docker · GitHub Actions
