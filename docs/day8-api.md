# Day 8: Fleet-status API

Flow: IoT rule -> DynamoDB (latest state per device) -> Lambda -> API Gateway (GET /devices)

- Table fleetpulse-device-status, partition key device_id, on-demand capacity
- IoT rule fleetpulse_to_dynamodb stores every message (DynamoDBv2 action)
- Lambda scans the table and adds a status: online if the last message is under 120 seconds old
- The API checks a shared key in the x-api-key header and returns 401 otherwise
- Least privilege: the rule role writes to the table, the Lambda role can only scan it

## Problem solved
The table stayed empty because its key was device-id (hyphen) while messages carry device_id (underscore). Key names cannot be changed, so I recreated the empty table.

## Limitations
- One shared key on a public URL (production: IAM, Cognito or a JWT authorizer)
- Scan reads the whole table, fine for a small fleet only
- Online status is a time window, not the real connection state
