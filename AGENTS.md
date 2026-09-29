# AGENTS.md · Wiki Agent 操作手册

## Git 规则

- 每次完成用户要求的修改后，只提交与当前任务相关的文件，并使用简洁明确的提交信息。
- 不得在未获用户明确授权时 push、merge、tag、发布或修改 remote。

本文件是本仓库的独立交接说明。即使 Agent 没有任何历史对话，只要读取本文件，就应能够安全地维护、检查和发布 Wiki。

## 1. 任务定义

这是一个由 AI 维护、由人选择来源和提出问题、由人审核发布的公开静态知识库。它遵循 Karpathy 的 LLM Wiki 模式：不在每次提问时从原始材料重新拼答案，而是在 ingest 时把知识编译进一个持久、互相链接、持续修订的 Wiki。

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

Wiki 是会复利的知识制品，不是原始材料的搜索界面：

- 人负责选择和提供来源、提出问题、判断结果是否值得保留，并审核发布。
- Agent 负责 Wiki 的组织、综合、交叉链接、更新、去重和体检。
- `raw/` 保存不可变来源；`wiki/` 保存已经综合的知识；本文件和 `SCHEMA.md` 定义维护规则。
- Query 优先读取已经编译好的 Wiki；只有校验、补证据或发现知识缺口时才回到原始来源。
- 新来源和新问题必须改善已有知识结构，而不是只增加孤立摘要。

当 Wiki 规模增长到目录无法有效导航时，可以引入全文检索工具；在真实需要出现前，不引入向量数据库、RAG 服务或复杂检索基础设施。

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
- 任何私人账号、业务系统或个人工作区中的非公开数据；
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

## 6. Ingest：把来源编译进 Wiki

当用户要求“把论文/文章/视频/仓库加入 Wiki”时：

1. 获取用户授权的来源，说明读到的是全文、摘要还是节选。
2. 先读 `index.md` 和相关 Wiki 页，建立当前知识结构，再读原始来源。不要从空白状态单独总结新材料。
3. 在 `raw/` 保存来源指针或合法的小型原始材料，并保持其不可变；修正只能通过补充说明或新版本完成。
4. 提取来源中的实体、概念、关系、主张、证据、矛盾和开放问题。
5. 创建或更新 `wiki/sources/<slug>.md`，记录来源贡献、证据边界、局限和阅读完整性。
6. 把新知识合并进已有 `concepts`、`topics` 和 `threads`；只有没有合适落点时才创建新页。
7. 新页必须与已有页面建立有意义的双向语义关系，不能只是“相关链接”堆砌；已有页面也要按新证据增量修订。
8. 如果新来源与旧页面冲突，保留冲突和各自证据，不擅自抹平差异。
9. 更新 `index.md`，使其继续充当紧凑的内容目录和 Agent 路由入口。
10. 向 `log.md` 追加 `ingest` 记录，说明新增来源和主要结构变化。
11. 执行第 10 节的完整验证，并报告新增、更新、冲突与未知项。

## 7. Query：回答并沉淀问题

Query 的默认目标是利用已经积累的 Wiki 回答问题，而不是临时对 `raw/` 做一次 RAG。具体流程：

1. 从 `index.md` 路由到少量相关 Wiki 页，沿内部链接扩展上下文。
2. 优先根据 Wiki 作答；只有需要核验关键事实、解决冲突或填补明确缺口时才读取 `raw/` 或原始链接。
3. 如果 Wiki 足以回答，直接综合已有知识，不重复 ingest 来源。
4. 在回答中区分明确证据、合理推断和未知项，并指向相关 Wiki 页或来源。
5. 如果本次推理产生了可复用的新综合、澄清了矛盾或暴露了缺口，更新相应 `concepts`、`topics` 或 `threads`，让后续查询不必重新推导。
6. 持久化修改后更新 `index.md` 和 `log.md`，执行完整验证；一次性、低复用价值的回答无需强行落盘。

## 8. Lint：知识库体检

Lint 不是格式检查的别名，而是防止长期知识漂移的主动维护操作。它可以重写和重组 Wiki，但不得修改不可变的原始来源。检查：

- 无法解析的 Wiki 链接；
- 没有入站链接且不在目录中的孤儿页；
- 相同或高度重叠的概念；
- 多页面之间的矛盾陈述；
- 缺少来源的强断言；
- 已过期的版本号、性能数据或状态描述；
- 页面类型、frontmatter、slug 和目录位置不一致；
- SVG 缺少标题、在窄屏溢出或依赖颜色表达含义。
- Wiki 页是否退化成来源摘要，缺少跨来源综合；
- `index.md` 是否仍足够紧凑，能够有效把 Agent 路由到相关页面；
- `log.md` 是否准确记录了知识库的主要变化。

Lint 发现问题时应直接修复可安全确定的结构、链接、重复和陈旧表述；无法裁决的冲突保留证据并写入开放问题。自动构建只能验证结构，不能证明内容正确，事实检查仍需回到来源。

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

每次完整构建都必须生成 `site/manifest.json`。它至少列出每页的标题、slug、类型、摘要、更新时间和 URL；新增页面未出现在 manifest 中视为构建失败。

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

## 12. 完成报告模板

向用户报告：

1. 新增或更新了哪些来源页、概念页、主题页；
2. 建立或修复了哪些知识连接；
3. 哪些结论仍受材料完整度限制；
4. 运行了哪些检查及结果；
5. 是否已经提交、推送和发布；
6. 如已发布，提供可访问的页面链接。
