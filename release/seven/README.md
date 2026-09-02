# 电影港湾

电影港湾是个人本地媒体库：展示收藏的电影与美剧，支持分类搜索、选集和浏览器播放。无需登录、数据库或云端服务。

发布包采用程序与个人媒体分离的结构，升级网站代码时只需整体替换 `release/seven/`，不会影响片单、配置、视频或海报。

## 发布包结构

```text
release/
├── seven/                  # 可整体替换：网站前端、启动程序和说明
│   ├── start.py
│   ├── index.html
│   ├── src/
│   └── styles/
└── movie_resources/        # 需要永久保留：个人配置、片单、视频和海报
    ├── config.json
    ├── movies.json
    ├── movies/
    ├── series/
    └── posters/
```

## 启动

```bash
python3 release/seven/start.py
```

默认地址为 `http://127.0.0.1:8000`。指定端口且不打开浏览器：

```bash
python3 release/seven/start.py --no-browser --port 8010
```

局域网共享时：

```bash
python3 release/seven/start.py --host 0.0.0.0 --no-browser
```

再从同一局域网的设备访问 `http://<本机局域网-IP>:8000`。仅建议在可信网络使用，并允许 macOS 防火墙接收 Python 入站连接。

启动器提供 HTTP Range 分段响应，视频可拖动进度条；请不要使用 `python3 -m http.server` 代替它。

## 配置和片单

编辑 `release/movie_resources/config.json`：

```json
{ "mediaDirectory": "./movie_resources" }
```

编辑 `release/movie_resources/movies.json`。其中 `poster`、`video` 和剧集 `episodes[].video` 都是相对于 `mediaDirectory` 的路径。

```json
[
  {
    "id": "movie-interstellar",
    "type": "movie",
    "title": "星际穿越",
    "year": 2014,
    "poster": "posters/movie-interstellar.jpg",
    "video": "movies/星际穿越.mp4"
  },
  {
    "id": "series-breaking-bad",
    "type": "series",
    "title": "绝命毒师",
    "poster": "posters/series-breaking-bad.jpg",
    "episodes": [
      { "season": 1, "episode": 1, "title": "第一集", "video": "series/绝命毒师/S01E01.mp4" }
    ]
  }
]
```

手动放置资源：

```text
release/movie_resources/
├── movies/电影.mp4
├── series/剧名/S01E01.mp4
└── posters/电影或剧集海报.webp
```

推荐浏览器兼容的 H.264/AAC MP4。海报可使用 `.jpg`、`.png` 或 `.webp`。

## 构建更新包

开发目录的前端或启动程序变更后运行：

```bash
python3 tools/build_release.py
```

该命令会完整重建 `release/seven/`。`release/movie_resources/` 若已存在则原样保留；对于从旧版结构迁移的发布目录，缺失的 `config.json` 与 `movies.json` 会仅首次补齐。将新生成的 `seven/` 覆盖到另一台机器的 `release/seven/` 即可完成代码更新。

## 测试

```bash
python3 -m unittest tests/test_build_release.py -v
node --test
```
