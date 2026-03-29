import http.server
import socketserver
import urllib.parse
import json
import os
import re
import argparse
import threading
import datetime

from config import load_config
from scanner import LibraryCache, slugify
from metadata import MetadataCache
from watch_history import WatchHistory
from subtitles import find_subtitle


class App:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        os.makedirs(cfg["data_dir"], exist_ok=True)

        self.watch_history = WatchHistory(
            os.path.join(cfg["data_dir"], "watch_history.json"))
        self.metadata = MetadataCache(
            os.path.join(cfg["data_dir"], "metadata_cache.json"),
            api_key=cfg.get("tmdb_api_key", ""))

        # Initialize without callback first so self.library is assigned before
        # _on_new_folder is ever called (LibraryCache runs initial scan in __init__)
        self.library = LibraryCache(
            cfg["media_path"],
            scan_interval=cfg["scan_interval_seconds"],
        )
        # Now that self.library exists, attach the metadata callback and trigger
        # it for any folders that were found during the initial scan
        self.library._on_new_folder = self._on_new_folder
        if cfg.get("tmdb_api_key"):
            lib = self.library.get()
            folders = [m["title"] for m in lib.get("movies", [])] + \
                      [s["title"] for s in lib.get("series", [])]
            threading.Thread(
                target=lambda: [self._on_new_folder(f) for f in folders],
                daemon=True,
            ).start()

    def _on_new_folder(self, folder_name: str):
        folder_id = slugify(folder_name)
        lib = self.library.get()
        is_series = any(s["id"] == folder_id for s in lib.get("series", []))
        meta = self.metadata.fetch_and_cache(folder_name, is_series=is_series)
        if meta:
            self.library.update_metadata(folder_id, meta)

    def handle_library(self) -> str:
        lib = self.library.get()
        return json.dumps(lib, ensure_ascii=False)

    def handle_watch_history_get(self) -> str:
        return json.dumps(self.watch_history.get_all(), ensure_ascii=False)

    def handle_watch_history_post(self, body: dict):
        self.watch_history.upsert(
            body["id"], body["position_ms"], body["duration_ms"])

    def handle_watch_history_delete(self, entry_id: str):
        self.watch_history.delete(entry_id)

    def make_error(self, code: int, message: str) -> str:
        return json.dumps({"error": message, "code": code})


def make_app(cfg: dict) -> App:
    return App(cfg)


class MediaHandler(http.server.BaseHTTPRequestHandler):
    app: App = None

    def log_message(self, fmt, *args):
        pass

    def _json(self, data: str, status: int = 200):
        body = data.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, code: int, message: str):
        self._json(self.app.make_error(code, message), status=code)

    def _check_auth(self) -> bool:
        token = self.app.cfg.get("auth_token", "")
        if not token:
            return True
        auth_header = self.headers.get("Authorization", "")
        return auth_header == f"Bearer {token}"

    def do_GET(self):
        if not self._check_auth():
            self._error(401, "Unauthorized"); return
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/library":
            self._json(self.app.handle_library())
        elif path.startswith("/stream/"):
            self._serve_stream(path[len("/stream/"):])
        elif path.startswith("/poster/"):
            self._serve_poster(path[len("/poster/"):])
        elif path.startswith("/subtitles/"):
            self._serve_subtitles(path[len("/subtitles/"):])
        elif path.startswith("/metadata/"):
            tmdb_id = path[len("/metadata/"):]
            meta = self.app.metadata.get(tmdb_id)
            if meta:
                self._json(json.dumps(meta, ensure_ascii=False))
            else:
                self._error(404, "Metadata not found")
        elif path == "/watch_history":
            self._json(self.app.handle_watch_history_get())
        else:
            self._error(404, "Not found")

    def do_POST(self):
        if not self._check_auth():
            self._error(401, "Unauthorized"); return
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path == "/watch_history":
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                self.app.handle_watch_history_post(body)
                self._json('{"ok": true}')
            except (KeyError, ValueError) as e:
                self._error(400, str(e))
        else:
            self._error(404, "Not found")

    def do_DELETE(self):
        if not self._check_auth():
            self._error(401, "Unauthorized"); return
        parsed = urllib.parse.urlparse(self.path)
        path = urllib.parse.unquote(parsed.path)

        if path.startswith("/watch_history/"):
            entry_id = path[len("/watch_history/"):]
            self.app.handle_watch_history_delete(entry_id)
            self._json('{"ok": true}')
        else:
            self._error(404, "Not found")

    def _serve_stream(self, rel_path: str):
        media_path = self.app.cfg["media_path"]
        abs_path = os.path.realpath(os.path.join(media_path, rel_path))
        base = os.path.realpath(media_path)
        if not abs_path.startswith(base + os.sep):
            self._error(403, "Forbidden"); return
        if not abs_path.lower().endswith(".mp4"):
            self._error(403, "Forbidden"); return
        if not os.path.isfile(abs_path):
            self._error(404, "File not found"); return

        file_size = os.path.getsize(abs_path)
        range_header = self.headers.get("Range")
        m = re.match(r'bytes=(\d+)-(\d*)', range_header) if range_header else None

        if m:
            start = int(m.group(1))
            end = int(m.group(2)) if m.group(2) else file_size - 1
            length = end - start + 1
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        else:
            start, length = 0, file_size
            self.send_response(200)

        self.send_header("Content-Type", "video/mp4")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()
        try:
            with open(abs_path, "rb") as f:
                f.seek(start)
                remaining = length
                while remaining > 0:
                    chunk = f.read(min(65536, remaining))
                    if not chunk: break
                    self.wfile.write(chunk)
                    remaining -= len(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _serve_poster(self, title: str):
        media_path = self.app.cfg["media_path"]
        poster_path = os.path.realpath(os.path.join(media_path, title, "poster.jpg"))
        base = os.path.realpath(media_path)
        if not poster_path.startswith(base + os.sep):
            self._error(403, "Forbidden"); return
        if os.path.isfile(poster_path):
            size = os.path.getsize(poster_path)
            self.send_response(200)
            self.send_header("Content-Type", "image/jpeg")
            self.send_header("Content-Length", str(size))
            self.end_headers()
            with open(poster_path, "rb") as f:
                self.wfile.write(f.read())
            return
        # Fallback: find tmdb poster_url in metadata cache
        folder_id = slugify(title)
        lib = self.app.library.get()
        meta = {}
        for item in lib.get("movies", []) + lib.get("series", []):
            if item["id"] == folder_id:
                meta = item.get("metadata", {})
                break
        poster_url = meta.get("poster_url", "")
        if poster_url:
            self.send_response(302)
            self.send_header("Location", poster_url)
            self.end_headers()
        else:
            self._error(404, "Poster not found")

    def _serve_subtitles(self, rel_path: str):
        media_path = self.app.cfg["media_path"]
        # find_subtitle() handles path traversal guard internally
        vtt_path = find_subtitle(media_path, rel_path)
        if not vtt_path:
            self._error(404, "Subtitles not found"); return
        size = os.path.getsize(vtt_path)
        self.send_response(200)
        self.send_header("Content-Type", "text/vtt; charset=utf-8")
        self.send_header("Content-Length", str(size))
        self.end_headers()
        try:
            with open(vtt_path, "rb") as f:
                self.wfile.write(f.read())
        except (BrokenPipeError, ConnectionResetError):
            pass


def run_server(cfg: dict):
    app = make_app(cfg)
    app.library.start()

    class Handler(MediaHandler):
        pass
    Handler.app = app

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("", cfg["port"]), Handler) as httpd:
        print(f"homeplayer-server running on port {cfg['port']}, media: {cfg['media_path']}")
        httpd.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config.json")
    args = parser.parse_args()
    cfg = load_config(args.config)
    run_server(cfg)
