import { buildMediaUrl } from './catalog.js';

const typeLabels = { all: '全部', movie: '电影', series: '美剧' };

export function getCardPresentation(item) {
  return {
    typeLabel: item.type === 'movie' ? '电影' : '美剧',
    meta: String(item.year ?? ''),
    poster: item.poster,
    fallbackText: item.title,
  };
}

export function renderHeader({ activeType, query, onTypeChange, onSearch }) {
  const header = document.querySelector('#site-header');
  header.replaceChildren();

  const brand = document.createElement('h1');
  brand.textContent = '电影港湾';
  header.append(brand);

  const controls = document.createElement('div');
  controls.className = 'header-controls';
  const typeControls = document.createElement('div');
  typeControls.className = 'type-controls';
  typeControls.setAttribute('aria-label', '媒体分类');
  for (const type of ['all', 'movie', 'series']) {
    const button = document.createElement('button');
    button.type = 'button';
    button.textContent = typeLabels[type];
    button.className = type === activeType ? 'is-active' : '';
    button.setAttribute('aria-pressed', String(type === activeType));
    button.addEventListener('click', () => onTypeChange(type));
    typeControls.append(button);
  }
  const search = document.createElement('label');
  search.className = 'search-control';
  const scope = document.createElement('span');
  scope.textContent = typeLabels[activeType];
  const input = document.createElement('input');
  input.type = 'search';
  input.value = query;
  input.placeholder = '搜索电影或剧名';
  input.setAttribute('aria-label', '搜索电影或剧名');
  input.addEventListener('input', (event) => onSearch(event.target.value));
  search.append(scope, input);
  controls.append(typeControls, search);
  header.append(controls);
}

function createFallback(text) {
  const fallback = document.createElement('div');
  fallback.className = 'poster-fallback';
  fallback.textContent = text;
  return fallback;
}

export function renderCatalogCards({ container, items, mediaDirectory, onOpen }) {
  container.replaceChildren();
  const grid = document.createElement('div');
  grid.className = 'catalog-grid';
  for (const item of items) {
    const presentation = getCardPresentation(item);
    const card = document.createElement('button');
    card.type = 'button';
    card.className = 'media-card';
    card.addEventListener('click', () => onOpen(item));
    if (presentation.poster) {
      const poster = document.createElement('img');
      poster.src = buildMediaUrl(mediaDirectory, presentation.poster);
      poster.alt = `${item.title} 海报`;
      poster.addEventListener('error', () => poster.replaceWith(createFallback(presentation.fallbackText)), { once: true });
      card.append(poster);
    } else {
      card.append(createFallback(presentation.fallbackText));
    }
    const content = document.createElement('span');
    content.className = 'card-content';
    const title = document.createElement('strong');
    title.textContent = item.title;
    const meta = document.createElement('small');
    meta.textContent = [presentation.typeLabel, presentation.meta].filter(Boolean).join(' · ');
    content.append(title, meta);
    card.append(content);
    grid.append(card);
  }
  container.append(grid);
}

export function renderEmptyState(container, message) {
  container.replaceChildren();
  const empty = document.createElement('p');
  empty.className = 'empty-state';
  empty.textContent = message;
  container.append(empty);
}
