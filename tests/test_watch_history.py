import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from watch_history import WatchHistory

def test_empty_on_start(tmp_path):
    wh = WatchHistory(str(tmp_path / "history.json"))
    assert wh.get_all() == {}

def test_upsert_and_get(tmp_path):
    wh = WatchHistory(str(tmp_path / "history.json"))
    wh.upsert("kryk-7", 3600000, 7200000)
    all_ = wh.get_all()
    assert "kryk-7" in all_
    assert all_["kryk-7"]["position_ms"] == 3600000
    assert all_["kryk-7"]["duration_ms"] == 7200000
    assert "updated_at" in all_["kryk-7"]

def test_upsert_series_episode(tmp_path):
    wh = WatchHistory(str(tmp_path / "history.json"))
    wh.upsert("show-s01e03", 1200000, 2700000)
    all_ = wh.get_all()
    assert "show-s01e03" in all_

def test_delete(tmp_path):
    wh = WatchHistory(str(tmp_path / "history.json"))
    wh.upsert("kryk-7", 1000, 2000)
    wh.delete("kryk-7")
    assert "kryk-7" not in wh.get_all()

def test_persists_to_disk(tmp_path):
    path = str(tmp_path / "history.json")
    wh = WatchHistory(path)
    wh.upsert("kryk-7", 1000, 2000)
    # Re-load from disk
    wh2 = WatchHistory(path)
    assert "kryk-7" in wh2.get_all()

def test_delete_nonexistent_is_noop(tmp_path):
    wh = WatchHistory(str(tmp_path / "history.json"))
    wh.delete("nonexistent")  # should not raise
