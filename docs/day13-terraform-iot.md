# Day 13: IoT infrastructure in Terraform

Terraform now builds the device side of the parallel stack (prefix fleetpulse-tf).

## Resources
- 3 IoT things and 3 active certificates (for_each over a list of device IDs)
- One shared IoT policy using the thing-name policy variable (written as $${...} in Terraform)
- IAM roles for the IoT rules, each limited to one action on one resource
- IoT rules: store every message in S3 and DynamoDB
- Certificate and key files written to certs/ (git-ignored, owner-only permissions) plus a downloaded copy of the Amazon root certificate

## Separate topic prefix
Both stacks live in one AWS account and region, and MQTT topics are shared, so the Terraform stack uses fleetpulse-tf/<device>/telemetry. The simulator reads FLEETPULSE_TOPIC_PREFIX (default fleetpulse), so the hand-built stack is unaffected.

## Test
export FLEETPULSE_TOPIC_PREFIX=fleetpulse-tf
python3 device/simulator.py fleetpulse-tf-device-001 10
Data arrived in the new S3 bucket and DynamoDB table, and nothing leaked into the hand-built stack.

## Security notes
- Private keys are created by Terraform and live in the encrypted, private remote state (acceptable for a demo; production devices should generate their own keys)
- Keys on disk are git-ignored and owner-only
- Rule roles are least privilege and trust only IoT in this account

## Next
Lambdas, API Gateway, SNS alerts, then a full destroy and rebuild.
