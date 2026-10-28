import os
import boto3

sns = boto3.client("sns")
TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]


def lambda_handler(event, context):
    device = event.get("device_id", "unknown")
    temp = event.get("temperature_c")
    battery = event.get("battery_pct")

    message = (
        f"Device {device} reported a high temperature.\n"
        f"Temperature: {temp} C\n"
        f"Battery: {battery}%\n"
        f"Timestamp: {event.get('ts')}"
    )

    sns.publish(
        TopicArn=TOPIC_ARN,
        Subject=f"FleetPulse alert: {device} at {temp} C",
        Message=message,
    )
    return {"statusCode": 200}
