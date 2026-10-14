# Wiki Index

## Deepnotes · 深入阅读

- [[qwen2-5-omni]] — 从 Thinker–Talker、TMRoPE 与流式处理理解 Qwen 全模态路线的基础架构。
- [[qwen3-8-omni]] — 从语音与空间音频编码、长上下文训练到全模态 Agent 系统的完整阅读笔记。
- [[minicpm-o-4-5]] — 解释模型怎样一边听一边说，以及 TAIL 如何用 `boundary token` 决定每个 `chunk` 生成多少文字。
- [[omnivchat]] — 从合成数据、证据回标、分层 Rubric 与 GSPO 理解原生音视频对话的训练评测闭环。

## Glances · 简单总结

当前没有只保留为 glance 的来源。

## Concepts · 概念

- [[omni-agent-stack]] — 区分策略模型、工具接口、Harness 与执行环境，解释完整 Agent 能力来自哪里。
- [[rotary-position-embedding]] — 从旋转矩阵与注意力点积解释 RoPE、M-RoPE 和 TMRoPE。

## Topics · 综合

- [[omni-model-architecture-paths]] — 比较共享 embedding、统一离散 token、专用编码器、Thinker–Talker 与持续交互协议。

## Threads · 线索

- [[native-omni-agent-attribution]] — 追踪如何分离模型、训练、插件与 Harness 对最终能力的贡献。
- [[omnivchat-grounding-attribution]] — 追踪合成数据、跨模态 Grounding、回复策略与 LLM Judge 对 OmniVChat 增益的贡献。
- [[full-duplex-timing-attribution]] — 追踪边界策略、离线时间戳、播放器反馈与运行时取消对全双工稳定性的贡献。
