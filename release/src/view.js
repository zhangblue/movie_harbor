import { buildMediaUrl, groupEpisodesBySeason } from './catalog.js';

const typeLabels = { all: '全部', movie: '电影', series: '美剧' };

export function getCardPresentation(item) {
  return {
    typeLabel: item.type === 'movie' ? '电影' : '美剧',
    meta: String(item.year ?? ''),
    poster: item.poster,
    fallbackText: item.title,
  };
}

export function getSeriesDetailPresentation(item) {
  return {
    poster: item.poster,
    fallbackText: item.title,
    description: item.description ?? '',
    hasEpisodes: item.episodes.length > 0,
  };
}

export function renderHeader({ activeType, query, onTypeChange, onSearch }) {
  const header = document.querySelector('#site-header');
  const existingInput = header.querySelector('input');
  if (existingInput) {
    const scope = header.querySelector('.search-scope');
    scope.textContent = typeLabels[activeType];
    for (const button of header.querySelectorAll('.type-controls button')) {
      const isActive = button.dataset.type === activeType;
      button.className = isActive ? 'is-active' : '';
      button.setAttribute('aria-pressed', String(isActive));
    }
    if (existingInput.value !== query) existingInput.value = query;
    return;
  }

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
    button.dataset.type = type;
    button.textContent = typeLabels[type];
    button.className = type === activeType ? 'is-active' : '';
    button.setAttribute('aria-pressed', String(type === activeType));
    button.addEventListener('click', () => onTypeChange(type));
    typeControls.append(button);
  }
  const search = document.createElement('label');
  search.className = 'search-control';
  const scope = document.createElement('span');
  scope.className = 'search-scope';
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

function createBackButton(onBack) {
  const button = document.createElement('button');
  button.type = 'button';
  button.className = 'back-button';
  button.textContent = '返回媒体库';
  button.addEventListener('click', onBack);
  return button;
}

export function renderSeriesDetail({ container, item, mediaDirectory, onBack, onOpenEpisode }) {
  container.replaceChildren();
  const presentation = getSeriesDetailPresentation(item);
  const heading = document.createElement('h2');
  heading.textContent = item.title;
  const content = document.createElement('div');
  content.className = 'series-detail';
  content.append(createBackButton(onBack), heading);

  const overview = document.createElement('div');
  overview.className = 'series-overview';
  if (presentation.poster) {
    const poster = document.createElement('img');
    poster.src = buildMediaUrl(mediaDirectory, presentation.poster);
    poster.alt = `${item.title} 海报`;
    poster.addEventListener('error', () => poster.replaceWith(createFallback(presentation.fallbackText)), { once: true });
    overview.append(poster);
  } else {
    overview.append(createFallback(presentation.fallbackText));
  }
  const description = document.createElement('p');
  description.className = 'series-description';
  description.textContent = presentation.description;
  overview.append(description);
  content.append(overview);

  if (!presentation.hasEpisodes) {
    const empty = document.createElement('p');
    empty.className = 'empty-state';
    empty.textContent = '暂未添加剧集';
    content.append(empty);
    container.append(content);
    return;
  }

  const seasons = groupEpisodesBySeason(item.episodes);
  const seasonControls = document.createElement('div');
  seasonControls.className = 'season-controls';
  seasonControls.setAttribute('aria-label', '选择季');
  const episodeControls = document.createElement('div');
  episodeControls.className = 'episode-controls';
  let activeSeason = seasons[0].season;
  const renderEpisodes = () => {
    episodeControls.replaceChildren();
    for (const { season, episodes } of seasons) {
      if (season !== activeSeason) continue;
      for (const episode of episodes) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = `第 ${episode.episode} 集${episode.title ? ` · ${episode.title}` : ''}`;
        button.addEventListener('click', () => onOpenEpisode(episode));
        episodeControls.append(button);
      }
    }
    for (const button of seasonControls.children) {
      button.classList.toggle('is-active', Number(button.dataset.season) === activeSeason);
    }
  };
  for (const { season } of seasons) {
    const button = document.createElement('button');
    button.type = 'button';
    button.dataset.season = String(season);
    button.textContent = `第 ${season} 季`;
    button.addEventListener('click', () => {
      activeSeason = season;
      renderEpisodes();
    });
    seasonControls.append(button);
  }
  content.append(seasonControls, episodeControls);
  container.append(content);
  renderEpisodes();
}

export function renderPlayer({ container, item, episode = null, mediaDirectory, source, onBack }) {
  container.replaceChildren();
  const content = document.createElement('div');
  content.className = 'player-detail';
  const heading = document.createElement('h2');
  heading.textContent = episode ? `${item.title} · 第 ${episode.episode} 集` : item.title;
  content.append(createBackButton(onBack), heading);
  if (typeof source !== 'string' || !source.trim()) {
    const unavailable = document.createElement('p');
    unavailable.className = 'empty-state';
    unavailable.textContent = '没有可用的视频文件。';
    content.append(unavailable);
  } else {
    const video = document.createElement('video');
    video.controls = true;
    video.playsInline = true;
    video.src = buildMediaUrl(mediaDirectory, source);
    video.addEventListener('error', () => {
      document.querySelector('#app-status').textContent = '视频文件不可用或浏览器不支持该格式。';
    });
    content.append(video);
  }
  container.append(content);
}

export function releasePlayer(container) {
  for (const video of container.querySelectorAll('video')) {
    video.pause();
    video.removeAttribute('src');
    video.load();
  }
  container.replaceChildren();
}
