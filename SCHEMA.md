# Wiki 内容规范

维护前先阅读本文件、`index.md` 和 `log.md` 最近记录。

## 页面类型

- `wiki/sources/`：一份论文、文章、视频或代码仓库对应一页。
- `wiki/concepts/`：跨来源复用的概念。
- `wiki/topics/`：综合多个来源的横向主题。
- `wiki/threads/`：尚未闭合的问题和个人思考线索。

只在出现真实内容时创建目录。

## Frontmatter

```yaml
---
title: 页面标题
slug: kebab-case-slug
type: concept
summary: 一句话摘要
updated: 2026-09-28
accent: moss
---
```

- `type`：`source`、`concept`、`topic`、`thread`。
- `accent`：`brick`、`ochre`、`moss`、`deep`。
- 内部链接：`[[slug]]` 或 `[[slug|显示文字]]`。

## 建议结构

```markdown
# 标题
## 一句话
## 直觉
## 怎么做的
## 证据与边界
## 链接
```

来源明确陈述、AI 推断和未知信息必须分开表达。

## 动画图示

使用内联 SVG，并包含 `viewBox`、`role="img"` 和 `<title>`：

```html
<figure>
  <figcaption><span>图 01</span><span>数据流</span></figcaption>
  <svg viewBox="0 0 880 300" role="img" aria-labelledby="figure-title">
    <title id="figure-title">图示说明</title>
    <g class="reveal d1">...</g>
    <path class="draw d2" pathLength="1000" d="..." />
    <g class="reveal d3 pulse">...</g>
  </svg>
</figure>
```

动画类包括 `reveal`、`draw`、`grow-x`、`pulse`，用 `d1` 至 `d8` 控制顺序。关闭动画后仍须能理解图意。

## Ingest

1. 先读 `index.md` 和相关 Wiki 页，再读新来源，避免从空白状态生成孤立摘要。
2. 将合法的公开材料或来源指针加入 `raw/`，之后保持只读。
3. 创建或更新 `sources` 页面，注明材料完整度、证据和局限。
4. 将新知识合并进已有 `concepts`、`topics` 和 `threads`；只有没有合适落点时才创建新页。
5. 补充有意义的交叉链接，明确保留无法裁决的来源冲突。
6. 更新作为内容目录的 `index.md` 和作为时间线的 `log.md`。
7. 运行检查和构建，确认 `manifest.json` 包含新增页面，人工预览后提交。

## Query

从 `index.md` 定位少量相关 Wiki 页并优先基于 Wiki 回答；只有核验、解决冲突或填补知识缺口时才回到原始资料。查询产生的可复用综合应回写 Wiki，低复用的一次性回答无需落盘。

## Lint

主动检查并修复重复概念、矛盾陈述、孤儿页、失效链接、缺少来源的强断言、过期内容和退化成单篇摘要的页面。必要时重组 Wiki，使 `index.md` 保持紧凑可导航；不得修改 `raw/`。格式检查通过不代表事实正确。
