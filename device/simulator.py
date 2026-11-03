import collections
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path

from awscrt import mqtt
from awsiot import mqtt_connection_builder

from ota import download, parse_package, verify_checksum
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
JOBS = f"$aws/things/{DEVICE_ID}/jobs"
CERTS = Path(__file__).resolve().parent.parent / "certs" / DEVICE_ID

interval = 2
firmware_version = "1.0.0"
connected = threading.Event()
needs_setup = threading.Event()
job_check = threading.Event()
job_queue = queue.Queue()
buffer = collections.deque(maxlen=500)


def on_interrupted(connection, error, **kwargs):
    connected.clear()
    print(f"CONNECTION LOST ({error}). Buffering readings until it returns.")


def on_resumed(connection, return_code, session_present, **kwargs):
    connected.set()
    needs_setup.set()
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


def report_state(wait=True, sync_desired=False):
    state = {"reported": {"interval_sec": interval, "firmware_version": firmware_version}}
    if sync_desired:
        state["desired"] = {"interval_sec": interval}
    future, _ = conn.publish(
        topic=f"{SHADOW}/update",
        payload=json.dumps({"state": state}),
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
    report_state(wait=False)


def on_job_notify(topic, payload, dup, qos, retain, **kwargs):
    if json.loads(payload).get("execution"):
        job_check.set()


def on_job_accepted(topic, payload, dup, qos, retain, **kwargs):
    execution = json.loads(payload).get("execution")
    if execution:
        job_queue.put(execution)


def on_rejected(topic, payload, dup, qos, retain, **kwargs):
    print(f"Request rejected on {topic}: {payload.decode()}")


def subscribe(topic, callback):
    future, _ = conn.subscribe(topic=topic, qos=mqtt.QoS.AT_LEAST_ONCE, callback=callback)
    future.result(timeout=10)


def setup_cloud():
    subscribe(f"{SHADOW}/update/delta", on_delta)
    subscribe(f"{JOBS}/notify-next", on_job_notify)
    subscribe(f"{JOBS}/start-next/accepted", on_job_accepted)
    subscribe(f"{JOBS}/start-next/rejected", on_rejected)
    subscribe(f"{JOBS}/+/update/rejected", on_rejected)
    report_state()
    job_check.set()


def request_job():
    future, _ = conn.publish(
        topic=f"{JOBS}/start-next", payload="{}", qos=mqtt.QoS.AT_LEAST_ONCE
    )
    future.result(timeout=10)


def report_job(job_id, status, details):
    message = {
        "status": status,
        "statusDetails": {key: str(value) for key, value in details.items()},
    }
    future, _ = conn.publish(
        topic=f"{JOBS}/{job_id}/update",
        payload=json.dumps(message),
        qos=mqtt.QoS.AT_LEAST_ONCE,
    )
    future.result(timeout=10)


def process_job(execution):
    global interval, firmware_version
    job_id = execution["jobId"]
    doc = execution.get("jobDocument") or {}
    print(f"Job {job_id} received: {doc.get('operation')} {doc.get('version')}")
    try:
        report_job(job_id, "IN_PROGRESS", {"step": "downloading"})
        if doc.get("operation") != "update":
            raise ValueError(f"unsupported operation {doc.get('operation')!r}")
        data = download(doc["url"])
        if not verify_checksum(data, doc["sha256"]):
            raise ValueError("checksum mismatch, update rejected")
        package = parse_package(data)
        interval = package["default_interval_sec"]
        firmware_version = package["version"]
        report_state(sync_desired=True)
        report_job(job_id, "SUCCEEDED", {"version": firmware_version})
        print(f"Job {job_id} SUCCEEDED: firmware {firmware_version}, interval {interval}s")
    except Exception as err:
        print(f"Job {job_id} FAILED: {err!r}")
        try:
            report_job(job_id, "FAILED", {"reason": str(err)[:200]})
        except Exception as report_err:
            print(f"Could not report the failure ({report_err!r})")


def service_jobs():
    if job_check.is_set():
        job_check.clear()
        try:
            request_job()
        except Exception as err:
            print(f"Job request failed ({err!r})")
    while not job_queue.empty():
        process_job(job_queue.get())


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
    setup_cloud()
    print(f"Shadow and jobs ready: interval {interval}s, firmware {firmware_version}")
except Exception as err:
    sys.exit(f"Setup failed ({err!r}). Check that the newest policy version is Active.")

for i in range(COUNT):
    buffer.append(make_payload(DEVICE_ID, i))
    if needs_setup.is_set():
        needs_setup.clear()
        try:
            setup_cloud()
        except Exception as err:
            print(f"Setup after reconnect failed ({err!r}); will retry")
            needs_setup.set()
    flush_buffer()
    end = time.time() + interval
    while time.time() < end:
        service_jobs()
        time.sleep(0.2)

deadline = time.time() + 30
while buffer and time.time() < deadline:
    flush_buffer()
    time.sleep(1)
if buffer:
    print(f"WARNING: {len(buffer)} readings were not delivered")

conn.disconnect().result()
