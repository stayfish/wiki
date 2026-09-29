---
title: Knowledge Workflow · 让知识留下来
slug: knowledge-workflow
type: concept
summary: 原始资料负责追溯，Markdown 负责结构，AI 负责整理，静态站点负责阅读。
updated: 2026-09-28
accent: moss
---

# Knowledge Workflow · 让知识留下来

## 一句话

把一次性的阅读和问答变成可以核对来源、持续修订、互相链接的长期知识。

## 直觉

聊天记录像桌上的便签：当下有用，却很快被下一次对话盖住。这个工作流保留原始材料，把可复用结论整理为相互连接的知识页，再生成适合阅读的静态网站。

<figure>
  <figcaption><span>图 01</span><span>知识从来源流向网页</span></figcaption>
  <svg viewBox="0 0 880 280" role="img" aria-labelledby="flow-title">
    <title id="flow-title">原始资料经 AI 整理成为 Markdown 知识，再渲染为静态网页并接受人工审核</title>
    <defs><marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0 0L10 5L0 10z" fill="var(--accent)" /></marker></defs>
    <g class="reveal d1"><rect class="node" x="25" y="80" width="170" height="100" rx="8"/><text class="kicker" x="110" y="115" text-anchor="middle">SOURCE</text><text class="title" x="110" y="150" text-anchor="middle">原始资料</text><text class="note" x="110" y="172" text-anchor="middle">raw/ · 只读</text></g>
    <path class="draw d2" pathLength="1000" d="M195 130H270" marker-end="url(#arrow)"/>
    <g class="reveal d3"><rect class="node accent" x="280" y="58" width="190" height="144" rx="8"/><text class="kicker" x="375" y="98" text-anchor="middle">SYNTHESIZE</text><text class="title" x="375" y="138" text-anchor="middle">AI 整理</text><text class="note" x="375" y="166" text-anchor="middle">提取 · 连接 · 质疑</text><text class="note" x="375" y="189" text-anchor="middle">人负责审核</text></g>
    <path class="draw d4" pathLength="1000" d="M470 130H545" marker-end="url(#arrow)"/>
    <g class="reveal d5"><rect class="node" x="555" y="80" width="150" height="100" rx="8"/><text class="kicker" x="630" y="115" text-anchor="middle">KNOWLEDGE</text><text class="title" x="630" y="150" text-anchor="middle">Markdown</text><text class="note" x="630" y="172" text-anchor="middle">wiki/ · 可追踪</text></g>
    <path class="draw d6" pathLength="1000" d="M705 130H760" marker-end="url(#arrow)"/>
    <g class="reveal d7 pulse"><circle class="output" cx="810" cy="130" r="50"/><text class="output-text" x="810" y="125" text-anchor="middle">PUBLISH</text><text class="output-title" x="810" y="154" text-anchor="middle">网页</text></g>
  </svg>
</figure>

## 怎么做的

加入资料时先保存可追溯的原文或来源指针，再创建来源页。只有能够跨来源复用的内容才拆成概念页；一次问答只有具有长期价值时才写成主题或思考线索。

构建器解析 `[[slug|内部链接]]`，计算反向链接，并生成静态 HTML 与公开的 `manifest.json`。访问网站不需要数据库或运行中的 AI。

## 证据与边界

AI 能加速摘要、交叉链接和 SVG 初稿，但不能替代来源核对。自动检查能发现格式和链接问题，不能证明事实正确。
