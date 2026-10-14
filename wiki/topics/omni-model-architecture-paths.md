---
title: 全模态模型的统一路线与阅读地图
slug: omni-model-architecture-paths
type: topic
summary: 比较共享 embedding、统一离散 token、专用编码器、Thinker–Talker，以及与架构正交的数据和评测闭环。
updated: 2026-10-14
accent: ochre
---

# 全模态模型的统一路线与阅读地图

## 当前结论

“全模态”没有唯一架构定义。当前重要路线分别统一语义空间、离散 token、Transformer 主干、交互协议或 Agent 接口；能理解所有模态不等于能原生生成所有模态，也不自动等于具备全双工或 Agent 能力。[[minicpm-o-4-5]] 表明，流式输入、流式输出和低 RTF 之外还需要持续话轮控制与播放同步；[[omnivchat]] 则表明，输入接口原生也不足以证明模型真正使用了音频和视频。架构、交互协议、训练数据、执行反馈和评测闭环是相互正交的能力轴。

## 问题范围

本页组织全模态架构及其训练评测边界的阅读地图。[[qwen2-5-omni]]、[[qwen3-8-omni]]、[[minicpm-o-4-5]] 与 [[omnivchat]] 已完成全文阅读；其他列出的论文目前只核对了公开摘要、贡献说明或相关章节，因此对应内容仍是阅读假设与比较框架。

## 主要路线

### 共享 embedding 空间

ImageBind 将图像、文本、音频、深度、热成像和 IMU 对齐到共享 embedding 空间，并以图像作为跨模态枢纽。它擅长对齐和检索，但不是完整的自回归对话与生成模型。

### 所有模态离散 token 化

Unified-IO 2、AnyGPT 与 Chameleon 代表不同程度的统一离散序列路线：图像、音频、文字、动作或坐标先被 tokenizer/codebook 转成离散 token，再由一个自回归模型理解和生成。这种路线输入输出形式统一，但不同模态的码率、序列长度和训练稳定性是核心难题。

### 专用编码器接入语言骨干

Qwen-Omni 使用 Vision Encoder 和音频编码器产生连续 embedding，经 adapter 投影进语言骨干。[[qwen2-5-omni]] 建立 Thinker–Talker，以 TMRoPE 对齐音视频并原生输出文字和语音；[[qwen3-8-omni]] 再加入 Spatial AuT。优点是可以继承强语言模型并为每种模态使用合适前端；缺点是输入输出不对称，图像和视频通常需要外部生成器。

### 长上下文全模态理解

Gemini 1.5 代表将音视频直接扩展到百万 token 上下文的路线。Qwen3.8 一方面采用 1M context、GDN 与 QSA，另一方面增加外层 Agent 按需取证；“全部装入”和“主动选择加载”应作为互补策略比较。

### Thinker–Talker 实时交互

[[qwen2-5-omni|Qwen2.5-Omni]] 建立 Thinker–Talker：Thinker统一理解并产生文本与隐藏状态，Talker根据这些状态和采样文字生成语音 codec token；[[rotary-position-embedding|TMRoPE]] 为音频和视频提供共同时间坐标。Qwen3.5-Omni进一步处理长音视频、时间对齐和流式语音稳定性；Qwen3.8 在此基础上增加空间音频、长上下文和 Agent 系统。

### 持续交互协议

[[minicpm-o-4-5]] 把视觉环境、音频环境和助手输出按共享时间窗序列化，并让模型用 Listen/Speak token 决定每窗是否开口。TAIL 再用发音时间戳构造变长文本块，使自回归 boundary 控制每个语音时间格承诺多少文字。它统一的是持续交互协议，而非新的模态 embedding 或 tokenization。

这一层与 Thinker–Talker 正交：一个模型可以流式接收音视频、流式产生语音，却仍然只在用户 turn 结束后回答。全双工还要求新输入在输出期间进入控制闭环，运行时能取消过期内容，并让真实播放进度长期贴近环境墙钟。[[full-duplex-timing-attribution]] 记录当前无法从通用 benchmark、RTF 或语音可懂度中单独归因的部分。

### 与架构正交的数据与评测闭环

[[omnivchat]] 不提出新的 Omni 编码架构，而是在 Qwen3-Omni Thinker 上建立合成、证据回标、tiered rubric、LLM judge 和 GSPO 闭环。它揭示了另一条能力轴：模型可以拥有原生音视频输入，却仍可能主要依赖 ASR 内容、视觉捷径、类别模板或评分器偏好。判断架构是否带来真实联合感知，需要 audio-only、video-only、ASR-text、模态错配与独立 judge 对照，详见 [[omnivchat-grounding-attribution]]。

## 比较与权衡

| 路线 | 统一对象 | 主要优势 | 主要限制 |
| --- | --- | --- | --- |
| ImageBind | 语义 embedding | 跨模态对齐与检索 | 不直接解决长序列生成 |
| Unified-IO 2 / AnyGPT | 离散 token | 任意模态输入输出形式统一 | 序列长、码率差异和训练稳定性 |
| Chameleon | 图文早期融合 token | 图文交错理解与生成 | 模态覆盖不等于完整 Omni |
| Gemini 1.5 | 长上下文中的多模态信息 | 可处理超长音视频 | 装得下不等于推理或检索可靠 |
| Qwen-Omni | 专用 Encoder + 共享 Thinker | 易继承语言推理和实时语音 | 视觉输出依赖外部工具 |
| MiniCPM-o 4.5 | 共享时间窗中的感知、控制与输出 | 持续视觉/音频输入、主动输出、端侧实时运行 | 一秒离散粒度；同步和打断证据不足 |
| Omni Agent 栈 | 模型、工具与 Harness | 能主动取证并改变环境 | 贡献归因、成本和可靠性更复杂 |
| OmniVChat 数据与 RL | 渲染事实、rubric 与回复策略 | 可规模化开放式音视频对话训练和评测 | 训练—评测耦合，grounding 归因不足 |

## 冲突与不确定性

- “token”有时指离散词表 ID，有时泛指一个连续序列位置，阅读时必须区分。
- Any-to-any 原生生成形式更统一，但不保证每种模态的质量优于专业生成器。
- 专用编码器路线虽然输出不对称，却可能更适合强理解模型和模块化产品系统。
- 长上下文 benchmark 不能替代真实长视频中的证据定位、时序推理和成本评测。
- 开放式 rubric 能容许多种正确措辞，但 criterion 遗漏、tier gate 和训练 judge 复用会把标注误差放大为系统性评分偏差。
- 冻结音视频 tower 后的回复策略增益不能自动归因于更强感知；需要比较训练前后的模态干预敏感性。
- RTF 小于 1 只说明计算吞吐能跟上现实时间，不能证明助手输出使用的是最新环境状态。
- 离线时间戳和自回归边界可以学习平均调度；若模型看不到真实播放器队列，网络或设备抖动后的闭环恢复仍未知。

## 我的判断

当前阅读判断是：全模态架构至少应沿五条轴比较，即模态如何表示、物理时间如何编码、语义与语音生成怎样分工、输入输出是否处于同一持续控制闭环，以及模型外 Harness 如何加载证据和执行动作。理解 Qwen3.8 仍需用 Unified-IO 2 或 AnyGPT 对照“所有模态离散 token 化”，并用 SWE-agent/OpenHands 理解 [[omni-agent-stack|工具和 Harness]]；理解实时交互则需用 [[minicpm-o-4-5]] 和 Moshi 区分流式生成与全双工控制。

## 下一步阅读

建议顺序：

1. ImageBind：共享多模态空间；
2. Unified-IO 2：统一理解与生成；
3. Chameleon 或 AnyGPT：统一离散序列的不同实现；
4. Gemini 1.5：百万 token 多模态上下文；
5. [[qwen2-5-omni|Qwen2.5-Omni]]：已完成；Thinker–Talker、TMRoPE 与实时语音；
6. [[minicpm-o-4-5]]：已完成；共享时间轴、Listen/Speak 与 TAIL；
7. Moshi：用并行语音流对照显式时间窗协议；
8. Qwen3.5-Omni：长音视频、时间对齐和 ARIA；
9. [[omnivchat]]：已完成；数据合成、分层 rubric、开放式评测与 GSPO 回复策略；
10. 回看 [[qwen3-8-omni]]，区分继承与新增部分。

Agent/Harness 支线依次阅读 ReAct、Toolformer、Reflexion、CodeAct、SWE-agent 和 OpenHands。

## 来源与连接

- [[qwen3-8-omni]]：当前已完成全文阅读的核心来源。
- [[qwen2-5-omni]]：Thinker–Talker、TMRoPE 与流式语音的前代架构来源。
- [[minicpm-o-4-5]]：将持续感知、显式话轮控制和时间对齐语音交错加入同一序列协议。
- [[full-duplex-timing-attribution]]：追踪模型内部时间轴与真实播放器状态之间的归因缺口。
- [[omnivchat]]：把原生音视频输入连接到数据合成、开放式评分与回复策略优化。
- [[omnivchat-grounding-attribution]]：记录架构能力与 rubric/judge 适配之间尚未解决的归因问题。
- [[rotary-position-embedding]]：解释多模态时间和空间坐标如何进入 Attention。
- [[omni-agent-stack]]：把模态统一问题连接到 Agent 运行时。
- ImageBind：https://arxiv.org/abs/2305.05665
- Unified-IO 2：https://arxiv.org/abs/2312.17172
- AnyGPT：https://arxiv.org/abs/2402.12226
- Chameleon：https://arxiv.org/abs/2405.09818
- Gemini 1.5：https://arxiv.org/abs/2403.05530
- Qwen2.5-Omni：https://arxiv.org/abs/2503.20215
- Qwen3.5-Omni：https://arxiv.org/abs/2604.15804
