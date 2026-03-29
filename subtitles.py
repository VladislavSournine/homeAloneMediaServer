import os

def find_subtitle(media_path: str, video_rel_path: str) -> str | None:
    """Return absolute path to .vtt file for the given video, or None."""
    # Guard against path traversal
    abs_video = os.path.realpath(os.path.join(media_path, video_rel_path))
    if not abs_video.startswith(os.path.realpath(media_path) + os.sep):
        return None

    folder = os.path.dirname(abs_video)
    base = os.path.splitext(os.path.basename(abs_video))[0]

    # Priority 1: base_Українська.vtt
    preferred = os.path.join(folder, base + "_Українська.vtt")
    if os.path.isfile(preferred):
        return preferred

    # Priority 2: any .vtt starting with base, alphabetical first
    if not os.path.isdir(folder):
        return None
    candidates = sorted(
        f for f in os.listdir(folder)
        if f.endswith('.vtt') and f.startswith(base)
    )
    if candidates:
        return os.path.join(folder, candidates[0])

    return None
