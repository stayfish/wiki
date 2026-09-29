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

1. 将合法的公开材料或来源指针加入 `raw/`，之后保持只读。
2. 创建或更新 `sources` 页面，注明材料完整度。
3. 将可复用知识拆到 `concepts`，补充交叉链接。
4. 更新 `index.md` 和 `log.md`。
5. 运行检查、测试和构建，人工预览后提交。

## Query

从 `index.md` 定位页面，必要时回到原始资料。只有长期有复用价值的答案才写入 `topics` 或 `threads`。

## Lint

检查重复概念、矛盾陈述、孤儿页、失效链接、缺少来源的强断言和过期内容。格式检查通过不代表事实正确。
