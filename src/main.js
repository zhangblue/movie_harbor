import { filterCatalog, validateCatalog } from './catalog.js';
import { renderCatalogCards, renderEmptyState, renderHeader } from './view.js';

const state = { activeType: 'all', query: '', selectedItem: null };
const header = document.querySelector('#site-header');
const catalogView = document.querySelector('#catalog-view');
const status = document.querySelector('#app-status');

function render(items, mediaDirectory) {
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
      status.textContent = '播放与剧集详情将在后续版本提供。';
    },
  });
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
