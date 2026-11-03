import hashlib

import pytest

from ota import download, load_state, parse_package, save_state, verify_checksum

GOOD = b'{"version":"1.1.0","default_interval_sec":5}'
GOOD_SHA = hashlib.sha256(GOOD).hexdigest()


def test_checksum_matches():
    assert verify_checksum(GOOD, GOOD_SHA)


def test_checksum_ignores_case_and_whitespace():
    assert verify_checksum(GOOD, "  " + GOOD_SHA.upper() + "\n")


def test_one_extra_space_breaks_checksum():
    assert not verify_checksum(GOOD + b" ", GOOD_SHA)


def test_checksum_rejects_non_string():
    assert not verify_checksum(GOOD, None)
    assert not verify_checksum(GOOD, 123)


def test_parse_valid_package():
    package = parse_package(GOOD)
    assert package["version"] == "1.1.0"
    assert package["default_interval_sec"] == 5


@pytest.mark.parametrize("bad", [
    b"not json",
    b"[1, 2]",
    b'{"default_interval_sec": 5}',
    b'{"version": "", "default_interval_sec": 5}',
    b'{"version": "1.0.0"}',
    b'{"version": "1.0.0", "default_interval_sec": 500}',
    b'{"version": "1.0.0", "default_interval_sec": "5"}',
])
def test_parse_rejects_bad_packages(bad):
    with pytest.raises(ValueError):
        parse_package(bad)


def test_state_round_trip(tmp_path):
    path = tmp_path / "nested" / "dev.json"
    save_state(path, {"firmware_version": "1.2.0", "interval_sec": 4})
    assert load_state(path) == {"firmware_version": "1.2.0", "interval_sec": 4}
    assert not (tmp_path / "nested" / "dev.tmp").exists()


def test_load_missing_file_returns_empty(tmp_path):
    assert load_state(tmp_path / "missing.json") == {}


def test_load_corrupt_file_returns_empty(tmp_path):
    path = tmp_path / "bad.json"
    path.write_text("{oops")
    assert load_state(path) == {}


def test_load_non_dict_returns_empty(tmp_path):
    path = tmp_path / "list.json"
    path.write_text("[1, 2, 3]")
    assert load_state(path) == {}


def test_download_requires_https():
    with pytest.raises(ValueError):
        download("http://example.com/package.json")
