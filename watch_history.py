import json
import os
import threading
import datetime

class WatchHistory:
    def __init__(self, path: str):
        self._path = path
        self._lock = threading.Lock()
        self._data = self._load()

    def get_all(self) -> dict:
        with self._lock:
            return dict(self._data)

    def upsert(self, entry_id: str, position_ms: int, duration_ms: int):
        with self._lock:
            self._data[entry_id] = {
                "position_ms": position_ms,
                "duration_ms": duration_ms,
                "updated_at": datetime.datetime.now().isoformat(timespec='seconds'),
            }
            self._save()

    def delete(self, entry_id: str):
        with self._lock:
            self._data.pop(entry_id, None)
            self._save()

    def _load(self) -> dict:
        if os.path.exists(self._path):
            try:
                with open(self._path) as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError):
                pass
        return {}

    def _save(self):
        os.makedirs(os.path.dirname(self._path), exist_ok=True)
        with open(self._path, "w") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)
