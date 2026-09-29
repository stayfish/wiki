# AI Knowledge Wiki

一个由 AI 协助维护、由人审核、发布到 GitHub Pages 的静态知识库。

```text
原始资料 -> raw/ -> AI 整理 -> wiki/ -> 构建器 -> GitHub Pages
```

## 环境

需要 Python 3.13 和 [uv](https://docs.astral.sh/uv/)：

```bash
uv sync
```

项目当前只使用 Python 标准库，没有运行时依赖。

## 目录

- `raw/`：公开原始资料或来源指针；大型、私密或无权公开的材料不要提交。
- `wiki/`：Markdown 知识页，是内容的唯一真实来源。
- `render.py`：静态网站构建器。
- `assets/`：全站样式与滚动动画。
- `SCHEMA.md`：AI 必须遵循的内容结构与工作流。
- `index.md`：给人和 AI 使用的知识地图。
- `log.md`：ingest、query、lint 操作记录。
- `site/`：本地生成结果，已忽略，不提交。

## 使用

检查内容：

```bash
uv run python render.py --check
```

生成网站：

```bash
uv run python render.py
```

本地预览：

```bash
uv run python -m http.server 8000 -d site
```

打开 <http://localhost:8000>。

执行生成结果检查：

```bash
uv run python -m py_compile render.py
uv run python render.py --check
```

## GitHub Pages

`.github/workflows/pages.yml` 会在 `main` 分支更新时完成校验、测试、构建和发布。首次使用时，在 GitHub 仓库设置中将 Pages Source 选择为 **GitHub Actions**。

构建器同时生成 `manifest.json`。未来 Homepage 可以只读这个公开清单，获取页面标题、摘要、类型、更新时间和 URL，而无需共享数据库或仓库权限。

## 安全边界

- AI 可以生成 Markdown、SVG 和动画分镜，但不能直接发布。
- 人工审核事实、引用、隐私、版权和移动端排版后才合并到 `main`。
- Wiki 不连接 Homepage 数据库，也不持有 Homepage 的访问凭据。
- 不要将 `.env`、私人项目数据、API 密钥或真实用户数据放入 `raw/` 或 `wiki/`。
