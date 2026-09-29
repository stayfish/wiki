# AGENTS.md · Wiki Agent 操作手册

## Git 规则

- 每次完成用户要求的修改后，只提交与当前任务相关的文件，并使用简洁明确的提交信息。
- 不得在未获用户明确授权时 push、merge、tag、发布或修改 remote。

本文件是本仓库的独立交接说明。即使 Agent 没有任何历史对话，只要读取本文件，就应能够安全地维护、检查和发布 Wiki。

## 1. 任务定义

这是一个由 AI 协助维护、由人审核的公开静态知识库：

```text
公开来源或来源指针
        ↓
      raw/
        ↓ AI 阅读、提炼、建立联系
      wiki/
        ↓ render.py
      site/
        ↓ GitHub Actions
https://stayfish.github.io/wiki/
```

仓库：<https://github.com/stayfish/wiki>

AI 的职责不是简单摘要，而是将新材料合并进已有知识结构，同时保留来源、证据边界和可复查性。

## 2. 开始任何任务前

按顺序执行：

1. 阅读本文件。
2. 阅读 `SCHEMA.md`，确认页面格式和动画规范。
3. 阅读 `index.md`，了解已有页面，避免重复概念。
4. 阅读 `log.md` 最近几条记录，了解近期演化。
5. 执行 `git status --short`，保留所有与当前任务无关的用户改动。

如果指令之间有冲突，优先级为：用户当前明确要求、本文件、`SCHEMA.md`。

## 3. 仓库结构

```text
wiki/
├── AGENTS.md                 # 仓库级规则与完整 Agent 操作手册
├── SCHEMA.md                 # 页面结构和内容规范
├── README_ZH.md              # 面向人的项目说明
├── index.md                  # 知识地图
├── log.md                    # ingest/query/lint 时间线
├── render.py                 # 标准库静态构建器
├── assets/
│   ├── style.css             # 杂志式公共样式
│   └── wiki.js               # 进入视口后播放 SVG 动画
├── raw/                      # 原始材料或来源指针
├── wiki/
│   ├── sources/              # 一份来源一页
│   ├── concepts/             # 跨来源概念
│   ├── topics/               # 多来源综合主题
│   └── threads/              # 开放问题和思考线索
├── site/                     # 生成结果，Git 忽略
└── .github/workflows/pages.yml
```

只有出现真实内容时才创建 `sources`、`topics` 或 `threads` 等目录，不创建空骨架。

## 4. 安全与内容边界

Wiki 是公开网站。不得写入或提交：

- 密码、令牌、Cookie、`.env` 内容或生产配置；
- Homepage 的用户、Idea、Project、Todo 或其他私人数据；
- 未公开的个人资料、公司材料或聊天记录；
- 无权再发布的论文全文、图片、数据集或代码；
- 大型模型、数据集、数据库转储或构建产物。

对于网页、论文和 GitHub 仓库，优先在 `raw/` 保存小型来源指针，而不是复制整个材料：

```markdown
# 来源标题

- URL: https://example.com/source
- Accessed: 2026-09-28
- Type: paper
- Scope: full text / abstract / excerpt
- Notes: 使用公开版本
```

`raw/` 中已保存的来源视为只读。需要修正描述时新建说明，不静默改写原始材料。

## 5. 页面规则

每页以 frontmatter 开始：

```yaml
---
title: KV Cache · Transformer 的短期记忆
slug: kv-cache
type: concept
summary: 缓存历史 token 的注意力键值，避免生成时重复计算。
updated: 2026-09-28
accent: moss
---
```

约束：

- `slug` 使用唯一的英文 kebab-case。
- `type` 只能是 `source`、`concept`、`topic`、`thread`。
- `accent` 只能是 `brick`、`ochre`、`moss`、`deep`。
- `summary` 是一句可独立显示的摘要。
- `updated` 使用实际修改日期 `YYYY-MM-DD`，不要机械修改未发生内容变化的页面。
- 内部链接使用 `[[slug]]` 或 `[[slug|显示文字]]`。
- 新增链接前先确认目标页面存在；不要故意留下死链。

概念页默认结构：

```markdown
# 标题

## 一句话
## 直觉
## 怎么做的
## 证据与边界
## 链接
```

内容要求：

- 先讲直觉和为什么需要它，再讲机制。
- 明确区分来源事实、AI 推断和未知信息。
- 不编造作者观点、数据、引用、页码、代码位置或实验结果。
- 重要断言尽量指回来源页或公开链接。
- 一个概念只维护一个主页面；发现同义页时优先合并，而不是继续复制。

## 6. Ingest：加入新来源

当用户要求“把论文/文章/视频/仓库加入 Wiki”时：

1. 获取并阅读用户授权的来源；说明读到的是全文、摘要还是节选。
2. 搜索 `index.md` 和 `wiki/`，识别已有来源、同义概念和可复用页面。
3. 在 `raw/` 保存来源指针或合法的小型原始材料。
4. 创建 `wiki/sources/<slug>.md`，记录问题、方法、结论、证据、局限和阅读完整性。
5. 只把跨来源有复用价值的知识拆到 `wiki/concepts/`。
6. 更新已有概念，而不是为同一概念创建近似页面。
7. 在来源页、概念页之间增加有意义的 `[[wikilink]]`。
8. 更新 `index.md`；按类型添加一句导航说明。
9. 向 `log.md` 顶部或日期顺序合适的位置追加 `ingest` 记录。
10. 执行第 10 节中的完整验证。
11. 向用户说明新增、更新了哪些页面，以及仍未确认的内容。

## 7. Query：回答并沉淀问题

当用户针对已有知识提问时：

1. 先从 `index.md` 定位相关页面。
2. 阅读对应 `sources` 和 `concepts`；高风险结论回到 `raw/` 或原始链接。
3. 在回答中区分明确证据、合理推断和未知项。
4. 只有答案具有长期复用价值时，才创建或更新 `topics`、`threads` 或概念页。
5. 发生持久化修改时更新 `index.md`、`log.md` 并执行完整验证。
6. 普通一次性问答无需为了留下痕迹而强行新增页面。

## 8. Lint：知识库体检

检查：

- 无法解析的 Wiki 链接；
- 没有入站链接且不在目录中的孤儿页；
- 相同或高度重叠的概念；
- 多页面之间的矛盾陈述；
- 缺少来源的强断言；
- 已过期的版本号、性能数据或状态描述；
- 页面类型、frontmatter、slug 和目录位置不一致；
- SVG 缺少标题、在窄屏溢出或依赖颜色表达含义。

自动构建只能验证结构，不能证明内容正确。事实检查需要回到来源。

## 9. 动画图示

图示使用内联 SVG，禁止为了普通流程图新增大型前端框架。最小格式：

```html
<figure>
  <figcaption><span>图 01</span><span>KV Cache 数据流</span></figcaption>
  <svg viewBox="0 0 880 300" role="img" aria-labelledby="kv-title">
    <title id="kv-title">KV Cache 数据流说明</title>
    <g class="reveal d1">...</g>
    <path class="draw d2" pathLength="1000" d="..." />
    <g class="reveal d3 pulse">...</g>
  </svg>
</figure>
```

可用动画：

- `reveal d1` 至 `d8`：按顺序淡入；
- `draw d1` 至 `d8`：绘制路径；
- `grow-x`：横向展开；
- `pulse`：出现后强调一次。

每幅图必须：

- 有 `viewBox`、`role="img"`、`aria-labelledby` 和 `<title>`；
- 在不开启动画时仍然表达完整含义；
- 避免文字溢出、元素遮挡和仅靠颜色区分；
- 在桌面和窄屏预览后再发布。

## 10. 构建与验证

首选命令：

```bash
uv sync
uv run python -m py_compile render.py
uv run python render.py --check
uv run python render.py
```

如果当前环境没有 `uv`，且项目仍无第三方依赖，可以使用：

```bash
python3 -m py_compile render.py
python3 render.py --check
python3 render.py
```

生成结果在 `site/`，不要提交。可以本地预览：

```bash
python3 -m http.server 8000 -d site
```

至少确认：

- 命令以退出码 0 完成；
- `site/index.html` 存在；
- 新页面对应 HTML 存在；
- `site/manifest.json` 能解析并包含新页面；
- 页面内部链接的相对路径正确；
- 动画页面加载 `wiki.js`；
- `git diff --check` 通过。

## 11. Git 与发布

修改完成后遵守本文件的 Git 规则：提交且只提交当前任务相关文件。建议提交信息：

```text
docs: ingest <source>
docs: add <concept> explanation
docs: update <topic>
fix: repair wiki links
```

提交前：

```bash
git status --short
git diff --check
git diff --cached --stat
```

不要擅自修改 remote、push、merge、tag 或发布。只有用户明确要求推送或发布时，才执行：

```bash
git push origin main
```

推送后查看 GitHub Actions 的 `Publish Wiki` 工作流，确认 build 与 deploy 都成功，再访问：

- 网站：<https://stayfish.github.io/wiki/>
- Manifest：<https://stayfish.github.io/wiki/manifest.json>

## 12. 与 Homepage 的未来连接

当前两个项目完全独立。允许的最小连接是 Homepage 只读公开的 `manifest.json`，其中提供页面标题、slug、类型、摘要、更新时间和相对 URL。

不要：

- 让 Wiki 直接访问 Homepage 数据库；
- 将 Homepage 私人内容自动公开；
- 给 AI 任意数据库或 GitHub 写权限；
- 在没有人工审核的情况下从 Homepage 自动发布。

如果未来需要从 Homepage 导出内容，应采用“用户明确选择 → 生成 Markdown 草稿 → 人工检查 → 提交/PR → 发布”的流程。

## 13. 完成报告模板

向用户报告：

1. 新增或更新了哪些来源页、概念页、主题页；
2. 建立或修复了哪些知识连接；
3. 哪些结论仍受材料完整度限制；
4. 运行了哪些检查及结果；
5. 是否已经提交、推送和发布；
6. 如已发布，提供可访问的页面链接。
