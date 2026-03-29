import json
import os

REQUIRED = ["media_path", "data_dir"]
DEFAULTS = {
    "port": 8765,
    "tmdb_api_key": "",
    "scan_interval_seconds": 300,
    "auth_token": "",
}


class ConfigError(Exception):
    pass


def load_config(path: str) -> dict:
    try:
        with open(path) as f:
            cfg = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        raise ConfigError(f"Cannot load config: {e}")

    for key in REQUIRED:
        if key not in cfg:
            raise ConfigError(f"Missing required config key: {key}")

    if not os.path.isabs(cfg["data_dir"]):
        raise ConfigError(f"data_dir must be an absolute path, got: {cfg['data_dir']}")

    if not os.path.isabs(cfg["media_path"]):
        raise ConfigError(f"media_path must be an absolute path, got: {cfg['media_path']}")

    for key, default in DEFAULTS.items():
        cfg.setdefault(key, default)

    return cfg
