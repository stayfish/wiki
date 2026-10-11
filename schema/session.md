# Session · 本地对话工作区

Session 用于保存阅读过程，不属于公开 Wiki。一个 session 对应一篇论文或一条连续研究线程；同一主题的追问、纠偏和分块精读作为多个 turn 追加到同一目录。

## 目录与生命周期

```text
sessions/<session-slug>/
├── session.md    # 完整讨论的规范来源
└── index.html    # 每轮回答后重建的本地静态页面
sessions/index.html  # 自动生成的本地总览，不提交
```

- 不创建 `state.md` 或另一份滚动摘要。层次结构直接存在于每轮回答中。
- 新论文、明显不同的研究问题或用户明确要求“新建 session”时创建新目录；普通追问继续当前 session。
- `sessions/*/` 默认被 Git 忽略，避免公开聊天内容、本地来源线索或尚未审核的推断。
- 每轮先把用户输入原文和 Agent 完整回答原文追加到 `session.md`，再运行 `render_session.py`。
- 渲染单个 session 时同步刷新 `sessions/index.html`；不带路径运行渲染器时，校验并重建全部 session 和总览页。
- 渲染成功后，Codex 对话区的最终回复只包含 `index.html` 的本地链接；完整回答只在 session 页面展示，避免两处重复。

## Frontmatter

```yaml
---
title: Session 标题
slug: unique-kebab-case
created: 2026-10-10
updated: 2026-10-10
status: active
source: 公开论文 URL 或 none
---
```

`status` 使用 `active`、`ready-to-compile` 或 `closed`。它只表示讨论阶段，不代表 Wiki 已审核。

## Turn 结构

```markdown
## Turn 01 · 本轮主题

### 用户

用户本轮输入原文。

### Codex

Agent 本轮完整回答原文。回答可以根据论文的问题树使用小标题，但 session 层不再为它强制添加“当前结论”、“分层分析”或“本轮留下的问题”等包装。
```

Turn 按时间追加。不静默改写、润色、压缩或删除已保存的用户输入与 Agent 回答；后续纠偏写进新 turn，并链接或点名被修正的旧判断。用户输入中的 Markdown、代码块和列表保持原样；若它们影响 session 页面结构，应修复渲染器或容器语义，不应改写原文。

## 编译进 Wiki

只有用户明确要求“写入 Wiki”“沉淀”或“入库”时才执行：

1. 完整读取 session，而不是只看最后一轮。
2. 回到原始来源核验将进入 Wiki 的关键事实与数字。
3. 按阅读价值选择 `glance` 或 `deepnote`；把可复用机制、跨来源综合和开放问题分别路由到 `concept`、`topic`、`thread`。
4. 编译 deepnote 时，保留讨论中形成的一级块与子块结构，并必须加入全文阅读后校准的 `## 摘要翻译`。
5. 保留用户纠偏和真实分歧，删除对话中的重复、操作说明与已经被推翻的临时猜测。
6. Session 保留为本地过程记录，不把整段聊天复制到公开页面。
