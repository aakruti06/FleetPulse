import collections
import json
import os
import sys
import threading
import time
from pathlib import Path

from awscrt import mqtt
from awsiot import mqtt_connection_builder

from telemetry import make_payload, valid_interval

ENDPOINT = os.environ.get("FLEETPULSE_ENDPOINT")
if not ENDPOINT:
    sys.exit("Set FLEETPULSE_ENDPOINT first (your IoT Core device data endpoint).")
if len(sys.argv) not in (2, 3):
    sys.exit("Usage: python3 device/simulator.py <device-name> [message-count]")

DEVICE_ID = sys.argv[1]
COUNT = int(sys.argv[2]) if len(sys.argv) == 3 else 30
TOPIC = f"fleetpulse/{DEVICE_ID}/telemetry"
SHADOW = f"$aws/things/{DEVICE_ID}/shadow"
CERTS = Path(__file__).resolve().parent.parent / "certs" / DEVICE_ID

interval = 2
connected = threading.Event()
needs_shadow_setup = threading.Event()
buffer = collections.deque(maxlen=500)


def on_interrupted(connection, error, **kwargs):
    connected.clear()
    print(f"CONNECTION LOST ({error}). Buffering readings until it returns.")


def on_resumed(connection, return_code, session_present, **kwargs):
    connected.set()
    needs_shadow_setup.set()
    print(f"Connection restored. {len(buffer)} buffered readings to send.")


conn = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=str(CERTS / f"{DEVICE_ID}-certificate.pem.crt"),
    pri_key_filepath=str(CERTS / f"{DEVICE_ID}-private.pem.key"),
    ca_filepath=str(CERTS / "AmazonRootCA1.pem"),
    client_id=DEVICE_ID,
    keep_alive_secs=10,
    reconnect_min_timeout_secs=1,
    reconnect_max_timeout_secs=30,
    on_connection_interrupted=on_interrupted,
    on_connection_resumed=on_resumed,
)
conn.connect().result()
connected.set()
print(f"{DEVICE_ID} connected, publishing to {TOPIC}")


def report_interval(wait=True):
    msg = {"state": {"reported": {"interval_sec": interval}}}
    future, _ = conn.publish(
        topic=f"{SHADOW}/update",
        payload=json.dumps(msg),
        qos=mqtt.QoS.AT_LEAST_ONCE,
    )
    if wait:
        future.result(timeout=10)


def on_delta(topic, payload, dup, qos, retain, **kwargs):
    global interval
    desired = json.loads(payload).get("state", {}).get("interval_sec")
    if valid_interval(desired):
        interval = desired
        print(f"Shadow update received: interval is now {interval}s")
    else:
        print(f"Shadow update ignored (invalid interval): {desired!r}")
    report_interval(wait=False)


def setup_shadow():
    sub_future, _ = conn.subscribe(
        topic=f"{SHADOW}/update/delta",
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_delta,
    )
    sub_future.result(timeout=10)
    report_interval()


def flush_buffer():
    while buffer and connected.is_set():
        item = buffer[0]
        try:
            future, _ = conn.publish(
                topic=TOPIC, payload=json.dumps(item), qos=mqtt.QoS.AT_LEAST_ONCE
            )
            future.result(timeout=5)
        except Exception as err:
            print(f"Send failed ({err!r}); {len(buffer)} readings stay buffered")
            return
        buffer.popleft()
        print("Sent:", item)


try:
    setup_shadow()
    print(f"Shadow ready, reported interval {interval}s")
except Exception as err:
    sys.exit(f"Shadow setup failed ({err!r}). Check that the newest policy version is Active.")

for i in range(COUNT):
    buffer.append(make_payload(DEVICE_ID, i))
    if needs_shadow_setup.is_set():
        needs_shadow_setup.clear()
        try:
            setup_shadow()
        except Exception as err:
            print(f"Shadow setup after reconnect failed ({err!r}); will retry")
            needs_shadow_setup.set()
    flush_buffer()
    time.sleep(interval)

deadline = time.time() + 30
while buffer and time.time() < deadline:
    flush_buffer()
    time.sleep(1)
if buffer:
    print(f"WARNING: {len(buffer)} readings were not delivered")

conn.disconnect().result()
