# 手动媒体管理实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 superpowers:subagent-driven-development（推荐）或 superpowers:executing-plans 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 移除自动扫描与片单写入，使发布包只通过手动放置媒体和编辑 JSON 管理影片。

**架构：** `release/start.py` 保留本地 HTTP Range 服务，但不再导入或调用扫描器；构建器复制手动维护的媒体目录、配置和片单。网站不变，仍从 `data/movies.json` 的手动路径读取资源。

**技术栈：** Python 3 标准库、Node 内置测试。

---

## 文件结构

- 删除：`release/scan_library.py` — 不再支持自动扫描。
- 删除：`tests/test_scan_library.py` — 删除扫描器专属测试。
- 修改：`release/start.py` — 移除扫描导入和 `--no-scan` 参数。
- 修改：`tools/build_release.py` — 不再复制扫描器。
- 修改：`tests/test_build_release.py` — 删除扫描假设，断言启动器不改写片单。
- 修改：`README.md`、`release/README.md` — 改为手动添加资源说明。

### 任务 1：移除扫描器并保留 Range 启动服务

**文件：**
- 删除：`release/scan_library.py`
- 删除：`tests/test_scan_library.py`
- 修改：`release/start.py`
- 修改：`tools/build_release.py`
- 修改：`tests/test_build_release.py`
- 修改：`README.md`
- 修改：`release/README.md`

- [ ] **步骤 1：编写失败的手动启动测试**

在 `tests/test_build_release.py` 增加：

```python
def test_start_arguments_do_not_offer_a_scan_switch(self):
    arguments = parse_args(["--no-browser", "--port", "8765"])
    self.assertFalse(hasattr(arguments, "no_scan"))

def test_build_release_does_not_ship_a_scanner(self):
    build_release(source, destination)
    self.assertFalse((destination / "scan_library.py").exists())
```

- [ ] **步骤 2：运行测试确认失败**

运行：`python3 -m unittest tests/test_build_release.py -v`

预期：FAIL，因为当前 CLI 有 `no_scan` 属性且构建器复制扫描器。

- [ ] **步骤 3：实现最小删除与文档调整**

从 `release/start.py` 删除 `import scan_library`、`--no-scan` 参数和调用扫描器的分支；保留 `--port`、`--no-browser`、`RangeRequestHandler`、`create_server` 与 `main` 的安全关闭逻辑。

从 `tools/build_release.py` 的构建输入列表删除 `release/scan_library.py`；删除扫描器与扫描测试文件。更新两份 README，使唯一的资源流程为“复制视频和海报 → 手动编辑 `data/movies.json` → 运行 `start.py`”。

- [ ] **步骤 4：运行全量验证**

运行：`python3 -m unittest tests/test_build_release.py -v && node --test && git diff --check`

预期：PASS；Range 的 200、206、416 测试仍通过；构建产物没有 `scan_library.py`，启动器不会修改片单。

- [ ] **步骤 5：Commit**

```bash
git add -u release tests README.md release/README.md tools/build_release.py
git commit -m "feat: switch to manual media management"
```

## 计划自检

- 规格覆盖：任务 1 删除自动扫描、保留 Range 服务、更新构建和手动配置文档。
- 完整性：每一步均指明文件、代码行为和验证命令。
- 类型一致性：所有用户维护数据仍使用 `data/movies.json`、`poster`、`video` 与 `episodes` 字段。
