# Movie Harbor 开发约定

## 项目定位

这是一个本地个人媒体库网站。前端展示电影和美剧；Python 启动器仅负责本地静态资源与视频 HTTP Range 响应，不包含登录、数据库或自动扫描逻辑。

## 发布目录边界

发布包必须保持以下结构：

```text
release/
├── seven/            # 可替换的程序代码
└── movie_resources/  # 用户持久化数据
```

- `release/seven/` 包含 `start.py`、`index.html`、`src/`、`styles/` 与发布说明；升级时允许完整替换该目录。
- `release/movie_resources/` 包含 `config.json`、`movies.json`、视频、剧集和海报；不得在构建或代码更新时删除、覆盖或扫描其中的用户资源。
- 启动命令为 `python3 release/seven/start.py`。
- 本地媒体 URL 必须通过启动器映射到 `movie_resources`，以便前端可继续读取 `/config.json`、`/data/movies.json` 和 `/movie_resources/...`。

## 媒体维护

- 片单由用户手动维护：`release/movie_resources/movies.json`。
- 媒体根目录由 `release/movie_resources/config.json` 配置；默认值为 `./movie_resources`。
- 片单中的海报和视频路径均相对于 `mediaDirectory`。
- 不添加自动扫描、自动写入片单或用户登录功能，除非需求明确要求。

## 构建与验证

- 使用 `python3 tools/build_release.py` 重建 `release/seven/`。
- 构建器在首次生成或旧版迁移时可以补齐缺失的 `config.json`、`movies.json`，但不得修改已有的同名文件或媒体资源。
- 修改发布服务或构建逻辑后，运行：

  ```bash
  python3 -m unittest tests/test_build_release.py -v
  node --test
  ```

- 保持视频 HTTP Range 支持，确保浏览器拖动进度条能够正常工作。
