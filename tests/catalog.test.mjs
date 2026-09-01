import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import {
  buildMediaUrl,
  filterCatalog,
  getPlayableSource,
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

test('validateCatalog accepts a series with no episodes yet', () => {
  const result = validateCatalog([
    { id: 'unreleased-show', type: 'series', title: '待播美剧', episodes: [] },
  ]);
  assert.deepEqual(result, [
    { id: 'unreleased-show', type: 'series', title: '待播美剧', episodes: [] },
  ]);
});

test('validateCatalog keeps entries whose movie or episode video has not been added yet', () => {
  const catalog = [
    { id: 'unavailable-film', type: 'movie', title: '缺片电影', video: '' },
    {
      id: 'unavailable-show',
      type: 'series',
      title: '缺片美剧',
      episodes: [
        { season: 1, episode: 1 },
        { season: 1, episode: 2, video: '' },
      ],
    },
  ];

  assert.deepEqual(validateCatalog(catalog), catalog);
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

test('getPlayableSource returns an item video and an episode video', () => {
  assert.equal(getPlayableSource(items[0]), 'a.mp4');
  assert.equal(getPlayableSource(items[1], items[1].episodes[0]), 's02e01.mp4');
});

test('getPlayableSource rejects invalid item and episode combinations', () => {
  assert.throws(() => getPlayableSource(items[1]));
  assert.throws(() => getPlayableSource(items[0], { video: 'episode.mp4' }));
});

test('getPlayableSource clearly rejects a missing or empty video only when it is opened', () => {
  assert.throws(
    () => getPlayableSource({ id: 'film', type: 'movie', title: '缺片电影' }),
    /没有可用的视频文件/,
  );
  assert.throws(
    () => getPlayableSource({ id: 'film', type: 'movie', title: '缺片电影', video: '  ' }),
    /没有可用的视频文件/,
  );
  assert.throws(
    () => getPlayableSource(
      { id: 'show', type: 'series', title: '缺片美剧', episodes: [] },
      { season: 1, episode: 1, video: '' },
    ),
    /没有可用的视频文件/,
  );
});

test('the default catalog ships a series episode backed by its bundled movie demo source', () => {
  const catalog = JSON.parse(readFileSync(new URL('../data/movies.json', import.meta.url), 'utf8'));
  const movie = catalog.find((item) => item.type === 'movie');
  const series = catalog.find((item) => item.type === 'series');

  assert.ok(series, '默认片单应包含美剧示例');
  assert.ok(series.episodes.length > 0, '美剧示例应包含可选剧集');
  assert.equal(series.episodes[0].video, movie.video);
});
