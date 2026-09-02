"""Build a portable copy of the local media library."""

import argparse
import shutil
import tempfile
from pathlib import Path


RUNTIME_FILES = ("index.html", "config.json", "README.md")
RUNTIME_DIRECTORIES = ("data", "src", "styles", "movie_resources")
RUNTIME_SCRIPTS = ("start.py", "scan_library.py")


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


def _stage_runtime(source_root: Path, staging: Path) -> None:
    for relative_path in RUNTIME_FILES:
        source = source_root / relative_path
        if not source.is_file():
            raise FileNotFoundError(source)
        shutil.copy2(source, staging / relative_path)

    for relative_path in RUNTIME_DIRECTORIES:
        source = source_root / relative_path
        if relative_path == "movie_resources" and not source.exists():
            (staging / relative_path).mkdir()
            continue
        if not source.is_dir():
            raise FileNotFoundError(source)
        shutil.copytree(source, staging / relative_path)

    for script_name in RUNTIME_SCRIPTS:
        source = source_root / "release" / script_name
        if not source.is_file():
            raise FileNotFoundError(source)
        (staging / "release").mkdir(exist_ok=True)
        shutil.copy2(source, staging / "release" / script_name)


def _remove_generated_output(destination: Path) -> None:
    for relative_path in (*RUNTIME_FILES, *RUNTIME_DIRECTORIES, *RUNTIME_SCRIPTS):
        output = destination / relative_path
        if output.is_symlink() or output.is_file():
            output.unlink()
        elif output.is_dir():
            shutil.rmtree(output)


def build_release(source_root: Path, destination: Path) -> None:
    """Copy the runtime and local media from *source_root* into *destination*."""
    source_root, destination = _validate_destination(source_root, destination)
    if not source_root.is_dir():
        raise FileNotFoundError(source_root)

    with tempfile.TemporaryDirectory() as temporary:
        staging = Path(temporary)
        _stage_runtime(source_root, staging)
        destination.mkdir(parents=True, exist_ok=True)
        _remove_generated_output(destination)

        for relative_path in RUNTIME_FILES:
            shutil.copy2(staging / relative_path, destination / relative_path)
        for relative_path in RUNTIME_DIRECTORIES:
            shutil.copytree(staging / relative_path, destination / relative_path)
        for script_name in RUNTIME_SCRIPTS:
            shutil.copy2(staging / "release" / script_name, destination / script_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a portable local media library release.")
    parser.add_argument("--output", type=Path, help="Directory for the generated release (default: source_root/release)")
    arguments = parser.parse_args()
    source_root = Path(__file__).resolve().parents[1]
    destination = arguments.output if arguments.output is not None else source_root / "release"
    build_release(source_root, destination)
    print(f"Built release in {destination}")


if __name__ == "__main__":
    main()
