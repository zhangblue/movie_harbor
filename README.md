# 电影港湾

电影港湾是个人本地媒体库网站：展示收藏的电影与美剧，支持分类搜索、选集和浏览器播放。无需登录、数据库或云端服务。

项目包含可复制的 `release/` 运行包。它使用 Python 标准库扫描本地视频、更新片单，并通过 HTTP Range 分段响应支持大 MP4 拖动进度条。

## 快速启动

推荐运行发布包：

```bash
python3 release/start.py
```

它会扫描媒体库、更新 `release/data/movies.json`，并在 `http://127.0.0.1:8000` 启动网站。

```bash
# 跳过扫描、不自动打开浏览器、使用 8010 端口
python3 release/start.py --no-scan --no-browser --port 8010
```

不要使用 `python3 -m http.server` 播放视频；它不提供本项目所需的 Range 分段处理。

## 工程结构

```text
config.json                 # 开发目录媒体配置
data/movies.json            # 开发片单
movie_resources/            # 本地视频与海报（默认不提交 Git）
index.html / src/ / styles/ # 前端网站
release/                    # 可直接复制和运行的发布包
  start.py                  # 扫描并启动本地 Range 服务
  scan_library.py           # 增量扫描器
  config.json
  data/movies.json
  movie_resources/
tools/build_release.py      # 生成/刷新 release 的构建脚本
```

## 构建与发布

修改前端、扫描器或配置后，运行：

```bash
python3 tools/build_release.py
```

该命令刷新 `release/` 的运行时文件。复制整个 `release/` 目录到另一台电脑后，进入该目录执行：

```bash
python3 start.py
```

请一并保留或填充 `release/movie_resources/`，其中是实际本地媒体文件。

## 配置媒体目录

编辑 `release/config.json`：

```json
{ "mediaDirectory": "./movie_resources" }
```

路径必须相对于 `release/`，不能填写 `/Users/...`、`C:\...` 等绝对路径。

## 添加电影、美剧和海报

按目录约定放置资源：

```text
release/movie_resources/
├── movies/
│   └── 星际穿越.mp4
├── series/
│   └── 绝命毒师/
│       ├── S01E01.mp4
│       └── S01E02.mp4
└── posters/
    ├── movie-星际穿越.jpg
    └── series-绝命毒师.jpg
```

视频支持 `.mp4`、`.webm`、`.mov`；海报支持 `.jpg`、`.png`、`.webp`。文件名 `S01E02` 自动识别为第 1 季第 2 集；未匹配的剧集文件会按文件名字典序归入第 1 季。

更新片单：

```bash
python3 release/scan_library.py
```

扫描器会新增影片、更新视频路径，保留人工填写的标题、简介、年份、类型和海报。已删除的视频会标为 `null`，影片资料不会被删除。若发现同名媒体、重复季集或 `S00E01` 这类无效编号，会停止并报告冲突，防止丢失数据。

## 片单格式

`release/data/movies.json` 可手动维护；`video`、`poster` 均相对于 `mediaDirectory`。

```json
{
  "id": "movie-interstellar",
  "type": "movie",
  "title": "星际穿越",
  "year": 2014,
  "poster": "posters/movie-interstellar.jpg",
  "video": "movies/星际穿越.mp4"
}
```

```json
{
  "id": "series-breaking-bad",
  "type": "series",
  "title": "绝命毒师",
  "poster": "posters/series-breaking-bad.jpg",
  "episodes": [
    { "season": 1, "episode": 1, "title": "第一集", "video": "series/绝命毒师/S01E01.mp4" }
  ]
}
```

海报或视频尚未准备好时可设为 `null`；网站保留条目并在打开时说明视频不可用。

## 播放排查

拖动进度条时服务会返回 `206 Partial Content`。浏览器取消旧分段请求属于正常行为，服务端会安全忽略。

无法播放时依次检查：

1. 使用 `python3 release/start.py` 启动。
2. 片单视频路径与 `release/movie_resources/` 的文件名完全一致。
3. 终端没有 404 或扫描错误。
4. 视频使用浏览器兼容编码；推荐 H.264 视频 + AAC 音频的 MP4。

## 测试

```bash
python3 -m unittest tests/test_scan_library.py tests/test_build_release.py -v
node --test
```
