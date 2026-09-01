import test from 'node:test';
import assert from 'node:assert/strict';
import { getCardPresentation, getSeriesDetailPresentation, renderHeader, renderPlayer } from '../src/view.js';

class FakeElement {
  constructor(tagName) {
    this.tagName = tagName;
    this.children = [];
    this.listeners = new Map();
    this.dataset = {};
  }

  append(...children) {
    for (const child of children) child.parentNode = this;
    this.children.push(...children);
  }

  replaceChildren(...children) {
    for (const child of children) child.parentNode = this;
    this.children = children;
  }

  setAttribute() {}

  addEventListener(type, listener) {
    this.listeners.set(type, listener);
  }

  emit(type) {
    this.listeners.get(type)({ target: this });
  }

  querySelector(selector) {
    return this.querySelectorAll(selector)[0] ?? null;
  }

  querySelectorAll(selector) {
    const matches = [];
    const visit = (element) => {
      const classNames = element.className?.split(' ') ?? [];
      const matchesSelector = selector === element.tagName
        || (selector.startsWith('.') && classNames.includes(selector.slice(1)))
        || (selector === '.type-controls button' && element.tagName === 'button'
          && element.parentNode?.className === 'type-controls');
      if (matchesSelector) matches.push(element);
      for (const child of element.children) visit(child);
    };
    for (const child of this.children) visit(child);
    return matches;
  }
}

function withFakeDocument(run) {
  const originalDocument = globalThis.document;
  const header = new FakeElement('header');
  const status = new FakeElement('status');
  globalThis.document = {
    createElement: (tagName) => new FakeElement(tagName),
    querySelector(selector) {
      if (selector === '#site-header') return header;
      if (selector === '#app-status') return status;
      return null;
    },
  };
  try {
    run({ header, status });
  } finally {
    globalThis.document = originalDocument;
  }
}

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

test('renderHeader keeps one focused input through consecutive search queries', () => {
  withFakeDocument(({ header }) => {
    const queries = [];
    const callbacks = {
      activeType: 'all',
      onTypeChange() {},
      onSearch(query) { queries.push(query); },
    };
    renderHeader({ ...callbacks, query: '' });
    const input = header.querySelector('input');

    for (const query of ['绝', '绝命']) {
      input.value = query;
      input.selectionStart = query.length;
      input.selectionEnd = query.length;
      input.emit('input');
      renderHeader({ ...callbacks, query });
      assert.equal(header.querySelector('input'), input);
      assert.equal(input.value, query);
      assert.equal(input.selectionStart, query.length);
      assert.equal(input.selectionEnd, query.length);
    }
    assert.deepEqual(queries, ['绝', '绝命']);
  });
});

test('renderPlayer shows an unavailable state instead of creating a broken video for a missing source', () => {
  withFakeDocument(() => {
    const container = new FakeElement('section');
    renderPlayer({
      container,
      item: { type: 'movie', title: '缺片电影' },
      mediaDirectory: './movie_resources',
      source: null,
      onBack() {},
    });

    assert.equal(container.querySelector('video'), null);
    assert.ok(container.querySelector('p'));
  });
});
