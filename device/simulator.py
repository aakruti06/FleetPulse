import json, random, time
from pathlib import Path
from awscrt import mqtt
from awsiot import mqtt_connection_builder

ENDPOINT = "a2v4tpht6mhubb-ats.iot.ap-south-1.amazonaws.com"
DEVICE_ID = "demo-thing"
TOPIC = "fleetpulse/device-001/telemetry"

CERTS = Path(__file__).resolve().parent.parent / "certs"

conn = mqtt_connection_builder.mtls_from_path(
    endpoint=ENDPOINT,
    cert_filepath=str(CERTS / "demo-certificate.pem.crt"),
    pri_key_filepath=str(CERTS / "demo-private.pem.key"),
    ca_filepath=str(CERTS / "AmazonRootCA1.pem"),
    client_id=DEVICE_ID,
    keep_alive_secs=30,
)
conn.connect().result()
print("Connected")

for i in range(10):
    payload = {
        "device_id": DEVICE_ID,
        "ts": int(time.time()),
        "temperature_c": round(random.uniform(20, 45), 2),
        "battery_pct": round(100 - i * 0.5, 1),
        "vibration": round(random.uniform(0, 1), 3),
    }
    future, _ = conn.publish(topic=TOPIC, payload=json.dumps(payload), qos=mqtt.QoS.AT_LEAST_ONCE)
    future.result()
    print("Sent:", payload)
    time.sleep(2)

conn.disconnect().result()
