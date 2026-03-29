import sys, os, json, threading, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import urllib.request
import pytest
from server import make_app, run_server

@pytest.fixture
def app(tmp_path):
    media = tmp_path / "Movies"
    media.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    folder = media / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").write_bytes(b"fakevideo" * 100)
    (folder / "Inception_1080p_Українська.vtt").write_text("WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHello")
    (folder / "poster.jpg").write_bytes(b"fakejpg")
    cfg = {
        "media_path": str(media),
        "port": 0,
        "tmdb_api_key": "",
        "data_dir": str(data),
        "scan_interval_seconds": 9999,
    }
    return make_app(cfg)

def test_library_returns_movies(app):
    lib = json.loads(app.handle_library())
    assert len(lib["movies"]) == 1
    assert lib["movies"][0]["title"] == "Inception"
    assert lib["movies"][0]["has_subtitles"] is True
    assert "last_scanned" in lib

def test_watch_history_post_and_get(app):
    app.handle_watch_history_post({"id": "inception", "position_ms": 1000, "duration_ms": 5000})
    history = json.loads(app.handle_watch_history_get())
    assert "inception" in history
    assert history["inception"]["position_ms"] == 1000

def test_watch_history_delete(app):
    app.handle_watch_history_post({"id": "inception", "position_ms": 1000, "duration_ms": 5000})
    app.handle_watch_history_delete("inception")
    history = json.loads(app.handle_watch_history_get())
    assert "inception" not in history

def test_error_response_is_json(app):
    result = app.make_error(404, "Not found")
    data = json.loads(result)
    assert data["code"] == 404
    assert "Not found" in data["error"]


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    tmp_path = tmp_path_factory.mktemp("live")
    media = tmp_path / "Movies"
    media.mkdir()
    data = tmp_path / "data"
    data.mkdir()
    folder = media / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").write_bytes(b"x" * 100)
    (folder / "secret.txt").write_text("secret")
    cfg = {
        "media_path": str(media),
        "port": 18799,
        "tmdb_api_key": "",
        "data_dir": str(data),
        "scan_interval_seconds": 9999,
    }
    t = threading.Thread(target=run_server, args=(cfg,), daemon=True)
    t.start()
    time.sleep(0.3)
    yield "http://127.0.0.1:18799"


def test_stream_non_mp4_returns_403(live_server):
    req = urllib.request.Request(live_server + "/stream/Inception/secret.txt")
    try:
        urllib.request.urlopen(req)
        assert False, "Expected 403"
    except urllib.error.HTTPError as e:
        assert e.code == 403


def test_stream_mp4_returns_200(live_server):
    req = urllib.request.Request(live_server + "/stream/Inception/Inception_1080p.mp4")
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
