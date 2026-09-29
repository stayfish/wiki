# 通用来源页模板

来源页保存到 `wiki/sources/<slug>.md`，`type` 使用 `source`。适用于文章、网页、视频、播客、书章和代码仓库；论文在此基础上遵循 [`paper.md`](./paper.md)。

## 建议额外元数据

```yaml
source_kind: article
source_url: https://example.com/source
source_version: 访问或发布版本
read_scope: full-text
status: reviewed
```

## 默认结构

```markdown
# 来源标题

## 为什么读
## 一句话结论
## 核心内容
## 关键证据或示例
## 局限与质疑
## 与 Wiki 的连接
## 阅读后的问题
## 来源
```

按媒介调整“证据”：视频注明时间点，书章注明章节，代码仓库注明 commit 或 release，网页注明访问日期。无法取得全文时必须在 `read_scope` 和正文中说明，不得把二手摘要伪装成完整阅读。
