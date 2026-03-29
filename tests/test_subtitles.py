import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from subtitles import find_subtitle

def test_finds_ukrainska_first(tmp_path):
    folder = tmp_path / "Крик 7"
    folder.mkdir()
    (folder / "Крик 7_720p_Українська.vtt").touch()
    (folder / "Крик 7_720p_English.vtt").touch()
    result = find_subtitle(str(tmp_path), "Крик 7/Крик 7_720p.mp4")
    assert result.endswith("_Українська.vtt")

def test_falls_back_to_alphabetical(tmp_path):
    folder = tmp_path / "Movie"
    folder.mkdir()
    (folder / "Movie_720p_English.vtt").touch()
    (folder / "Movie_720p_German.vtt").touch()
    result = find_subtitle(str(tmp_path), "Movie/Movie_720p.mp4")
    assert result.endswith("_English.vtt")

def test_returns_none_when_no_vtt(tmp_path):
    folder = tmp_path / "Movie"
    folder.mkdir()
    (folder / "Movie_720p.mp4").touch()
    assert find_subtitle(str(tmp_path), "Movie/Movie_720p.mp4") is None

def test_path_traversal_rejected(tmp_path):
    assert find_subtitle(str(tmp_path), "../etc/passwd") is None

def test_returns_none_when_folder_missing(tmp_path):
    assert find_subtitle(str(tmp_path), "NonExistent/movie.mp4") is None
