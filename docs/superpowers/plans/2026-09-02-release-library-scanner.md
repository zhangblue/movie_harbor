# 本地媒体库发布与扫描器实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 生成可独立运行的 `release/` 目录，其中的无依赖 Python 程序能增量扫描本地电影/美剧资源、维护片单并启动网站。

**架构：** `release/scan_library.py` 是唯一的片单写入者：读取相对配置、扫描约定目录、合并已存在的人工元数据并原子写回 JSON。`release/start.py` 调用扫描器后以标准库 HTTP 服务器公开 `release/`；发布脚本只复制明确列出的站点与运行时文件，不复制开发文档、测试或 Git 数据。

**技术栈：** Python 3 标准库（`argparse`、`json`、`pathlib`、`http.server`、`unittest`）、HTML/CSS/ES modules。

---

## 文件结构

- 创建：`tools/build_release.py` — 可重复构建 `release/`，复制网页、配置、片单、Python 程序与媒体目录。
- 创建：`release/scan_library.py` — 纯标准库增量扫描器及 CLI。
- 创建：`release/start.py` — 先扫描、后启动 HTTP 服务的 CLI。
- 创建：`release/config.json`、`release/data/movies.json`、`release/index.html`、`release/src/`、`release/styles/` — 构建产物。
- 创建：`tests/test_scan_library.py` — 使用临时目录验证扫描、人工元数据保留、删除媒体和海报选择。
- 创建：`tests/test_build_release.py` — 验证构建目录内容与媒体目录复制。
- 修改：`README.md` — 增加发布构建、扫描器和启动命令。

### 任务 1：可测试的增量媒体扫描器

**文件：**
- 创建：`release/scan_library.py`
- 创建：`tests/test_scan_library.py`

- [ ] **步骤 1：编写失败的扫描测试**

```python
from pathlib import Path
from scan_library import scan_catalog

def test_scan_catalog_adds_movie_and_series_without_overwriting_manual_fields(tmp_path: Path):
    media = tmp_path / 'movie_resources'
    (media / 'movies').mkdir(parents=True)
    (media / 'series' / '示例剧').mkdir(parents=True)
    (media / 'movies' / '新电影.mp4').touch()
    (media / 'series' / '示例剧' / 'S01E02.mp4').touch()
    catalog = [{"id": "new-movie", "type": "movie", "title": "人工片名", "description": "保留", "video": None}]
    updated = scan_catalog(media, catalog)
    movie = next(item for item in updated if item['id'] == 'new-movie')
    assert movie['title'] == '人工片名'
    assert movie['description'] == '保留'
    assert movie['video'] == 'movies/新电影.mp4'
    assert next(item for item in updated if item['type'] == 'series')['episodes'][0]['season'] == 1
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python3 -m unittest tests/test_scan_library.py -v`

预期：FAIL，提示找不到 `scan_library`。

- [ ] **步骤 3：实现扫描器和 CLI**

实现以下接口：

```python
VIDEO_EXTENSIONS = {'.mp4', '.webm', '.mov'}

def make_id(value: str) -> str: ...
def parse_episode(filename: str) -> tuple[int, int] | None: ...
def scan_catalog(media_root: Path, catalog: list[dict]) -> list[dict]: ...
def main() -> None: ...
```

`scan_catalog` 只扫描 `movies/` 和 `series/<name>/`；按稳定 ID 合并；电影与剧集若扫描后不存在相应文件，将 `video` 写为 `None`，但保留条目。扫描器读取 `posters/<id>.jpg`、`.png`、`.webp` 并只为新条目或原 `poster` 为空的条目补充海报。`main()` 接收 `--root`（默认 `release/`），读取根目录 `config.json`、更新 `data/movies.json`，用同目录临时文件加 `Path.replace()` 原子替换。

- [ ] **步骤 4：运行单元测试确认通过**

运行：`python3 -m unittest tests/test_scan_library.py -v`

预期：PASS；覆盖新电影、美剧 S01E02、人工字段保留、缺失视频置空、海报优先级与未带 SxxExx 文件的第 1 季顺序分配。

- [ ] **步骤 5：Commit**

```bash
git add release/scan_library.py tests/test_scan_library.py
git commit -m "feat: add incremental media library scanner"
```

### 任务 2：发布构建器与本地启动器

**文件：**
- 创建：`tools/build_release.py`
- 创建：`release/start.py`
- 创建：`tests/test_build_release.py`
- 修改：`README.md`

- [ ] **步骤 1：编写失败的发布构建与启动参数测试**

```python
from pathlib import Path
from build_release import build_release

def test_build_release_copies_runtime_files_and_media(tmp_path: Path):
    source = tmp_path / 'source'
    destination = tmp_path / 'release'
    # 创建最小 index.html、config.json、data/movies.json、src、styles、release Python 文件和 movie_resources。
    build_release(source, destination)
    assert (destination / 'start.py').is_file()
    assert (destination / 'scan_library.py').is_file()
    assert (destination / 'config.json').is_file()
    assert (destination / 'movie_resources').is_dir()
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python3 -m unittest tests/test_build_release.py -v`

预期：FAIL，提示找不到 `build_release`。

- [ ] **步骤 3：实现确定性构建和启动器**

`tools/build_release.py` 导出：

```python
def build_release(source_root: Path, destination: Path) -> None:
    # 删除 destination 内先前由构建器生成的明确文件/目录，
    # 再复制 index.html、config.json、data/、src/、styles/、release/start.py、
    # release/scan_library.py、movie_resources/ 和 README.md。
```

只删除传入的明确 `destination`，调用方默认 `source_root / 'release'`；不接受根目录、空路径或解析后等于 `source_root` 的目的目录，遇到这些值抛出 `ValueError`。脚本入口支持 `--output`。

`release/start.py` 的 CLI：

```python
parser.add_argument('--no-scan', action='store_true')
parser.add_argument('--port', type=int, default=8000)
parser.add_argument('--no-browser', action='store_true')
```

未传 `--no-scan` 时先调用 `scan_library.main` 的可复用扫描函数；随后以 `ThreadingHTTPServer` 在 `127.0.0.1` 服务发布目录。`--no-browser` 不调用 `webbrowser.open`，便于自动化验证。

- [ ] **步骤 4：运行测试及发布冒烟验证**

运行：`python3 -m unittest tests/test_scan_library.py tests/test_build_release.py -v`

预期：PASS。

运行：`python3 tools/build_release.py && python3 release/start.py --no-scan --no-browser --port 8010`

预期：构建生成 `release/` 的完整运行时文件；服务器打印 `http://127.0.0.1:8010`。用 `curl -I http://127.0.0.1:8010/` 验证 HTTP 200 后停止服务器。

- [ ] **步骤 5：补充使用说明并提交**

在 `README.md` 增加：构建命令、`release/` 可复制性、`python3 release/scan_library.py`、`python3 release/start.py`、`--no-scan` 和端口参数；说明增量合并规则与媒体消失处理。

```bash
git add tools/build_release.py release/start.py release/scan_library.py tests/test_build_release.py README.md release/
git commit -m "feat: package releasable local media library"
```

## 计划自检

- 规格覆盖：任务 1 实现目录扫描、ID 合并、海报、人工数据保留和媒体缺失处理；任务 2 构建独立目录、启动程序和发布验证。
- 完整性：每项实现都有具体文件、函数、命令和预期结果。
- 类型一致性：所有路径均使用 `Path`，目录参数统一命名为 `media_root` 或 `source_root`，片单字段统一为 `video`、`episodes`、`poster`。
