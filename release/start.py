"""Start a local release server."""

import argparse
import os
import re
import webbrowser
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import BinaryIO, Optional, Tuple

BYTE_RANGE_PATTERN = re.compile(r"bytes=(\d*)-(\d*)$")


class RangeRequestHandler(SimpleHTTPRequestHandler):
    """Serve static files and honor one RFC 7233 byte range per request."""

    _range: Optional[Tuple[int, int]] = None

    def end_headers(self) -> None:
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def _parse_range(self, header: str, size: int) -> Optional[Tuple[int, int]]:
        match = BYTE_RANGE_PATTERN.fullmatch(header)
        if match is None:
            return None
        first, last = match.groups()
        if not first and not last:
            return None
        try:
            if not first:
                suffix_length = int(last)
                if suffix_length <= 0 or size == 0:
                    return None
                return max(size - suffix_length, 0), size - 1

            start = int(first)
            if start >= size:
                return None
            end = size - 1 if not last else min(int(last), size - 1)
        except ValueError:
            return None
        return (start, end) if end >= start else None

    def send_head(self) -> Optional[BinaryIO]:
        self._range = None
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()

        content_type = self.guess_type(path)
        try:
            file = open(path, "rb")
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None

        size = os.fstat(file.fileno()).st_size
        requested_ranges = self.headers.get_all("Range")
        if requested_ranges is not None:
            selected_range = self._parse_range(requested_ranges[0], size) if len(requested_ranges) == 1 else None
            if selected_range is None:
                file.close()
                self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
                self.send_header("Content-Range", f"bytes */{size}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return None
            start, end = selected_range
            self._range = selected_range
            self.send_response(HTTPStatus.PARTIAL_CONTENT)
            self.send_header("Content-type", content_type)
            self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
            self.send_header("Content-Length", str(end - start + 1))
            self.end_headers()
            file.seek(start)
            return file

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", content_type)
        self.send_header("Content-Length", str(size))
        self.end_headers()
        return file

    def copyfile(self, source: BinaryIO, outputfile: BinaryIO) -> None:
        if self._range is None:
            super().copyfile(source, outputfile)
            return

        remaining = self._range[1] - self._range[0] + 1
        while remaining:
            chunk = source.read(min(64 * 1024, remaining))
            if not chunk:
                break
            try:
                outputfile.write(chunk)
            except (BrokenPipeError, ConnectionResetError):
                return
            remaining -= len(chunk)


def create_server(root: Path, port: int) -> ThreadingHTTPServer:
    """Return a loopback-only static server rooted at *root*."""
    handler = partial(RangeRequestHandler, directory=str(root))
    return ThreadingHTTPServer(("127.0.0.1", port), handler)


def parse_args(arguments: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Serve a local media library release.")
    parser.add_argument("--port", type=int, default=8000, help="Loopback port to listen on (default: 8000)")
    parser.add_argument("--no-browser", action="store_true", help="Do not open the site in a browser")
    return parser.parse_args(arguments)


def main() -> None:
    arguments = parse_args()
    release_root = Path(__file__).resolve().parent
    server = create_server(release_root, arguments.port)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"Serving release at {url}")
    if not arguments.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
