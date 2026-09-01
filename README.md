# 电影港湾

这是一个通过浏览器浏览、搜索和播放本地电影与美剧文件的静态媒体库。请使用静态文件服务器运行它，不能直接双击打开 `index.html`。

## 运行

在项目根目录执行：

```bash
python3 -m http.server 8000
```

然后在浏览器中打开 `http://localhost:8000`。

## 配置媒体目录

`config.json` 中的 `mediaDirectory` 必须是相对于项目根目录、且由这个静态服务器公开的目录，例如：

```json
{ "mediaDirectory": "./movie_resources" }
```

浏览器不能安全地扫描任意绝对本机路径，因此不要填入 `/Users/...`、`C:\\...` 等绝对目录。将媒体文件放入项目中的 `movie_resources/`（或另一个相对目录）后，再在片单中引用它们。

## 添加电影与海报

1. 将电影视频放到媒体目录中的任意子目录，例如 `movie_resources/movies/my-film.mp4`。
2. 将海报放到媒体目录中，例如 `movie_resources/posters/my-film.jpg`。
3. 在 `data/movies.json` 中添加电影条目。`video` 和 `poster` 都是相对于 `mediaDirectory` 的路径：

```json
{
  "id": "my-film",
  "type": "movie",
  "title": "我的电影",
  "year": 2026,
  "poster": "posters/my-film.jpg",
  "video": "movies/my-film.mp4"
}
```

没有海报时可将 `poster` 设为 `null`，页面会显示片名占位封面。

## 添加美剧与剧集

一部美剧只需要一张海报。建议把视频按剧集放在独立目录中，例如：

```text
movie_resources/
  posters/my-series.jpg
  series/my-series/s01e01.mp4
  series/my-series/s01e02.mp4
```

在 `data/movies.json` 中使用 `episodes` 数组定义剧集；每个对象的 `season`、`episode` 为数字，`video` 为相对于 `mediaDirectory` 的视频路径：

```json
{
  "id": "my-series",
  "type": "series",
  "title": "我的美剧",
  "poster": "posters/my-series.jpg",
  "episodes": [
    { "season": 1, "episode": 1, "title": "第一集", "video": "series/my-series/s01e01.mp4" },
    { "season": 1, "episode": 2, "title": "第二集", "video": "series/my-series/s01e02.mp4" }
  ]
}
```

尚未添加剧集时可使用空数组：`"episodes": []`。

## 默认演示美剧

默认片单还带有“美剧演示：第一季”，用于检查“美剧”分类、详情页和选集流程。该示例**没有随站点附带视频文件**；打开第一集会显示“没有可用的视频文件。”提示。添加自己的美剧时，请按上方格式将该集的 `video` 替换为实际剧集视频路径。

## 无法播放时

先确认视频文件确实位于 `mediaDirectory` 下，且片单路径大小写和文件名完全一致。若页面提示浏览器不支持该格式，通常是视频编码不受当前浏览器支持；可尝试使用 H.264 视频与 AAC 音频编码的 MP4 文件，或改用支持该媒体编码的浏览器。也可在浏览器开发者工具的网络面板中确认视频请求没有返回 404。
