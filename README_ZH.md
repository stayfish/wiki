# AI Knowledge Wiki

一个通过人与 Agent 对话积累阅读笔记、由人审核并发布到 GitHub Pages 的静态知识库。

```text
阅读材料 -> 与 Agent 讨论 -> raw/ + wiki/ -> 人工审核 -> GitHub Pages
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
- `schema/`：阅读对话工作流、内容契约和各类页面模板。
- `AGENTS.md`：仓库规则，以及供没有对话上下文的 Agent 使用的完整操作手册。
- `index.md`：给人和 AI 使用的知识地图。
- `log.md`：ingest、query、lint 操作记录。
- `site/`：本地生成结果，已忽略，不提交。

## 使用

如果要让一个 Agent 接手，直接让它先阅读 [`AGENTS.md`](./AGENTS.md)，再用自然语言给出材料或问题。

## 通过对话做阅读笔记

默认采用“先读和讨论，再确认写入”的方式：

```text
阅读这篇论文，先和我讨论，不要写入 Wiki：<路径或 URL>
```

Agent 会说明实际阅读范围，给出核心问题、3–5 个要点、证据、局限以及与现有笔记的关系。你可以继续追问或指定重点，然后说：

```text
按“方法为什么有效”这个重点，把刚才的讨论写入 Wiki。
```

如果不需要中间确认，可以直接说：

```text
直接把这篇文章加入 Wiki，完整阅读，提炼可复用概念，并保留反例和局限。
```

查询默认只回答、不修改文件：

```text
根据现有 Wiki 回答这个问题，先不要修改文件：<问题>
```

值得长期保留时再说：

```text
把刚才的答案沉淀到 Wiki，优先更新已有页面。
```

还可以要求 Agent 做阅读回顾：

```text
回顾最近五次阅读：哪些结论变强了，哪些仍有冲突，下一步该读什么？
```

完整规则见 [`schema/SCHEMA.md`](./schema/SCHEMA.md) 和 [`schema/conversation.md`](./schema/conversation.md)。

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

构建器必须同时生成 `manifest.json`，列出页面标题、slug、类型、摘要、更新时间和 URL。新增页面未进入清单时不得发布。

## 安全边界

- AI 可以生成 Markdown、SVG 和动画分镜，但不能直接发布。
- 人工审核事实、引用、隐私、版权和移动端排版后才合并到 `main`。
- 不要将 `.env`、私人项目数据、API 密钥或真实用户数据放入 `raw/` 或 `wiki/`。
