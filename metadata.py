import json
import os
import threading
import requests

TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"

def build_movie_metadata(tmdb_id: int, search_result: dict, details: dict) -> dict:
    year = 0
    date = search_result.get("release_date", "")
    if date:
        try: year = int(date[:4])
        except ValueError: pass
    return {
        "tmdb_id": tmdb_id,
        "poster_url": TMDB_IMAGE_BASE + details["poster_path"] if details.get("poster_path") else "",
        "year": year,
        "rating": round(search_result.get("vote_average", 0), 1),
        "genres": [g["name"] for g in details.get("genres", [])],
        "overview": search_result.get("overview", ""),
    }

def build_series_metadata(tmdb_id: int, search_result: dict, details: dict) -> dict:
    year = 0
    date = search_result.get("first_air_date", "")
    if date:
        try: year = int(date[:4])
        except ValueError: pass
    return {
        "tmdb_id": tmdb_id,
        "poster_url": TMDB_IMAGE_BASE + details["poster_path"] if details.get("poster_path") else "",
        "first_air_year": year,
        "rating": round(search_result.get("vote_average", 0), 1),
        "genres": [g["name"] for g in details.get("genres", [])],
        "overview": search_result.get("overview", ""),
        "season_count": details.get("number_of_seasons", 0),
        "episode_count": details.get("number_of_episodes", 0),
    }

class MetadataCache:
    def __init__(self, cache_path: str, api_key: str):
        self._path = cache_path
        self._api_key = api_key
        self._lock = threading.Lock()
        self._data = self._load()

    def get(self, tmdb_id: str) -> dict:
        with self._lock:
            return self._data.get(str(tmdb_id), {})

    def fetch_and_cache(self, title: str, is_series: bool) -> dict:
        if not self._api_key:
            return {}
        try:
            media_type = "tv" if is_series else "movie"
            r = requests.get(
                f"{TMDB_BASE}/search/multi",
                params={"api_key": self._api_key, "query": title, "language": "uk-UA"},
                timeout=10,
            )
            r.raise_for_status()
            results = r.json().get("results", [])
            # Filter by media_type and pick highest popularity
            filtered = [x for x in results if x.get("media_type") == media_type]
            if not filtered:
                filtered = results  # fallback: take any type
            if not filtered:
                return {}
            best = max(filtered, key=lambda x: x.get("popularity", 0))
            tmdb_id = best["id"]

            detail_url = f"{TMDB_BASE}/{media_type}/{tmdb_id}"
            resp = requests.get(
                detail_url, params={"api_key": self._api_key}, timeout=10
            )
            resp.raise_for_status()
            details = resp.json()

            if is_series:
                meta = build_series_metadata(tmdb_id, best, details)
            else:
                meta = build_movie_metadata(tmdb_id, best, details)

            with self._lock:
                self._data[str(tmdb_id)] = meta
                self._save()
            return meta
        except Exception as e:
            print(f"[metadata] fetch failed for '{title}': {e}")
            return {}

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
