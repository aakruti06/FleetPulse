import importlib.util
import json
import sys
import time
import types
from decimal import Decimal
from pathlib import Path

import pytest

LAMBDA_FILE = (
    Path(__file__).resolve().parent.parent
    / "cloud" / "lambdas" / "api" / "lambda_function.py"
)


class FakeTable:
    def __init__(self, items):
        self.items = items

    def scan(self):
        return {"Items": self.items}


@pytest.fixture
def api(monkeypatch):
    now_ms = int(time.time() * 1000)
    table = FakeTable([
        {"device_id": "dev-b", "received_at": Decimal(now_ms - 600_000),
         "temperature_c": Decimal("30.5")},
        {"device_id": "dev-a", "received_at": Decimal(now_ms - 5_000),
         "battery_pct": Decimal("90")},
    ])
    fake_boto3 = types.ModuleType("boto3")
    fake_boto3.resource = lambda name: types.SimpleNamespace(Table=lambda n: table)
    monkeypatch.setitem(sys.modules, "boto3", fake_boto3)
    monkeypatch.setenv("TABLE_NAME", "fake-table")
    monkeypatch.setenv("API_KEY", "secret-key")
    spec = importlib.util.spec_from_file_location("api_lambda", LAMBDA_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def call(api, headers):
    response = api.lambda_handler({"headers": headers}, None)
    return response["statusCode"], json.loads(response["body"])


def test_rejects_missing_key(api):
    status, body = call(api, {})
    assert status == 401
    assert body == {"error": "unauthorized"}


def test_rejects_wrong_key(api):
    status, _ = call(api, {"x-api-key": "wrong"})
    assert status == 401


def test_returns_devices_sorted(api):
    status, body = call(api, {"x-api-key": "secret-key"})
    assert status == 200
    assert body["count"] == 2
    assert [d["device_id"] for d in body["devices"]] == ["dev-a", "dev-b"]


def test_online_and_stale_status(api):
    _, body = call(api, {"x-api-key": "secret-key"})
    by_id = {d["device_id"]: d for d in body["devices"]}
    assert by_id["dev-a"]["status"] == "online"
    assert by_id["dev-b"]["status"] == "stale"


def test_decimals_become_plain_numbers(api):
    _, body = call(api, {"x-api-key": "secret-key"})
    by_id = {d["device_id"]: d for d in body["devices"]}
    assert by_id["dev-a"]["battery_pct"] == 90
    assert isinstance(by_id["dev-a"]["battery_pct"], int)
    assert by_id["dev-b"]["temperature_c"] == 30.5
