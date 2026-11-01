from telemetry import make_payload, valid_interval


def test_payload_has_expected_fields():
    payload = make_payload("fleetpulse-device-001", 0)
    assert set(payload) == {"device_id", "ts", "temperature_c", "battery_pct", "vibration"}
    assert payload["device_id"] == "fleetpulse-device-001"


def test_values_stay_in_range():
    for i in range(200):
        payload = make_payload("dev", i)
        assert 20 <= payload["temperature_c"] <= 45
        assert 0 <= payload["battery_pct"] <= 100
        assert 0 <= payload["vibration"] <= 1


def test_battery_never_negative():
    assert make_payload("dev", 1000)["battery_pct"] == 0


def test_battery_drops_over_time():
    assert make_payload("dev", 10)["battery_pct"] < make_payload("dev", 0)["battery_pct"]


def test_valid_interval_accepts_good_values():
    for value in (1, 2, 10, 60, 2.5):
        assert valid_interval(value)


def test_valid_interval_rejects_bad_values():
    for value in (0, 0.5, 61, 500, -1, None, "10", True):
        assert not valid_interval(value)
