# Evidence Sidecar · 结构与证据契约

`evidence/<page-slug>.json` 是 Wiki 页面的机器可读伴随文件。Markdown 继续承载公开正文；sidecar 保存稳定内容块 ID、结构化 claim、核验状态与原文锚点。它不能替代来源页中的证据边界说明。

## 顶层结构

```json
{
  "version": 1,
  "page_slug": "paper-slug",
  "source_version": "arXiv v1",
  "blocks": {
    "方法": "method-overview",
    "方法 / 训练过程": "method-training"
  },
  "claims": []
}
```

`blocks` 的键使用正文标题路径：二级标题直接使用标题，三级标题使用 `二级标题 / 三级标题`。值是持久、唯一的 kebab-case ID。正文改标题或调整层级时必须同步键，但保留 ID；新增章节生成新 ID，不按当前顺序重编号。

## Claim

```json
{
  "id": "claim-example",
  "block_id": "method-training",
  "claim_type": "author",
  "verification_status": "located",
  "summary": "可独立理解的细粒度结论",
  "anchors": [
    {
      "kind": "section",
      "label": "Section 3.2",
      "source_url": "https://example.com/paper"
    }
  ]
}
```

`claim_type` 只能是：

- `author`：作者明确陈述；
- `experiment`：原文实验数据或实验观察；
- `analysis`：基于来源的分析推断；
- `user`：用户确认的判断。

`verification_status` 只能是：

- `verified`：已核对原文位置与 claim 的支撑关系；
- `located`：已找到候选原文位置，但尚未完成支撑关系核验；
- `unverified`：尚未核对；
- `unavailable`：来源或必要证据不可用；
- `conflict`：来源与当前结论存在冲突。

`anchors` 可以描述 `section`、`page`、`text`、`equation`、`figure` 或 `table`。不能编造页码、文本范围或图表编号；无法精确定位时使用真实的较粗粒度锚点，或保持空数组。

## 私人工作区数据

阅读状态和个人笔记不写入 evidence sidecar，也不自动进入公开 Wiki。前端使用版本化存储接口，数据至少包含 `pageSlug`、`readingState`、`notes`；笔记使用稳定 `blockId` 绑定章节。当前静态部署默认使用浏览器存储并支持 JSON 导入导出，未来同步服务必须保持同一数据模型与显式隐私边界。
