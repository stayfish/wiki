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
- `sessions/`：本地阅读讨论页；一个主题包含多轮问答，默认忽略且不发布。
- `wiki/`：Markdown 知识页，是内容的唯一真实来源。
- `render.py`：静态网站构建器。
- `render_session.py`：把 session Markdown 渲染为本地静态页面，并生成全部 session 的本地总览。
- `scripts/resolve_paper_title.py`：读取待读论文页面的标准标题元数据，并由 GitHub Action 创建 Issue。
- `assets/`：全站样式与滚动动画。
- `schema/`：阅读对话工作流、内容契约和各类页面模板。
- `reader-profile.md`：只记录决定解释深度所需的读者背景。
- `AGENTS.md`：仓库规则，以及供没有对话上下文的 Agent 使用的完整操作手册。
- `index.md`：给人和 AI 使用的知识地图。
- `log.md`：ingest、query、lint 操作记录。
- `site/`：本地生成结果，已忽略，不提交。

## 使用

如果要让一个 Agent 接手，直接让它先阅读 [`AGENTS.md`](./AGENTS.md)，再用自然语言给出材料或问题。

## 通过对话做阅读笔记

默认先做阅读价值判断，再决定写成速览或深入笔记：

```text
判断这篇论文是否值得精读，先和我讨论，不要写入 Wiki：<路径或 URL>
```

Agent 会为同一篇论文或研究线程维护一个本地 session，把每轮用户输入和 Agent 完整回答原样保存并更新为可点击的静态页面。渲染完成后，Codex 对话区只返回对应的 session 页面链接，完整回答在页面中阅读。Agent 先用 glance 判断论文是否值得精读；你确认后，Agent 先用“旧方法 → 具体失败 → 本文改动 → 预期行为 → 证据责任”做整体定向，再给出 4–6 个可调整的阅读块。面向你的地图只说明每块为何要读、读完能判断什么；章节、公式、claim 与完整图表计划由 Agent 分开维护，进入对应块时再展示。阅读仍按问题背景与相关工作、观察与核心 idea、方法、实验与论证、贡献与局限等自然顺序推进，每个一级块结束后暂停，你可以围绕当前块继续追问和纠偏，确认后再进入下一块。地图可以随讨论调整。只有你明确要求时，Agent 才从完整 session 编译 Wiki；最终 deepnote 必须包含全文阅读后校准的忠实中文摘要翻译，并使用独立卡片显示。你可以继续追问或指定重点，然后说：

```text
按“方法为什么有效”这个重点，把刚才的讨论写入 Wiki。
```

如果不需要中间确认，可以直接说：

```text
直接把这篇论文加入 Wiki；先判断深度，值得精读就生成 deepnote，否则保存 glance。
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

完整规则见 [`schema/SCHEMA.md`](./schema/SCHEMA.md)、[`schema/conversation.md`](./schema/conversation.md) 和 [`schema/writing.md`](./schema/writing.md)。

## 手机添加待读论文

公开 Wiki 首页提供 Reading List 输入框。粘贴 arXiv、DOI、OpenReview 或论文主页后，页面会复制链接并打开仓库的 **Add to Reading List** workflow：

1. 点击 **Run workflow**；
2. 将剪贴板中的 URL 粘贴到唯一输入框；
3. 再次点击 **Run workflow**。

GitHub 要求仓库写权限才能手动运行 workflow，任务本身还会检查触发者必须是仓库所有者。Action 随后读取论文页面的 `citation_title`、`og:title` 或 HTML `<title>`，避免重复，并创建 `[待读] 论文标题` Issue。首页从 GitHub 的公开 API 读取这些未关闭 Issue；关闭 Issue 即从待读列表移除。

这个流程不会把 GitHub Token 交给浏览器，也不会把待读链接提前写成 `glance`。无法读取标题时，workflow 会失败并保留错误日志，不会创建只有 URL 或错误标题的条目。

Session 页面可手动重建。指定路径用于校验目标 session，渲染器会同步刷新所有对话页与总览，避免跨 session 导航过期：

```bash
uv run python render_session.py sessions/<session-slug>/session.md
```

不带路径会校验并重建全部 session，同时生成 `sessions/index.html` 总览页：

```bash
uv run python render_session.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory .
```

随后打开 <http://127.0.0.1:8765/sessions/>。总览和对话页都只在本地生成，不会进入公开站点。

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
uv run python -m py_compile render.py render_session.py
uv run python render.py --check
```

## GitHub Pages

`.github/workflows/pages.yml` 会在 `main` 分支更新时完成校验、测试、构建和发布。首次使用时，在 GitHub 仓库设置中将 Pages Source 选择为 **GitHub Actions**。

构建器必须同时生成 `manifest.json`，列出页面标题、slug、类型、摘要、更新时间和 URL。新增页面未进入清单时不得发布。

## 安全边界

- AI 可以生成 Markdown、SVG 和动画分镜，但不能直接发布。
- 人工审核事实、引用、隐私、版权和移动端排版后才合并到 `main`。
- 不要将 `.env`、私人项目数据、API 密钥或真实用户数据放入 `raw/` 或 `wiki/`。

## 静态产品边界

公开站点保持为可直接部署到 GitHub Pages 的静态 HTML、CSS 和浏览器端 JavaScript，不依赖自建应用后端、账号系统或在线 AI 服务。Reading List 复用 GitHub Actions、Issues 和公开 API，不在站点中保存凭据。

- 搜索、阅读模式、阅读偏好和章节导航均在浏览器内完成。
- 站点不收集或保存私人阅读状态与笔记；公开待读链接由仓库所有者明确提交到 GitHub Issues。长期笔记仍由对话编译进公开 Wiki，并继续接受人工审核。
- Evidence sidecar 随静态构建发布，只链接已经记录的公开来源，不执行服务端 PDF 解析或实时证据定位。
- 站点不提供实时 AI 助手、跨论文语义问答、云端笔记或需要密钥的功能。
