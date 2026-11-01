import hmac, json, os, time
from decimal import Decimal
import boto3

table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
API_KEY = os.environ["API_KEY"]
ONLINE_WINDOW_SEC = 120


def _clean(value):
    if isinstance(value, Decimal):
        return int(value) if value == value.to_integral_value() else float(value)
    return value


def _response(status, body):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body),
    }


def lambda_handler(event, context):
    sent_key = (event.get("headers") or {}).get("x-api-key", "")
    if not hmac.compare_digest(sent_key.encode(), API_KEY.encode()):
        return _response(401, {"error": "unauthorized"})

    now_ms = int(time.time() * 1000)
    devices = []
    for item in table.scan().get("Items", []):
        device = {key: _clean(val) for key, val in item.items()}
        age_sec = (now_ms - device.get("received_at", 0)) / 1000
        device["seconds_since_last_message"] = round(age_sec)
        device["status"] = "online" if age_sec < ONLINE_WINDOW_SEC else "stale"
        devices.append(device)

    devices.sort(key=lambda d: d["device_id"])
    return _response(200, {"count": len(devices), "devices": devices})
