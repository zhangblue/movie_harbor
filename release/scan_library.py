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


def make_id(value: str) -> str:
    """Create a stable, filesystem-friendly identifier from a title or filename."""
    normalized = unicodedata.normalize("NFKD", value).casefold()
    identifier = re.sub(r"[^\w]+", "-", normalized, flags=re.UNICODE).strip("-_")
    return identifier or "untitled"


def parse_episode(filename: str) -> Optional[Tuple[int, int]]:
    """Return the season and episode encoded as SxxExx in *filename*."""
    match = EPISODE_PATTERN.search(filename)
    if match is None:
        return None
    season, episode = int(match.group(1)), int(match.group(2))
    if season < 1 or episode < 1:
        raise ValueError(f"invalid episode number in {filename}")
    return season, episode


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
        scanned_id = make_id(f"movie-{path.stem}")
        video = f"movies/{path.name}"
        if scanned_id in scanned:
            raise ValueError(f"conflicting movie files for {scanned_id}: {scanned[scanned_id]} and {video}")
        scanned[scanned_id] = video

    movies: list[dict] = []
    unmatched = dict(existing)
    for scanned_id, video in scanned.items():
        item = unmatched.pop(scanned_id, None)
        if item is None:
            legacy_id = make_id(Path(video).stem)
            item = unmatched.pop(legacy_id, None)
        if item is None:
            matches = [(item_id, candidate) for item_id, candidate in unmatched.items() if candidate.get("video") == video]
            if len(matches) > 1:
                raise ValueError(f"multiple movie entries reference {video}")
            if matches:
                item_id, item = matches[0]
                del unmatched[item_id]
        if item is None:
            item = {"id": scanned_id, "type": "movie", "title": Path(video).stem, "poster": None}
        updated = dict(item)
        updated["video"] = video
        movies.append(_with_poster(updated, media_root))
    for item in unmatched.values():
        updated = dict(item)
        updated["video"] = None
        movies.append(_with_poster(updated, media_root))
    return movies


def _episodes_for(directory: Optional[Path], existing_episodes: list[dict]) -> list[dict]:
    scanned: dict[tuple[int, int], str] = {}
    unmarked: list[Path] = []
    for path in _media_files(directory) if directory is not None else []:
        parsed = parse_episode(path.name)
        if parsed is None:
            unmarked.append(path)
        else:
            video = f"series/{directory.name}/{path.name}"
            if parsed in scanned:
                raise ValueError(f"conflicting episode files for S{parsed[0]:02d}E{parsed[1]:02d}: {scanned[parsed]} and {video}")
            scanned[parsed] = video
    next_episode = 1
    while (1, next_episode) in scanned:
        next_episode += 1
    for path in unmarked:
        scanned[(1, next_episode)] = f"series/{directory.name}/{path.name}"
        next_episode += 1

    episodes_by_key = {}
    for episode in existing_episodes:
        key = (episode.get("season"), episode.get("episode"))
        if not all(isinstance(part, int) and part > 0 for part in key):
            raise ValueError(f"invalid episode number: {key}")
        if key in episodes_by_key:
            raise ValueError(f"duplicate episode number: {key}")
        episodes_by_key[key] = episode
    episodes: list[dict] = []
    for key, episode in episodes_by_key.items():
        updated = dict(episode)
        updated["video"] = scanned.pop(key, None)
        episodes.append(updated)
    for (season, episode), video in scanned.items():
        episodes.append({"season": season, "episode": episode, "video": video})
    return sorted(episodes, key=lambda episode: (episode["season"], episode["episode"]))


def _scan_series(media_root: Path, existing: dict[str, dict]) -> list[dict]:
    series_directory = media_root / "series"
    directories = sorted((path for path in series_directory.iterdir() if path.is_dir()), key=lambda path: path.name.casefold()) if series_directory.is_dir() else []
    scanned = {make_id(f"series-{directory.name}"): directory for directory in directories}

    series: list[dict] = []
    unmatched = dict(existing)
    for scanned_id, directory in scanned.items():
        item = unmatched.pop(scanned_id, None)
        if item is None:
            legacy_id = make_id(directory.name)
            item = unmatched.pop(legacy_id, None)
        if item is None:
            directory_videos = {f"series/{directory.name}/{path.name}" for path in _media_files(directory)}
            matches = [
                (item_id, candidate)
                for item_id, candidate in unmatched.items()
                if any(episode.get("video") in directory_videos for episode in candidate.get("episodes", []))
            ]
            if len(matches) > 1:
                raise ValueError(f"multiple series entries reference {directory.name}")
            if matches:
                item_id, item = matches[0]
                del unmatched[item_id]
        if item is None:
            item = {"id": scanned_id, "type": "series", "title": directory.name, "poster": None, "episodes": []}
        updated = dict(item)
        updated["episodes"] = _episodes_for(directory, updated.get("episodes", []))
        series.append(_with_poster(updated, media_root))
    for item in unmatched.values():
        updated = dict(item)
        updated["episodes"] = _episodes_for(None, updated.get("episodes", []))
        series.append(_with_poster(updated, media_root))
    return series


def scan_catalog(media_root: Path, catalog: list[dict]) -> list[dict]:
    """Return *catalog* synchronized with files below ``movies`` and ``series``."""
    seen_ids = set()
    for item in catalog:
        item_id = item.get("id")
        if item_id and item_id in seen_ids:
            raise ValueError(f"duplicate catalog id: {item_id}")
        if item_id:
            seen_ids.add(item_id)
    movie_items = {item["id"]: item for item in catalog if item.get("type") == "movie" and item.get("id")}
    series_items = {item["id"]: item for item in catalog if item.get("type") == "series" and item.get("id")}
    other_items = [dict(item) for item in catalog if item.get("type") not in {"movie", "series"}]
    return _scan_movies(media_root, movie_items) + _scan_series(media_root, series_items) + other_items


def main(root: Optional[Path] = None) -> None:
    """Synchronize the catalog at *root*, or parse ``--root`` for CLI use."""
    if root is None:
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
