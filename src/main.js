import { filterCatalog, getPlayableSource, validateCatalog } from './catalog.js';
import { renderCatalogCards, renderEmptyState, renderHeader, renderPlayer, renderSeriesDetail } from './view.js';

const state = { activeType: 'all', query: '', selectedItem: null };
const header = document.querySelector('#site-header');
const catalogView = document.querySelector('#catalog-view');
const detailView = document.querySelector('#detail-view');
const playerView = document.querySelector('#player-view');
const status = document.querySelector('#app-status');

function showView(view) {
  catalogView.hidden = view !== catalogView;
  detailView.hidden = view !== detailView;
  playerView.hidden = view !== playerView;
}

function render(items, mediaDirectory) {
  status.textContent = '';
  showView(catalogView);
  renderHeader({
    activeType: state.activeType,
    query: state.query,
    onTypeChange(type) {
      state.activeType = type;
      render(items, mediaDirectory);
    },
    onSearch(query) {
      state.query = query;
      render(items, mediaDirectory);
    },
  });
  const filteredItems = filterCatalog(items, state.activeType, state.query);
  if (filteredItems.length === 0) {
    renderEmptyState(catalogView, '当前分类下无匹配内容。');
    return;
  }
  renderCatalogCards({
    container: catalogView,
    items: filteredItems,
    mediaDirectory,
    onOpen(item) {
      state.selectedItem = item;
      if (item.type === 'movie') openPlayer(items, mediaDirectory, item);
      else openSeries(items, mediaDirectory, item);
    },
  });
}

function openSeries(items, mediaDirectory, item) {
  status.textContent = '';
  renderSeriesDetail({
    container: detailView,
    item,
    mediaDirectory,
    onBack: () => render(items, mediaDirectory),
    onOpenEpisode: (episode) => openPlayer(items, mediaDirectory, item, episode),
  });
  showView(detailView);
}

function openPlayer(items, mediaDirectory, item, episode = null) {
  status.textContent = '';
  let source = null;
  try {
    source = getPlayableSource(item, episode);
  } catch (error) {
    status.textContent = error.message;
  }
  renderPlayer({
    container: playerView,
    item,
    episode,
    mediaDirectory,
    source,
    onBack: () => episode ? openSeries(items, mediaDirectory, item) : render(items, mediaDirectory),
  });
  showView(playerView);
}

async function loadCatalog() {
  try {
    const [configResponse, catalogResponse] = await Promise.all([
      fetch('./config.json'),
      fetch('./data/movies.json'),
    ]);
    if (!configResponse.ok || !catalogResponse.ok) throw new Error('资源请求失败');
    const [config, catalog] = await Promise.all([configResponse.json(), catalogResponse.json()]);
    if (typeof config.mediaDirectory !== 'string') throw new Error('媒体目录无效');
    render(validateCatalog(catalog), config.mediaDirectory);
  } catch (error) {
    renderEmptyState(catalogView, '无法读取媒体库，请检查配置文件和片单。');
    status.textContent = error.message;
  }
}

loadCatalog();
