import http.client
import sys
import tempfile
import threading
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(ROOT / "release"))

from build_release import build_release
from start import create_server, parse_args


class BuildReleaseTests(unittest.TestCase):
    def test_build_release_copies_runtime_files_and_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "release"
            (source / "data").mkdir(parents=True)
            (source / "src").mkdir()
            (source / "styles").mkdir()
            (source / "release").mkdir()
            (source / "movie_resources").mkdir()
            (source / "movie_resources" / "movies").mkdir(parents=True)
            (source / "index.html").write_text("<title>Movie Harbor</title>", encoding="utf-8")
            (source / "config.json").write_text('{"mediaDirectory":"./movie_resources"}', encoding="utf-8")
            (source / "data" / "movies.json").write_text("[]", encoding="utf-8")
            (source / "src" / "main.js").write_text("console.log('ready')", encoding="utf-8")
            (source / "styles" / "main.css").write_text("body {}", encoding="utf-8")
            (source / "release" / "start.py").write_text("# starter", encoding="utf-8")
            (source / "release" / "scan_library.py").write_text("# scanner", encoding="utf-8")
            (source / "movie_resources" / "movies" / "film.mp4").write_bytes(b"video")
            (source / "README.md").write_text("# Movie Harbor", encoding="utf-8")

            build_release(source, destination)

            self.assertTrue((destination / "start.py").is_file())
            self.assertTrue((destination / "scan_library.py").is_file())
            self.assertTrue((destination / "config.json").is_file())
            self.assertTrue((destination / "movie_resources" / "movies" / "film.mp4").is_file())
            self.assertEqual((destination / "src" / "main.js").read_text(encoding="utf-8"), "console.log('ready')")

    def test_build_release_replaces_generated_outputs_but_keeps_unmanaged_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "output"
            (source / "data").mkdir(parents=True)
            (source / "src").mkdir()
            (source / "styles").mkdir()
            (source / "release").mkdir()
            (source / "movie_resources").mkdir()
            for relative_path in ("index.html", "config.json", "README.md", "data/movies.json", "src/main.js", "styles/main.css", "release/start.py", "release/scan_library.py"):
                path = source / relative_path
                path.write_text(relative_path, encoding="utf-8")
            (destination / "data").mkdir(parents=True)
            (destination / "data" / "obsolete.json").write_text("obsolete", encoding="utf-8")
            (destination / "notes.txt").parent.mkdir(parents=True, exist_ok=True)
            (destination / "notes.txt").write_text("keep", encoding="utf-8")

            build_release(source, destination)

            self.assertFalse((destination / "data" / "obsolete.json").exists())
            self.assertEqual((destination / "notes.txt").read_text(encoding="utf-8"), "keep")

    def test_build_release_creates_an_empty_media_directory_when_the_source_has_no_media(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = Path(temporary) / "output"
            (source / "data").mkdir(parents=True)
            (source / "src").mkdir()
            (source / "styles").mkdir()
            (source / "release").mkdir()
            for relative_path in ("index.html", "config.json", "README.md", "data/movies.json", "src/main.js", "styles/main.css", "release/start.py", "release/scan_library.py"):
                (source / relative_path).write_text(relative_path, encoding="utf-8")

            build_release(source, destination)

            self.assertTrue((destination / "movie_resources").is_dir())

    def test_build_release_preserves_staged_scripts_when_output_is_source_release_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            destination = source / "release"
            (source / "data").mkdir(parents=True)
            (source / "src").mkdir()
            (source / "styles").mkdir()
            (source / "movie_resources").mkdir()
            destination.mkdir()
            for relative_path in ("index.html", "config.json", "README.md", "data/movies.json", "src/main.js", "styles/main.css", "release/start.py", "release/scan_library.py"):
                (source / relative_path).write_text(relative_path, encoding="utf-8")

            build_release(source, destination)

            self.assertEqual((destination / "start.py").read_text(encoding="utf-8"), "release/start.py")
            self.assertEqual((destination / "scan_library.py").read_text(encoding="utf-8"), "release/scan_library.py")
            self.assertTrue((destination / "movie_resources").is_dir())

    def test_build_release_rejects_unsafe_destinations(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            source.mkdir()

            with self.assertRaises(ValueError):
                build_release(source, source)
            with self.assertRaises(ValueError):
                build_release(source, Path())
            with self.assertRaises(ValueError):
                build_release(source, Path("/"))


class ReleaseServerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "movie.mp4").write_bytes(b"0123456789")
        self.server = create_server(self.root, 0)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.thread.join()
        self.server.server_close()
        self.temporary.cleanup()

    def request(self, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.request("GET", "/movie.mp4", headers=headers or {})
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body

    def request_with_duplicate_range_headers(self):
        connection = http.client.HTTPConnection("127.0.0.1", self.server.server_port)
        connection.putrequest("GET", "/movie.mp4")
        connection.putheader("Range", "bytes=0-1")
        connection.putheader("Range", "bytes=2-3")
        connection.endheaders()
        response = connection.getresponse()
        body = response.read()
        connection.close()
        return response, body

    def test_server_returns_single_byte_range_with_streaming_headers(self):
        response, body = self.request({"Range": "bytes=2-2"})

        self.assertEqual(response.status, 206)
        self.assertEqual(response.getheader("Accept-Ranges"), "bytes")
        self.assertEqual(response.getheader("Content-Range"), "bytes 2-2/10")
        self.assertEqual(response.getheader("Content-Length"), "1")
        self.assertEqual(body, b"2")

    def test_server_supports_open_and_suffix_single_ranges(self):
        open_response, open_body = self.request({"Range": "bytes=5-"})
        suffix_response, suffix_body = self.request({"Range": "bytes=-3"})

        self.assertEqual((open_response.status, open_response.getheader("Content-Range"), open_response.getheader("Content-Length"), open_body), (206, "bytes 5-9/10", "5", b"56789"))
        self.assertEqual((suffix_response.status, suffix_response.getheader("Content-Range"), suffix_response.getheader("Content-Length"), suffix_body), (206, "bytes 7-9/10", "3", b"789"))

    def test_server_rejects_invalid_byte_range(self):
        response, body = self.request({"Range": "bytes=10-12"})

        self.assertEqual(response.status, 416)
        self.assertEqual(response.getheader("Content-Range"), "bytes */10")
        self.assertEqual(response.getheader("Content-Length"), "0")
        self.assertEqual(body, b"")

    def test_server_rejects_multiple_or_malformed_ranges(self):
        for header in ("bytes=0-1,3-4", "bytes=abc-def", "items=0-1"):
            response, body = self.request({"Range": header})

            self.assertEqual(response.status, 416)
            self.assertEqual(response.getheader("Content-Range"), "bytes */10")
            self.assertEqual(body, b"")

    def test_server_rejects_duplicate_raw_http_range_headers(self):
        response, body = self.request_with_duplicate_range_headers()

        self.assertEqual(response.status, 416)
        self.assertEqual(response.getheader("Content-Range"), "bytes */10")
        self.assertEqual(response.getheader("Content-Length"), "0")
        self.assertEqual(body, b"")

    def test_server_advertises_ranges_for_full_media_responses(self):
        response, body = self.request()

        self.assertEqual(response.status, 200)
        self.assertEqual(response.getheader("Accept-Ranges"), "bytes")
        self.assertEqual(response.getheader("Content-Length"), "10")
        self.assertEqual(body, b"0123456789")

    def test_start_arguments_allow_automation_without_scan_or_browser(self):
        arguments = parse_args(["--no-scan", "--no-browser", "--port", "8765"])

        self.assertTrue(arguments.no_scan)
        self.assertTrue(arguments.no_browser)
        self.assertEqual(arguments.port, 8765)


if __name__ == "__main__":
    unittest.main()
