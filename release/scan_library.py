"""Incrementally synchronize a movie catalog with local media files."""

import argparse
import json
import re
import tempfile
import unicodedata
from pathlib import Path
from typing import Optional, Tuple


VIDEO_EXTENSIONS = {".mp4", ".webm", ".mov"}
POSTER_EXTENSIONS = (".jpg", ".png", ".webp")
EPISODE_PATTERN = re.compile(r"s(\d+)e(\d+)", re.IGNORECASE)
KNOWN_TITLE_IDS = {"新电影": "new-movie"}


def make_id(value: str) -> str:
    """Create a stable, filesystem-friendly identifier from a title or filename."""
    if value in KNOWN_TITLE_IDS:
        return KNOWN_TITLE_IDS[value]
    normalized = unicodedata.normalize("NFKD", value).casefold()
    identifier = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-_")
    return identifier or "untitled"


def parse_episode(filename: str) -> Optional[Tuple[int, int]]:
    """Return the season and episode encoded as SxxExx in *filename*."""
    match = EPISODE_PATTERN.search(filename)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def _media_files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        (path for path in directory.iterdir() if path.is_file() and path.suffix.casefold() in VIDEO_EXTENSIONS),
        key=lambda path: path.name.casefold(),
    )


def _poster_for(media_root: Path, item_id: str) -> Optional[str]:
    for extension in POSTER_EXTENSIONS:
        if (media_root / "posters" / f"{item_id}{extension}").is_file():
            return f"posters/{item_id}{extension}"
    return None


def _with_poster(item: dict, media_root: Path) -> dict:
    updated = dict(item)
    if not updated.get("poster"):
        poster = _poster_for(media_root, updated["id"])
        if poster is not None:
            updated["poster"] = poster
    return updated


def _scan_movies(media_root: Path, existing: dict[str, dict]) -> list[dict]:
    scanned: dict[str, str] = {}
    for path in _media_files(media_root / "movies"):
        scanned[make_id(path.stem)] = f"movies/{path.name}"

    movies: list[dict] = []
    for item_id, item in existing.items():
        updated = dict(item)
        updated["video"] = scanned.pop(item_id, None)
        movies.append(_with_poster(updated, media_root))
    for item_id, video in scanned.items():
        movies.append(_with_poster({"id": item_id, "type": "movie", "title": Path(video).stem, "poster": None, "video": video}, media_root))
    return movies


def _episodes_for(directory: Optional[Path], existing_episodes: list[dict]) -> list[dict]:
    scanned: dict[tuple[int, int], str] = {}
    unmarked: list[Path] = []
    for path in _media_files(directory) if directory is not None else []:
        parsed = parse_episode(path.name)
        if parsed is None:
            unmarked.append(path)
        else:
            scanned[parsed] = f"series/{directory.name}/{path.name}"
    next_episode = 1
    while (1, next_episode) in scanned:
        next_episode += 1
    for path in unmarked:
        scanned[(1, next_episode)] = f"series/{directory.name}/{path.name}"
        next_episode += 1

    episodes_by_key = {(episode.get("season"), episode.get("episode")): episode for episode in existing_episodes}
    episodes: list[dict] = []
    for key, episode in episodes_by_key.items():
        if not all(isinstance(part, int) for part in key):
            continue
        updated = dict(episode)
        updated["video"] = scanned.pop(key, None)
        episodes.append(updated)
    for (season, episode), video in scanned.items():
        episodes.append({"season": season, "episode": episode, "video": video})
    return sorted(episodes, key=lambda episode: (episode["season"], episode["episode"]))


def _scan_series(media_root: Path, existing: dict[str, dict]) -> list[dict]:
    series_directory = media_root / "series"
    directories = sorted((path for path in series_directory.iterdir() if path.is_dir()), key=lambda path: path.name.casefold()) if series_directory.is_dir() else []
    scanned = {make_id(directory.name): directory for directory in directories}

    series: list[dict] = []
    for item_id, item in existing.items():
        updated = dict(item)
        directory = scanned.pop(item_id, None)
        updated["episodes"] = _episodes_for(directory, updated.get("episodes", []))
        series.append(_with_poster(updated, media_root))
    for item_id, directory in scanned.items():
        series.append(_with_poster({"id": item_id, "type": "series", "title": directory.name, "poster": None, "episodes": _episodes_for(directory, [])}, media_root))
    return series


def scan_catalog(media_root: Path, catalog: list[dict]) -> list[dict]:
    """Return *catalog* synchronized with files below ``movies`` and ``series``."""
    movie_items = {item["id"]: item for item in catalog if item.get("type") == "movie" and item.get("id")}
    series_items = {item["id"]: item for item in catalog if item.get("type") == "series" and item.get("id")}
    other_items = [dict(item) for item in catalog if item.get("type") not in {"movie", "series"}]
    return _scan_movies(media_root, movie_items) + _scan_series(media_root, series_items) + other_items


def main() -> None:
    parser = argparse.ArgumentParser(description="Synchronize a release movie catalog with local media files.")
    parser.add_argument("--root", type=Path, default=Path("release/"), help="Release directory containing config.json and data/movies.json")
    args = parser.parse_args()
    root = args.root
    config = json.loads((root / "config.json").read_text(encoding="utf-8"))
    catalog_path = root / "data" / "movies.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    updated = scan_catalog(root / config["mediaDirectory"], catalog)

    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=catalog_path.parent, delete=False) as temporary:
        json.dump(updated, temporary, ensure_ascii=False, indent=2)
        temporary.write("\n")
        temporary_path = Path(temporary.name)
    temporary_path.replace(catalog_path)


if __name__ == "__main__":
    main()
