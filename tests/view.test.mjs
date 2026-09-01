import test from 'node:test';
import assert from 'node:assert/strict';
import { getCardPresentation, getSeriesDetailPresentation } from '../src/view.js';

test('getCardPresentation labels series and creates a text fallback without a poster', () => {
  assert.deepEqual(
    getCardPresentation({ type: 'series', title: '绝命毒师', year: 2008, poster: null }),
    { typeLabel: '美剧', meta: '2008', poster: null, fallbackText: '绝命毒师' },
  );
});

test('getSeriesDetailPresentation exposes poster, description, and episode availability', () => {
  assert.deepEqual(
    getSeriesDetailPresentation({
      type: 'series',
      title: '绝命毒师',
      poster: 'series/breaking-bad.jpg',
      description: '一名教师的人生转折。',
      episodes: [],
    }),
    {
      poster: 'series/breaking-bad.jpg',
      fallbackText: '绝命毒师',
      description: '一名教师的人生转折。',
      hasEpisodes: false,
    },
  );
});

test('getSeriesDetailPresentation uses the title fallback when no poster exists', () => {
  assert.deepEqual(
    getSeriesDetailPresentation({ type: 'series', title: '无海报美剧', poster: null, episodes: [] }),
    { poster: null, fallbackText: '无海报美剧', description: '', hasEpisodes: false },
  );
});
