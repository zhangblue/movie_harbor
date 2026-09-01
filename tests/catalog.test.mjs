import test from 'node:test';
import assert from 'node:assert/strict';
import { buildMediaUrl, validateCatalog } from '../src/catalog.js';

test('buildMediaUrl joins a configured relative directory and media path', () => {
  assert.equal(
    buildMediaUrl('./movie_resources/', 'movies/film.mp4'),
    './movie_resources/movies/film.mp4',
  );
});

test('validateCatalog accepts a movie and a series with episode videos', () => {
  const result = validateCatalog([
    { id: 'film', type: 'movie', title: '电影', video: 'movies/film.mp4' },
    { id: 'show', type: 'series', title: '美剧', episodes: [{ season: 1, episode: 1, video: 'series/show/s01e01.mp4' }] },
  ]);
  assert.equal(result.length, 2);
});
