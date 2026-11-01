import random
import time


def make_payload(device_id, i):
    return {
        "device_id": device_id,
        "ts": int(time.time()),
        "temperature_c": round(random.uniform(20, 45), 2),
        "battery_pct": round(max(0, 100 - i * 0.5), 1),
        "vibration": round(random.uniform(0, 1), 3),
    }


def valid_interval(value):
    is_number = isinstance(value, (int, float)) and not isinstance(value, bool)
    return is_number and 1 <= value <= 60
