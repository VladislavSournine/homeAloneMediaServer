import sys, os, json, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import urllib.request
import urllib.error
import pytest
from server import run_server


@pytest.fixture(scope="module")
def auth_server(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("auth")
    (tmp_path / "Movies").mkdir()
    (tmp_path / "data").mkdir()
    cfg = {
        "media_path": str(tmp_path / "Movies"),
        "port": 18800,
        "tmdb_api_key": "",
        "data_dir": str(tmp_path / "data"),
        "scan_interval_seconds": 9999,
        "auth_token": "secret123",
    }
    threading.Thread(target=run_server, args=(cfg,), daemon=True).start()
    time.sleep(0.3)
    yield "http://127.0.0.1:18800"


@pytest.fixture(scope="module")
def no_auth_server(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("noauth")
    (tmp_path / "Movies").mkdir()
    (tmp_path / "data").mkdir()
    cfg = {
        "media_path": str(tmp_path / "Movies"),
        "port": 18801,
        "tmdb_api_key": "",
        "data_dir": str(tmp_path / "data"),
        "scan_interval_seconds": 9999,
        "auth_token": "",
    }
    threading.Thread(target=run_server, args=(cfg,), daemon=True).start()
    time.sleep(0.3)
    yield "http://127.0.0.1:18801"


def test_no_token_returns_401(auth_server):
    try:
        urllib.request.urlopen(auth_server + "/library")
        assert False, "Expected 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401


def test_wrong_token_returns_401(auth_server):
    req = urllib.request.Request(
        auth_server + "/library",
        headers={"Authorization": "Bearer wrong"},
    )
    try:
        urllib.request.urlopen(req)
        assert False, "Expected 401"
    except urllib.error.HTTPError as e:
        assert e.code == 401


def test_correct_token_returns_200(auth_server):
    req = urllib.request.Request(
        auth_server + "/library",
        headers={"Authorization": "Bearer secret123"},
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200


def test_no_auth_configured_allows_all(no_auth_server):
    with urllib.request.urlopen(no_auth_server + "/library") as resp:
        assert resp.status == 200
