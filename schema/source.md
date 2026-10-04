# 阅读笔记共享契约

来源页保存到 `wiki/sources/<slug>.md`。完成来源核验和阅读价值判断后，使用 `type: glance` 或 `type: deepnote`；不得继续创建 `type: source`。论文同时遵循 [`paper.md`](./paper.md)，并按深度使用 [`glance.md`](./glance.md) 或 [`deepnote.md`](./deepnote.md)。

## 建议额外元数据

```yaml
source_kind: article
source_url: https://example.com/source
source_version: 访问或发布版本
read_scope: full-text
status: reviewed
```

`read_scope` 必须准确描述 `full-text`、`abstract`、`excerpt`、页码范围或代码版本。无法取得全文时可以产出 `glance`，但不能把摘要或二手材料写成 `deepnote`。

## 两种深度

- `glance`：已经完成六项判断，足以决定是否继续读。它是有证据边界的阅读卡，不是只改写摘要。
- `deepnote`：完整重建问题、方法、推导、实验和批评，并包含可执行的复现与 follow-up 分析。

同一来源只能有一个主页面。以后决定深入时，保留 slug 和历史连接，原地将 `glance` 升级为 `deepnote`。降级通常没有必要；若证据后来被撤回，应保留修订说明。

按媒介调整“证据”：视频注明时间点，书章注明章节，代码仓库注明 commit 或 release，网页注明访问日期。无法取得全文时必须在 `read_scope` 和正文中说明，不得把二手摘要伪装成完整阅读。
