import json, random, sys, time
from pathlib import Path
from awscrt import mqtt
from awsiot import mqtt_connection_builder

ENDPOINT = "a2v4tpht6mhubb-ats.iot.ap-south-1.amazonaws.com"

if len(sys.argv) not in (2, 3):
    sys.exit("Usage: python3 device/simulator.py <device-name> [message-count]")

DEVICE_ID = sys.argv[1]
COUNT = int(sys.argv[2]) if len(sys.argv) == 3 else 30
TOPIC = f"fleetpulse/{DEVICE_ID}/telemetry"
SHADOW = f"$aws/things/{DEVICE_ID}/shadow"
CERTS = Path(__file__).resolve().parent.parent / "certs" / DEVICE_ID

interval = 2  # seconds between messages, can be changed remotely via the shadow

conn = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=str(CERTS / f"{DEVICE_ID}-certificate.pem.crt"),
    pri_key_filepath=str(CERTS / f"{DEVICE_ID}-private.pem.key"),
    ca_filepath=str(CERTS / "AmazonRootCA1.pem"),
    client_id=DEVICE_ID,
    keep_alive_secs=30,
)
conn.connect().result()
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
    if isinstance(desired, (int, float)) and 1 <= desired <= 60:
        interval = desired
        print(f"Shadow update received: interval is now {interval}s")
    else:
        print(f"Shadow update ignored (invalid interval): {desired!r}")
    report_interval(wait=False)


try:
    sub_future, _ = conn.subscribe(
        topic=f"{SHADOW}/update/delta",
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_delta,
    )
    sub_future.result(timeout=10)
    report_interval()
    print(f"Shadow ready, reported interval {interval}s")
except Exception as err:
    sys.exit(f"Shadow setup failed ({err!r}). Check that the newest policy version is Active.")

for i in range(COUNT):
    payload = {
        "device_id": DEVICE_ID,
        "ts": int(time.time()),
        "temperature_c": round(random.uniform(20, 45), 2),
        "battery_pct": round(max(0, 100 - i * 0.5), 1),
        "vibration": round(random.uniform(0, 1), 3),
    }
    future, _ = conn.publish(topic=TOPIC, payload=json.dumps(payload), qos=mqtt.QoS.AT_LEAST_ONCE)
    future.result()
    print("Sent:", payload)
    time.sleep(interval)

conn.disconnect().result()
