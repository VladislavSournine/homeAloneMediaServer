import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pytest
from scanner import parse_movie_filename, parse_episode_filename, slugify, scan_library

def test_parse_movie():
    assert parse_movie_filename("Inception_1080p.mp4") == {"title": "Inception", "quality": "1080p"}

def test_parse_movie_ultra():
    assert parse_movie_filename("The Matrix_1080p Ultra.mp4") == {"title": "The Matrix", "quality": "1080p Ultra"}

def test_parse_movie_cyrillic():
    r = parse_movie_filename("Крик 7_720p.mp4")
    assert r == {"title": "Крик 7", "quality": "720p"}

def test_parse_movie_none():
    assert parse_movie_filename("random.mp4") is None
    assert parse_movie_filename("Show_S01E01_720p.mp4") is None

def test_parse_episode():
    r = parse_episode_filename("Breaking Bad_S01E03_720p.mp4")
    assert r == {"title": "Breaking Bad", "season": 1, "episode": 3, "quality": "720p"}

def test_parse_episode_none():
    assert parse_episode_filename("Inception_1080p.mp4") is None

def test_slugify_latin():
    assert slugify("Breaking Bad") == "breaking-bad"

def test_slugify_cyrillic_uses_folder_name(tmp_path):
    # Cyrillic titles use folder name as id directly (not slugified)
    (tmp_path / "Крик 7").mkdir()
    ((tmp_path / "Крик 7") / "Крик 7_720p.mp4").touch()
    lib = scan_library(str(tmp_path))
    assert lib["movies"][0]["id"] == "крик-7"  # lowercased folder

def test_scan_library_movie(tmp_path):
    folder = tmp_path / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").touch()
    lib = scan_library(str(tmp_path))
    assert len(lib["movies"]) == 1
    assert lib["movies"][0]["title"] == "Inception"
    assert lib["movies"][0]["quality"] == "1080p"
    assert lib["movies"][0]["file"] == "Inception/Inception_1080p.mp4"

def test_scan_library_series(tmp_path):
    folder = tmp_path / "Breaking Bad"
    folder.mkdir()
    (folder / "Breaking Bad_S01E01_720p.mp4").touch()
    (folder / "Breaking Bad_S01E02_720p.mp4").touch()
    lib = scan_library(str(tmp_path))
    assert len(lib["series"]) == 1
    assert lib["series"][0]["title"] == "Breaking Bad"
    assert len(lib["series"][0]["episodes"]) == 2

def test_scan_library_has_subtitles(tmp_path):
    folder = tmp_path / "Крик 7"
    folder.mkdir()
    (folder / "Крик 7_720p.mp4").touch()
    (folder / "Крик 7_720p_Українська.vtt").touch()
    lib = scan_library(str(tmp_path))
    assert lib["movies"][0]["has_subtitles"] is True

def test_scan_library_no_subtitles(tmp_path):
    folder = tmp_path / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").touch()
    lib = scan_library(str(tmp_path))
    assert lib["movies"][0]["has_subtitles"] is False

def test_scan_empty_dir(tmp_path):
    lib = scan_library(str(tmp_path))
    assert lib == {"movies": [], "series": []}

def test_scan_nonexistent_dir():
    lib = scan_library("/nonexistent/path")
    assert lib == {"movies": [], "series": []}

import time
import threading
from scanner import LibraryCache

def test_library_cache_initial_scan(tmp_path):
    folder = tmp_path / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").touch()
    cache = LibraryCache(str(tmp_path), scan_interval=9999)
    lib = cache.get()
    assert len(lib["movies"]) == 1

def test_library_cache_detects_new_folder(tmp_path):
    import threading as _threading
    detected = _threading.Event()
    cache = LibraryCache(str(tmp_path), scan_interval=0.05, on_new_folder=lambda f: detected.set())
    cache.start()
    try:
        folder = tmp_path / "Inception"
        folder.mkdir()
        (folder / "Inception_1080p.mp4").touch()
        assert detected.wait(timeout=2), "Scanner did not detect new folder within 2s"
        assert len(cache.get()["movies"]) == 1
    finally:
        cache.stop()

def test_library_cache_detects_deleted_folder(tmp_path):
    folder = tmp_path / "Inception"
    folder.mkdir()
    (folder / "Inception_1080p.mp4").touch()
    cache = LibraryCache(str(tmp_path), scan_interval=0.05)
    cache.start()
    try:
        time.sleep(0.1)
        import shutil
        shutil.rmtree(str(folder))
        time.sleep(0.2)
        assert len(cache.get()["movies"]) == 0
    finally:
        cache.stop()
