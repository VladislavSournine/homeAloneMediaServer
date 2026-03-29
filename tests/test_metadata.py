import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import pytest
from unittest.mock import patch, MagicMock
import metadata
from metadata import MetadataCache, build_movie_metadata, build_series_metadata

def test_cache_miss_returns_empty(tmp_path):
    cache = MetadataCache(str(tmp_path / "meta.json"), api_key="")
    assert cache.get("99999") == {}

def test_cache_hit_returns_stored(tmp_path):
    data = {"99999": {"tmdb_id": 99999, "year": 2020}}
    (tmp_path / "meta.json").write_text(json.dumps(data))
    cache = MetadataCache(str(tmp_path / "meta.json"), api_key="key")
    assert cache.get("99999")["year"] == 2020

def test_no_api_key_skips_fetch(tmp_path):
    cache = MetadataCache(str(tmp_path / "meta.json"), api_key="")
    result = cache.fetch_and_cache("Inception", is_series=False)
    assert result == {}

def test_fetch_movie_calls_tmdb(tmp_path):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": 27205, "title": "Inception", "popularity": 50.0,
                     "release_date": "2010-07-16", "vote_average": 8.4,
                     "genre_ids": [28], "overview": "A thief...", "media_type": "movie"}]
    }
    mock_details = MagicMock()
    mock_details.json.return_value = {
        "genres": [{"name": "Action"}],
        "poster_path": "/abc.jpg"
    }
    with patch("metadata.requests.get", side_effect=[mock_response, mock_details]):
        cache = MetadataCache(str(tmp_path / "meta.json"), api_key="testkey")
        result = cache.fetch_and_cache("Inception", is_series=False)
    assert result["tmdb_id"] == 27205
    assert result["year"] == 2010
    assert "Action" in result["genres"]
    assert result["rating"] == 8.4

def test_fetch_stores_in_cache(tmp_path):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "results": [{"id": 27205, "title": "Inception", "popularity": 50.0,
                     "release_date": "2010-07-16", "vote_average": 8.4,
                     "genre_ids": [], "overview": "", "media_type": "movie"}]
    }
    mock_details = MagicMock()
    mock_details.json.return_value = {"genres": [], "poster_path": None}
    with patch("metadata.requests.get", side_effect=[mock_response, mock_details]):
        cache = MetadataCache(str(tmp_path / "meta.json"), api_key="testkey")
        cache.fetch_and_cache("Inception", is_series=False)
    stored = json.loads((tmp_path / "meta.json").read_text())
    assert "27205" in stored
