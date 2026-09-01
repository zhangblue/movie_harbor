import test from 'node:test';
import assert from 'node:assert/strict';
import { getCardPresentation } from '../src/view.js';

test('getCardPresentation labels series and creates a text fallback without a poster', () => {
  assert.deepEqual(
    getCardPresentation({ type: 'series', title: '绝命毒师', year: 2008, poster: null }),
    { typeLabel: '美剧', meta: '2008', poster: null, fallbackText: '绝命毒师' },
  );
});
