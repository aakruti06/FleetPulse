import hashlib
import hmac
import json
import urllib.request

from telemetry import valid_interval

MAX_PACKAGE_BYTES = 100_000


def verify_checksum(data, expected_hex):
    if not isinstance(expected_hex, str):
        return False
    actual = hashlib.sha256(data).hexdigest()
    return hmac.compare_digest(actual, expected_hex.strip().lower())


def parse_package(data):
    package = json.loads(data.decode("utf-8"))
    if not isinstance(package, dict):
        raise ValueError("package must be a JSON object")
    version = package.get("version")
    if not isinstance(version, str) or not version:
        raise ValueError("package has no version")
    if not valid_interval(package.get("default_interval_sec")):
        raise ValueError("default_interval_sec must be between 1 and 60")
    return package


def download(url, timeout=15):
    if not url.startswith("https://"):
        raise ValueError("download URL must use https")
    with urllib.request.urlopen(url, timeout=timeout) as response:
        data = response.read(MAX_PACKAGE_BYTES + 1)
    if len(data) > MAX_PACKAGE_BYTES:
        raise ValueError("package too large")
    return data
