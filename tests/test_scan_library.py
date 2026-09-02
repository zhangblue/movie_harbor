import json
import sys
import tempfile
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "release"))

from scan_library import main, scan_catalog


class ScanCatalogTests(unittest.TestCase):
    def test_scan_catalog_keeps_a_legacy_movie_id_matched_by_existing_video_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "movies").mkdir(parents=True)
            (media / "series" / "示例剧").mkdir(parents=True)
            (media / "movies" / "新电影.mp4").touch()
            (media / "series" / "示例剧" / "S01E02.mp4").touch()
            catalog = [{"id": "人工-id", "type": "movie", "title": "人工片名", "description": "保留", "video": "movies/新电影.mp4"}]

            updated = scan_catalog(media, catalog)

            movie = next(item for item in updated if item["id"] == "人工-id")
            self.assertEqual(movie["title"], "人工片名")
            self.assertEqual(movie["description"], "保留")
            self.assertEqual(movie["video"], "movies/新电影.mp4")
            self.assertEqual(len([item for item in updated if item["type"] == "movie"]), 1)
            self.assertEqual(next(item for item in updated if item["type"] == "series")["episodes"][0]["season"], 1)

    def test_scan_catalog_keeps_a_legacy_series_id_matched_by_episode_path(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "series" / "中文剧").mkdir(parents=True)
            (media / "series" / "中文剧" / "S01E02.mp4").touch()
            catalog = [{
                "id": "人工-series-id",
                "type": "series",
                "title": "人工剧名",
                "description": "保留",
                "episodes": [{"season": 1, "episode": 2, "title": "人工集名", "video": "series/中文剧/S01E02.mp4"}],
            }]

            updated = scan_catalog(media, catalog)

            self.assertEqual(len(updated), 1)
            self.assertEqual(updated[0]["id"], "人工-series-id")
            self.assertEqual(updated[0]["description"], "保留")
            self.assertEqual(updated[0]["episodes"][0]["title"], "人工集名")

    def test_scan_catalog_uses_distinct_category_prefixed_ids_for_same_movie_and_series_name(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "movies").mkdir(parents=True)
            (media / "series" / "Foo").mkdir(parents=True)
            (media / "movies" / "Foo.mp4").touch()
            (media / "series" / "Foo" / "S01E01.mp4").touch()

            updated = scan_catalog(media, [])

            self.assertEqual({item["id"] for item in updated}, {"movie-foo", "series-foo"})
            self.assertEqual(len(updated), len({item["id"] for item in updated}))

    def test_scan_catalog_rejects_duplicate_catalog_ids_before_the_frontend_can_receive_them(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            duplicate_ids = [
                {"id": "same", "type": "movie", "title": "Film", "video": None},
                {"id": "same", "type": "series", "title": "Show", "episodes": []},
            ]

            with self.assertRaisesRegex(ValueError, "duplicate catalog id"):
                scan_catalog(media, duplicate_ids)

    def test_scan_catalog_rejects_duplicate_or_invalid_existing_episode_numbers(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "series" / "show").mkdir(parents=True)
            duplicated = [{
                "id": "show", "type": "series", "title": "Show",
                "episodes": [
                    {"season": 1, "episode": 1, "video": None},
                    {"season": 1, "episode": 1, "video": None},
                ],
            }]
            invalid = [{
                "id": "show", "type": "series", "title": "Show",
                "episodes": [{"season": 0, "episode": 1, "video": None}],
            }]

            with self.assertRaisesRegex(ValueError, "duplicate episode"):
                scan_catalog(media, duplicated)
            with self.assertRaisesRegex(ValueError, "invalid episode"):
                scan_catalog(media, invalid)

    def test_scan_catalog_clears_missing_videos_but_keeps_existing_entries(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "movies").mkdir(parents=True)
            (media / "series" / "show").mkdir(parents=True)
            catalog = [
                {"id": "gone-film", "type": "movie", "title": "保留电影", "video": "movies/gone-film.mp4"},
                {
                    "id": "show",
                    "type": "series",
                    "title": "保留剧集",
                    "episodes": [{"season": 2, "episode": 3, "title": "人工标题", "video": "series/show/S02E03.mp4"}],
                },
            ]

            updated = scan_catalog(media, catalog)

            self.assertEqual(updated[0]["title"], "保留电影")
            self.assertIsNone(updated[0]["video"])
            episode = updated[1]["episodes"][0]
            self.assertEqual(episode["title"], "人工标题")
            self.assertIsNone(episode["video"])

    def test_scan_catalog_prefers_jpg_poster_and_assigns_unmarked_files_to_first_season_in_order(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            media = Path(temp_dir) / "movie_resources"
            (media / "movies").mkdir(parents=True)
            (media / "series" / "Unmarked Show").mkdir(parents=True)
            (media / "posters").mkdir(parents=True)
            (media / "movies" / "Poster Film.webm").touch()
            (media / "movies" / "Manual Film.mp4").touch()
            (media / "series" / "Unmarked Show" / "beta.mov").touch()
            (media / "series" / "Unmarked Show" / "alpha.mp4").touch()
            (media / "posters" / "movie-poster-film.webp").touch()
            (media / "posters" / "movie-poster-film.png").touch()
            (media / "posters" / "movie-poster-film.jpg").touch()
            (media / "posters" / "manual-film.jpg").touch()

            updated = scan_catalog(media, [
                {"id": "manual-film", "type": "movie", "title": "人工海报", "poster": "manual-poster.png", "video": "movies/Manual Film.mp4"},
            ])

            film = next(item for item in updated if item["id"] == "movie-poster-film")
            self.assertEqual(film["poster"], "posters/movie-poster-film.jpg")
            manual_film = next(item for item in updated if item["id"] == "manual-film")
            self.assertEqual(manual_film["poster"], "manual-poster.png")
            series = next(item for item in updated if item["type"] == "series")
            self.assertEqual(
                [(episode["season"], episode["episode"], episode["video"]) for episode in series["episodes"]],
                [(1, 1, "series/Unmarked Show/alpha.mp4"), (1, 2, "series/Unmarked Show/beta.mov")],
            )

    def test_main_reads_config_and_replaces_catalog_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "release"
            (root / "data").mkdir(parents=True)
            (root / "movie_resources" / "movies").mkdir(parents=True)
            (root / "movie_resources" / "movies" / "CLI Film.mov").touch()
            (root / "config.json").write_text(json.dumps({"mediaDirectory": "./movie_resources"}), encoding="utf-8")
            (root / "data" / "movies.json").write_text("[]", encoding="utf-8")

            old_argv = sys.argv
            try:
                sys.argv = ["scan_library.py", "--root", str(root)]
                main()
            finally:
                sys.argv = old_argv

            catalog = json.loads((root / "data" / "movies.json").read_text(encoding="utf-8"))
            self.assertEqual(catalog[0]["id"], "movie-cli-film")
            self.assertEqual(catalog[0]["video"], "movies/CLI Film.mov")


if __name__ == "__main__":
    unittest.main()
