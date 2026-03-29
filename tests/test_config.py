import json
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from config import load_config, ConfigError


def test_load_valid_config(tmp_path):
    cfg = {
        "media_path": "/opt/share/Movies",
        "port": 8765,
        "data_dir": "/opt/homeplayer/data"
    }
    f = tmp_path / "config.json"
    f.write_text(json.dumps(cfg))
    result = load_config(str(f))
    assert result["media_path"] == "/opt/share/Movies"
    assert result["port"] == 8765
    assert result["tmdb_api_key"] == ""          # default
    assert result["scan_interval_seconds"] == 300  # default


def test_missing_required_field(tmp_path):
    f = tmp_path / "config.json"
    f.write_text(json.dumps({"port": 8765}))     # missing media_path and data_dir
    with pytest.raises(ConfigError):
        load_config(str(f))


def test_relative_data_dir_rejected(tmp_path):
    cfg = {"media_path": "/opt/share/Movies", "port": 8765, "data_dir": "./data"}
    f = tmp_path / "config.json"
    f.write_text(json.dumps(cfg))
    with pytest.raises(ConfigError, match="absolute"):
        load_config(str(f))


def test_relative_media_path_rejected(tmp_path):
    cfg = {"media_path": "./Movies", "port": 8765, "data_dir": "/opt/homeplayer/data"}
    f = tmp_path / "config.json"
    f.write_text(json.dumps(cfg))
    with pytest.raises(ConfigError, match="absolute"):
        load_config(str(f))
