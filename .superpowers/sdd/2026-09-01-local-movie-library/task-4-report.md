# 任务 4：电影播放、美剧详情与资源异常状态

## 变更

- 在 `src/catalog.js` 导出 `getPlayableSource`，仅允许电影本体或美剧剧集的有效播放组合。
- 在 `src/view.js` 增加美剧季/集详情、返回按钮及原生 `<video controls playsinline>` 播放器；视频错误会更新状态区。
- 在 `src/main.js` 接通电影直达播放、美剧详情、剧集播放以及页面返回流程。
- 在 `styles/main.css` 增加详情、剧集选择器与播放器样式。
- 在 `tests/catalog.test.mjs` 按红绿循环新增播放源路径和无效组合测试。

## 测试与验证

- 红灯：`node --test tests/catalog.test.mjs`，按预期因 `getPlayableSource` 尚未导出失败。
- 绿灯：`node --test tests/catalog.test.mjs`，6 项通过。
- 完整自动化：`node --test tests/*.test.mjs`，7 项通过。
- 语法及差异检查：`node --check src/catalog.js && node --check src/view.js && node --check src/main.js && git diff --check`，通过。

## 提交

- 实现提交：`983a674353ff61a808292826b82700de77a36f84`（`feat(播放): 添加电影播放与剧集详情`）。

## 疑虑

- 当前环境没有可连接的浏览器；无法执行简报要求的点击“沉默的羔羊”、播放实际 MP4、以及临时替换路径触发原生视频 `error` 的手工验收。代码已实现该事件处理，需在可用浏览器中补做此项验收。

## 审查修复（2026-09-02）

### 变更

- `validateCatalog` 现在接受 `episodes: []` 的美剧，仍拒绝缺失或非数组的 `episodes`。
- `getSeriesDetailPresentation` 提供详情页所需的唯一海报、与卡片一致的标题文字兜底、简介和剧集可用性；`renderSeriesDetail` 使用这些数据在选季/集控件前渲染海报和简介，并对海报加载失败使用同一兜底。
- 返回媒体库时会清空播放器遗留的状态消息。
- 新增空剧集片单、详情海报/简介/无剧集状态及无海报兜底的 Node 测试。

### 覆盖测试

- 红灯：`node --test tests/catalog.test.mjs`，`validateCatalog accepts a series with no episodes yet` 失败，错误为 `美剧缺少剧集`。
- 绿灯：`node --test tests/catalog.test.mjs`，7/7 通过；`node --test tests/view.test.mjs`，3/3 通过。
- 完整检查：`node --test tests/*.test.mjs && node --check src/catalog.js && node --check src/view.js && node --check src/main.js && git diff --check`。
  输出：10 tests、10 pass、0 fail；三个语法检查及差异检查退出码均为 0。

### 提交

- 修复实现：`a6a1f9266993c80f4a5268c1256469dd5294ae95`（`fix(美剧详情): 展示海报简介并支持空剧集`）。
