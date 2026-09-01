# 本地电影与美剧收藏网站实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 构建一个由相对媒体目录配置和本地 JSON 片单驱动的、支持电影与美剧浏览、分类搜索、选集和播放的无登录静态网站。

**架构：** 浏览器加载 `config.json`，再加载 `data/movies.json`；`src/catalog.js` 负责验证和筛选条目，`src/view.js` 只将状态渲染为 DOM，`src/main.js` 管理页面状态、路由和播放器事件。视频、海报与数据均按 `config.mediaDirectory` 组合成同源 URL，避免浏览器访问任意绝对文件路径。

**技术栈：** 原生 HTML、CSS、ES modules、HTML5 video、Node 内置 `node:test`。

---

## 文件结构

- 创建：`config.json` — 声明相对于站点根目录的媒体目录。
- 创建：`data/movies.json` — 当前本地影片的实际片单，以及电影与美剧条目的数据约定示例字段。
- 创建：`index.html` — 单页应用挂载点、无障碍状态区和 module 入口。
- 创建：`styles/main.css` — 深色影院风格、响应式网格、详情、播放器和错误/空状态样式。
- 创建：`src/catalog.js` — 纯函数：验证片单、规范化目录路径、构建媒体 URL、按分类与名称搜索、按季分组剧集。
- 创建：`src/view.js` — 纯 DOM 渲染：导航、搜索、卡片网格、剧集详情、播放器和状态消息。
- 创建：`src/main.js` — 获取配置与片单、管理当前分类/查询/详情/播放器状态，并绑定交互事件。
- 创建：`tests/catalog.test.mjs` — `catalog.js` 的节点单元测试。
- 创建：`README.md` — 运行方式、添加电影/美剧/海报的精确步骤，以及数据格式说明。

### 任务 1：媒体配置、实际片单和目录模型

**文件：**
- 创建：`config.json`
- 创建：`data/movies.json`
- 测试：`tests/catalog.test.mjs`

- [ ] **步骤 1：编写媒体 URL 与数据验证的失败测试**

```js
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
```

- [ ] **步骤 2：运行测试并确认失败**

运行：`node --test tests/catalog.test.mjs`

预期：FAIL，提示找不到 `src/catalog.js`。

- [ ] **步骤 3：创建配置、片单和最小目录函数**

创建 `config.json`：

```json
{ "mediaDirectory": "./movie_resources" }
```

创建 `data/movies.json`，以现有文件作为首个真实条目：

```json
[
  {
    "id": "silence-of-the-lambs",
    "type": "movie",
    "title": "沉默的羔羊",
    "year": 1991,
    "genres": ["惊悚", "剧情"],
    "description": "一部心理惊悚电影。",
    "poster": null,
    "video": "沉默的羔羊.1080p.BD中英双字[66影视www.66Ys.Co].mp4"
  }
]
```

创建 `src/catalog.js` 并实现这些导出：

```js
export function buildMediaUrl(mediaDirectory, relativePath) {
  const base = mediaDirectory.replace(/\/+$/, '');
  const path = relativePath.replace(/^\/+/, '');
  return `${base}/${path}`;
}

export function validateCatalog(items) {
  if (!Array.isArray(items)) throw new Error('片单必须是数组');
  const ids = new Set();
  for (const item of items) {
    if (!item?.id || !item?.title || !['movie', 'series'].includes(item.type) || ids.has(item.id)) {
      throw new Error('片单条目无效');
    }
    ids.add(item.id);
    if (item.type === 'movie' && typeof item.video !== 'string') throw new Error('电影缺少视频');
    if (item.type === 'series' && (!Array.isArray(item.episodes) || item.episodes.length === 0)) throw new Error('美剧缺少剧集');
    for (const episode of item.episodes ?? []) {
      if (!Number.isInteger(episode.season) || episode.season < 1 || !Number.isInteger(episode.episode) || episode.episode < 1 || typeof episode.video !== 'string') {
        throw new Error('剧集条目无效');
      }
    }
  }
  return items;
}
```

- [ ] **步骤 4：运行测试确认通过**

运行：`node --test tests/catalog.test.mjs`

预期：PASS，两个测试都通过。

- [ ] **步骤 5：Commit**

当前项目按用户要求暂不使用 Git；跳过提交，保留未提交文件供用户后续初始化仓库。

### 任务 2：分类限定搜索与美剧剧集模型

**文件：**
- 创建：`src/catalog.js`
- 修改：`tests/catalog.test.mjs`

- [ ] **步骤 1：添加失败的分类搜索与剧集分组测试**

```js
import { filterCatalog, groupEpisodesBySeason } from '../src/catalog.js';

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
```

- [ ] **步骤 2：运行测试并确认失败**

运行：`node --test tests/catalog.test.mjs`

预期：FAIL，提示 `filterCatalog` 与 `groupEpisodesBySeason` 尚未导出。

- [ ] **步骤 3：实现不搜索集名的筛选与分组函数**

在 `src/catalog.js` 增加：

```js
export function filterCatalog(items, activeType, query) {
  const normalizedQuery = query.trim().toLocaleLowerCase('zh-CN');
  return items.filter((item) => {
    const inActiveType = activeType === 'all' || item.type === activeType;
    return inActiveType && item.title.toLocaleLowerCase('zh-CN').includes(normalizedQuery);
  });
}

export function groupEpisodesBySeason(episodes) {
  const seasons = new Map();
  for (const episode of episodes) {
    seasons.set(episode.season, [...(seasons.get(episode.season) ?? []), episode]);
  }
  return [...seasons.entries()]
    .sort(([left], [right]) => left - right)
    .map(([season, seasonEpisodes]) => ({
      season,
      episodes: seasonEpisodes.sort((left, right) => left.episode - right.episode),
    }));
}
```

- [ ] **步骤 4：运行测试确认通过**

运行：`node --test tests/catalog.test.mjs`

预期：PASS，所有分类、名称和季集排序测试通过。

- [ ] **步骤 5：Commit**

当前项目按用户要求暂不使用 Git；跳过提交。

### 任务 3：应用骨架与收藏网格

**文件：**
- 创建：`index.html`
- 创建：`styles/main.css`
- 创建：`src/view.js`
- 创建：`src/main.js`

- [ ] **步骤 1：为关键渲染单元添加失败测试**

创建 `tests/view.test.mjs`：

```js
import test from 'node:test';
import assert from 'node:assert/strict';
import { getCardPresentation } from '../src/view.js';

test('getCardPresentation labels series and creates a text fallback without a poster', () => {
  assert.deepEqual(
    getCardPresentation({ type: 'series', title: '绝命毒师', year: 2008, poster: null }),
    { typeLabel: '美剧', meta: '2008', poster: null, fallbackText: '绝命毒师' },
  );
});
```

- [ ] **步骤 2：运行测试并确认失败**

运行：`node --test tests/view.test.mjs`

预期：FAIL，提示找不到 `src/view.js`。

- [ ] **步骤 3：建立挂载点并实现卡片和搜索控件渲染**

创建 `index.html`，确保包含：

```html
<main class="app-shell">
  <header id="site-header"></header>
  <section id="catalog-view"></section>
  <section id="detail-view" hidden></section>
  <section id="player-view" hidden></section>
  <p id="app-status" role="status" aria-live="polite"></p>
</main>
<script type="module" src="./src/main.js"></script>
```

在 `src/view.js` 中定义：

```js
export function renderHeader({ activeType, query, onTypeChange, onSearch }) {}
export function renderCatalogCards({ container, items, mediaDirectory, onOpen }) {}
export function renderEmptyState(container, message) {}
export function getCardPresentation(item) {}
```

`getCardPresentation` 对电影返回 `typeLabel: '电影'`，对剧集返回 `typeLabel: '美剧'`；它返回 `meta: String(item.year ?? '')`、原始 `poster` 与 `fallbackText: item.title`。每张卡片使用 `button`，显示这些数据；`poster` 为 `null` 或加载失败时渲染包含 `fallbackText` 的 `.poster-fallback`，不生成破损图片。搜索框的 placeholder 固定为“搜索电影或剧名”，旁边显示当前范围“全部”“电影”或“美剧”。

在 `src/main.js` 中使用 `fetch('./config.json')` 与 `fetch('./data/movies.json')`，检查 `response.ok`，执行 `validateCatalog`，并以 `{ activeType: 'all', query: '', selectedItem: null }` 初始化状态。分类切换与输入事件调用 `filterCatalog`，保留查询但依据新分类重算结果。

- [ ] **步骤 4：运行单元测试并进行浏览器验收**

运行：`node --test tests/catalog.test.mjs tests/view.test.mjs`

预期：PASS。

然后在项目根目录运行：`python3 -m http.server 8000`，打开 `http://localhost:8000`。

预期：能看到“全部 / 电影 / 美剧”、搜索框和当前的“沉默的羔羊”卡片；切换分类后搜索范围标签变化；在电影分类搜索一个剧名显示空状态。

- [ ] **步骤 5：Commit**

当前项目按用户要求暂不使用 Git；跳过提交。

### 任务 4：电影播放、美剧详情与资源异常状态

**文件：**
- 修改：`src/view.js`
- 修改：`src/main.js`
- 修改：`styles/main.css`
- 修改：`tests/catalog.test.mjs`

- [ ] **步骤 1：添加视频资源路径的失败测试**

```js
import { getPlayableSource } from '../src/catalog.js';

test('getPlayableSource returns an item video and an episode video', () => {
  assert.equal(getPlayableSource(items[0]), 'a.mp4');
  assert.equal(getPlayableSource(items[1], items[1].episodes[0]), 's02e01.mp4');
});

test('getPlayableSource rejects invalid item and episode combinations', () => {
  assert.throws(() => getPlayableSource(items[1]));
  assert.throws(() => getPlayableSource(items[0], { video: 'episode.mp4' }));
});
```

- [ ] **步骤 2：运行测试并确认失败**

运行：`node --test tests/catalog.test.mjs`

预期：FAIL，提示 `getPlayableSource` 尚未导出。

- [ ] **步骤 3：实现播放页、剧集详情和错误处理**

在 `src/catalog.js` 增加：

```js
export function getPlayableSource(item, episode = null) {
  if (item.type === 'movie' && episode === null) return item.video;
  if (item.type === 'series' && episode !== null) return episode.video;
  throw new Error('请选择可播放的视频');
}
```

在 `src/view.js` 增加 `renderSeriesDetail` 和 `renderPlayer`。前者使用 `groupEpisodesBySeason` 渲染季按钮与集按钮，并在 `episodes.length === 0` 时呈现“暂未添加剧集”。后者创建 `<video controls playsinline>`，将 `src` 设为 `buildMediaUrl(mediaDirectory, source)`，监听 `error` 并将 `#app-status` 更新为“视频文件不可用或浏览器不支持该格式。”；两种页面均提供返回按钮。

在 `src/main.js` 中，电影点击直接调用 `openPlayer(item)`；美剧点击调用 `openSeries(item)`，集按钮调用 `openPlayer(item, episode)`。配置或片单的 fetch/解析/验证异常被捕获后，调用 `renderEmptyState(catalogView, '无法读取媒体库，请检查配置文件和片单。')`。

- [ ] **步骤 4：运行测试并手工验证播放流程**

运行：`node --test tests/catalog.test.mjs`

预期：PASS。

然后运行：`python3 -m http.server 8000`，打开 `http://localhost:8000`，点击“沉默的羔羊”。

预期：出现带原生控制条的播放器；现有 MP4 可播放。临时将 `video` 改为不存在的相对路径并刷新，预期状态区显示“视频文件不可用或浏览器不支持该格式。”，完成后立刻恢复实际文件名。

- [ ] **步骤 5：Commit**

当前项目按用户要求暂不使用 Git；跳过提交。

### 任务 5：响应式视觉收尾与使用文档

**文件：**
- 修改：`styles/main.css`
- 创建：`README.md`

- [ ] **步骤 1：添加媒体库使用说明**

创建 `README.md`，包含：以 `python3 -m http.server 8000` 运行、`config.json` 的相对目录限制、电影视频与海报的添加方法、美剧剧集目录与 `episodes` 格式，以及浏览器不支持媒体编码时的排查方式。

- [ ] **步骤 2：实现响应式布局与可见焦点**

在 `styles/main.css` 实现 5 列桌面卡片网格、平板 3 列和小屏 2 列；小屏将搜索框置于导航下一行，播放器宽度限制为内容区宽度。为所有可操作的 `button`、搜索框和剧集按钮提供 `:focus-visible` 描边；为海报卡片、空状态、错误状态、详情和播放器分别提供视觉层次。

- [ ] **步骤 3：执行最终验证**

运行：`node --test tests/catalog.test.mjs tests/view.test.mjs`

预期：PASS。

运行：`python3 -m http.server 8000`，分别以桌面宽度和 390px 宽度检查页面。

预期：分类、范围限定搜索、电影播放、美剧选集、海报兜底、无结果和加载错误状态均可用，且没有横向滚动。

- [ ] **步骤 4：Commit**

当前项目按用户要求暂不使用 Git；跳过提交。

## 计划自检

- 规格覆盖：任务 1 覆盖配置/数据与资源边界；任务 2 覆盖分类限定名称搜索和剧集数据；任务 3 覆盖收藏页面；任务 4 覆盖播放、选集与异常；任务 5 覆盖响应式、可访问性与运行说明。
- 完整性：所有实现步骤均给出具体文件、函数、数据或命令。
- 类型一致性：`movie`、`series`、`activeType`（`all | movie | series`）、`mediaDirectory`、`episodes` 与 `getPlayableSource` 在全部任务中使用相同名称。
