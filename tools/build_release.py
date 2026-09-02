"""Build the replaceable-program part of a portable media library release."""

import argparse
import shutil
import tempfile
from pathlib import Path


PROGRAM_FILES = ("index.html", "README.md")
PROGRAM_DIRECTORIES = ("src", "styles")
RESOURCE_FILES = (("config.json", "config.json"), ("data/movies.json", "movies.json"))


def _validate_destination(source_root: Path, destination: Path) -> tuple[Path, Path]:
    if not str(destination) or destination == Path():
        raise ValueError("destination must not be empty")
    resolved_source = source_root.resolve()
    resolved_destination = destination.resolve()
    if resolved_destination == resolved_destination.parent:
        raise ValueError("destination must not be a filesystem root")
    if resolved_destination == resolved_source:
        raise ValueError("destination must not equal source_root")
    return resolved_source, resolved_destination


def _stage_release(source_root: Path, staging: Path) -> None:
    program_root = staging / "seven"
    resources_root = staging / "movie_resources"
    program_root.mkdir()
    resources_root.mkdir()
    for relative_path in PROGRAM_FILES:
        source = source_root / relative_path
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, program_root / relative_path)
    for relative_path in PROGRAM_DIRECTORIES:
        source = source_root / relative_path
        if not source.is_dir():
            raise FileNotFoundError(source)
        shutil.copytree(source, program_root / relative_path)
    starter = source_root / "release" / "seven" / "start.py"
    if not starter.is_file():
        raise FileNotFoundError(starter)
    shutil.copy2(starter, program_root / "start.py")

    source_media = source_root / "movie_resources"
    if source_media.exists():
        if not source_media.is_dir():
            raise NotADirectoryError(source_media)
        shutil.copytree(source_media, resources_root, dirs_exist_ok=True)
    for source_relative_path, target_name in RESOURCE_FILES:
        source = source_root / source_relative_path
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, resources_root / target_name)


def _replace_program_directory(staging: Path, destination: Path) -> None:
    program_destination = destination / "seven"
    if program_destination.is_symlink() or program_destination.is_file():
        program_destination.unlink()
    elif program_destination.is_dir():
        shutil.rmtree(program_destination)
    shutil.copytree(staging / "seven", program_destination)


def _seed_resources_if_needed(staging: Path, destination: Path) -> None:
    resource_destination = destination / "movie_resources"
    if not resource_destination.exists():
        shutil.copytree(staging / "movie_resources", resource_destination)
        return
    if not resource_destination.is_dir():
        raise NotADirectoryError(resource_destination)
    # User media is never replaced. Only seed files absent from older releases.
    for _source_relative_path, target_name in RESOURCE_FILES:
        target = resource_destination / target_name
        if not target.exists():
            shutil.copy2(staging / "movie_resources" / target_name, target)


def build_release(source_root: Path, destination: Path) -> None:
    """Build *destination*/seven without replacing the local media library."""
    source_root, destination = _validate_destination(source_root, destination)
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)
    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        _stage_release(source_root, staging)
        destination.mkdir(parents=True, exist_ok=True)
        _replace_program_directory(staging, destination)
        _seed_resources_if_needed(staging, destination)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a portable local media library release.")
    parser.add_argument("--output", type=Path, help="Directory for the generated release (default: source_root/release)")
    arguments = parser.parse_args()
    source_root = Path(__file__).resolve().parents[1]
    destination = arguments.output if arguments.output is not None else source_root / "release"
    build_release(source_root, destination)
    print(f"Built release program in {destination / 'seven'}")


if __name__ == "__main__":
    main()
