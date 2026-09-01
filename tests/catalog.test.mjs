import test from 'node:test';
import assert from 'node:assert/strict';
import {
  buildMediaUrl,
  filterCatalog,
  groupEpisodesBySeason,
  validateCatalog,
} from '../src/catalog.js';

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

const items = [
  { id: 'film', type: 'movie', title: '沉默的羔羊', video: 'a.mp4' },
  { id: 'show', type: 'series', title: '绝命毒师', episodes: [
    { season: 2, episode: 1, title: '七三七', video: 's02e01.mp4' },
    { season: 1, episode: 2, title: '猫之袋', video: 's01e02.mp4' },
  ] },
];

test('filterCatalog searches names only inside the active type', () => {
  assert.deepEqual(filterCatalog(items, 'movie', '绝命'), []);
  assert.deepEqual(filterCatalog(items, 'all', '绝命').map((item) => item.id), ['show']);
  assert.deepEqual(filterCatalog(items, 'series', '猫之袋'), []);
});

test('groupEpisodesBySeason sorts seasons and episodes numerically', () => {
  assert.deepEqual(groupEpisodesBySeason(items[1].episodes), [
    { season: 1, episodes: [items[1].episodes[1]] },
    { season: 2, episodes: [items[1].episodes[0]] },
  ]);
});
