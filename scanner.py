import os
import re
import threading
import datetime

QUALITY_PATTERN = r'360p|480p|720p|1080p Ultra|1080p|2160p|4k'

def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r'[^\w\s-]', '', s, flags=re.UNICODE)
    s = re.sub(r'[\s_]+', '-', s.strip())
    return s.strip('-') or title.lower().replace(' ', '-')

def parse_movie_filename(filename: str):
    m = re.match(rf'^(.+)_({QUALITY_PATTERN})\.mp4$', filename)
    if m and not re.search(r'_S\d+E\d+', m.group(1)):
        return {"title": m.group(1), "quality": m.group(2)}
    return None

def parse_episode_filename(filename: str):
    m = re.match(rf'^(.+)_S(\d+)E(\d+)_({QUALITY_PATTERN})\.mp4$', filename)
    if m:
        return {"title": m.group(1), "season": int(m.group(2)),
                "episode": int(m.group(3)), "quality": m.group(4)}
    return None

def _has_subtitles(folder_path: str, video_filename: str) -> bool:
    base = os.path.splitext(video_filename)[0]
    for f in os.listdir(folder_path):
        if f.endswith('.vtt') and f.startswith(base):
            return True
    return False

def scan_library(media_path: str) -> dict:
    if not os.path.exists(media_path):
        return {"movies": [], "series": []}

    movies, series = [], {}

    for folder in sorted(os.listdir(media_path)):
        folder_path = os.path.join(media_path, folder)
        if not os.path.isdir(folder_path):
            continue

        folder_id = slugify(folder)

        for filename in sorted(os.listdir(folder_path)):
            if not filename.endswith('.mp4'):
                continue

            ep = parse_episode_filename(filename)
            if ep:
                if folder_id not in series:
                    series[folder_id] = {"id": folder_id, "title": folder,
                                         "episodes": [], "metadata": {}}
                series[folder_id]["episodes"].append({
                    "season": ep["season"],
                    "episode": ep["episode"],
                    "quality": ep["quality"],
                    "file": f"{folder}/{filename}",
                    "has_subtitles": _has_subtitles(folder_path, filename),
                })
                continue

            mv = parse_movie_filename(filename)
            if mv:
                movies.append({
                    "id": folder_id,
                    "title": folder,
                    "quality": mv["quality"],
                    "file": f"{folder}/{filename}",
                    "has_subtitles": _has_subtitles(folder_path, filename),
                    "metadata": {},
                })

    return {"movies": movies, "series": list(series.values())}


class LibraryCache:
    def __init__(self, media_path: str, scan_interval: float = 300,
                 on_new_folder=None):
        self._media_path = media_path
        self._interval = scan_interval
        self._on_new_folder = on_new_folder  # callback(folder_name) for metadata fetch
        self._lock = threading.Lock()
        self._library = {"movies": [], "series": []}
        self._folder_mtimes: dict = {}
        self._last_scanned: str = ""
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()
        # Initial full scan (synchronous, before HTTP server starts)
        self._full_scan()

    def get(self) -> dict:
        with self._lock:
            result = dict(self._library)
            result["last_scanned"] = self._last_scanned
            return result

    def update_metadata(self, folder_id: str, metadata: dict):
        """Called by metadata.py after TMDb fetch completes."""
        with self._lock:
            for item in self._library.get("movies", []):
                if item["id"] == folder_id:
                    item["metadata"] = metadata
            for item in self._library.get("series", []):
                if item["id"] == folder_id:
                    item["metadata"] = metadata

    def start(self):
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)

    def _full_scan(self):
        lib = scan_library(self._media_path)
        mtimes = self._read_mtimes()
        with self._lock:
            new_folders = [f for f in mtimes if f not in self._folder_mtimes]
            self._library = lib
            self._folder_mtimes = mtimes
            self._last_scanned = datetime.datetime.now().isoformat(timespec='seconds')
        if self._on_new_folder:
            for folder in new_folders:
                self._on_new_folder(folder)

    def _read_mtimes(self) -> dict:
        if not os.path.exists(self._media_path):
            return {}
        result = {}
        for name in os.listdir(self._media_path):
            p = os.path.join(self._media_path, name)
            if os.path.isdir(p):
                result[name] = os.path.getmtime(p)
        return result

    def _run(self):
        while not self._stop_event.wait(self._interval):
            current_mtimes = self._read_mtimes()
            with self._lock:
                known = self._folder_mtimes
            changed = {f for f, m in current_mtimes.items()
                       if f not in known or known[f] != m}
            deleted = {f for f in known if f not in current_mtimes}
            if changed or deleted:
                self._full_scan()
