---
title: 全模态模型的统一路线与阅读地图
slug: omni-model-architecture-paths
type: topic
summary: 比较共享 embedding、统一离散 token、专用编码器与 Thinker–Talker 等全模态架构路线。
updated: 2026-09-29
accent: ochre
---

# 全模态模型的统一路线与阅读地图

## 当前结论

“全模态”没有唯一架构定义。当前重要路线分别统一语义空间、离散 token、Transformer 主干或交互接口；能理解所有模态不等于能原生生成所有模态，也不自动等于具备 Agent 能力。

## 问题范围

本页组织本轮讨论中形成的阅读地图。除 [[qwen3-8-omni]] 外，下列论文目前只核对了公开摘要和贡献说明，尚未完成全文阅读，因此这里记录的是阅读假设与比较框架，不是最终结论。

## 主要路线

### 共享 embedding 空间

ImageBind 将图像、文本、音频、深度、热成像和 IMU 对齐到共享 embedding 空间，并以图像作为跨模态枢纽。它擅长对齐和检索，但不是完整的自回归对话与生成模型。

### 所有模态离散 token 化

Unified-IO 2、AnyGPT 与 Chameleon 代表不同程度的统一离散序列路线：图像、音频、文字、动作或坐标先被 tokenizer/codebook 转成离散 token，再由一个自回归模型理解和生成。这种路线输入输出形式统一，但不同模态的码率、序列长度和训练稳定性是核心难题。

### 专用编码器接入语言骨干

Qwen-Omni 使用 Vision Encoder、AuT 和 Spatial AuT 产生连续 embedding，经 adapter 投影进语言骨干。优点是可以继承强语言模型并为每种模态使用合适前端；缺点是输入输出不对称，图像和视频通常需要外部生成器。

### 长上下文全模态理解

Gemini 1.5 代表将音视频直接扩展到百万 token 上下文的路线。Qwen3.8 一方面采用 1M context、GDN 与 QSA，另一方面增加外层 Agent 按需取证；“全部装入”和“主动选择加载”应作为互补策略比较。

### Thinker–Talker 实时交互

Qwen2.5-Omni 建立 Thinker–Talker：Thinker统一理解并产生文本与隐藏状态，Talker根据这些状态生成语音 codec token。Qwen3.5-Omni进一步处理长音视频、时间对齐和流式语音稳定性；Qwen3.8 在此基础上增加空间音频、长上下文和 Agent 系统。

## 比较与权衡

| 路线 | 统一对象 | 主要优势 | 主要限制 |
| --- | --- | --- | --- |
| ImageBind | 语义 embedding | 跨模态对齐与检索 | 不直接解决长序列生成 |
| Unified-IO 2 / AnyGPT | 离散 token | 任意模态输入输出形式统一 | 序列长、码率差异和训练稳定性 |
| Chameleon | 图文早期融合 token | 图文交错理解与生成 | 模态覆盖不等于完整 Omni |
| Gemini 1.5 | 长上下文中的多模态信息 | 可处理超长音视频 | 装得下不等于推理或检索可靠 |
| Qwen-Omni | 专用 Encoder + 共享 Thinker | 易继承语言推理和实时语音 | 视觉输出依赖外部工具 |
| Omni Agent 栈 | 模型、工具与 Harness | 能主动取证并改变环境 | 贡献归因、成本和可靠性更复杂 |

## 冲突与不确定性

- “token”有时指离散词表 ID，有时泛指一个连续序列位置，阅读时必须区分。
- Any-to-any 原生生成形式更统一，但不保证每种模态的质量优于专业生成器。
- 专用编码器路线虽然输出不对称，却可能更适合强理解模型和模块化产品系统。
- 长上下文 benchmark 不能替代真实长视频中的证据定位、时序推理和成本评测。

## 我的判断

本轮对话形成的阅读判断是：理解 Qwen3.8 不应只沿 Qwen 家族纵向阅读，还要用 Unified-IO 2 或 AnyGPT 作为“所有模态离散 token 化”的对照，并用 SWE-agent/OpenHands 理解为什么全模态模型仍需要 [[omni-agent-stack|工具和 Harness]]。

## 下一步阅读

建议顺序：

1. ImageBind：共享多模态空间；
2. Unified-IO 2：统一理解与生成；
3. Chameleon 或 AnyGPT：统一离散序列的不同实现；
4. Gemini 1.5：百万 token 多模态上下文；
5. Qwen2.5-Omni：Thinker–Talker 与实时语音；
6. Qwen3.5-Omni：长音视频、时间对齐和 ARIA；
7. 回看 [[qwen3-8-omni]]，区分继承与新增部分。

Agent/Harness 支线依次阅读 ReAct、Toolformer、Reflexion、CodeAct、SWE-agent 和 OpenHands。

## 来源与连接

- [[qwen3-8-omni]]：当前已完成全文阅读的核心来源。
- [[omni-agent-stack]]：把模态统一问题连接到 Agent 运行时。
- ImageBind：https://arxiv.org/abs/2305.05665
- Unified-IO 2：https://arxiv.org/abs/2312.17172
- AnyGPT：https://arxiv.org/abs/2402.12226
- Chameleon：https://arxiv.org/abs/2405.09818
- Gemini 1.5：https://arxiv.org/abs/2403.05530
- Qwen2.5-Omni：https://arxiv.org/abs/2503.20215
- Qwen3.5-Omni：https://arxiv.org/abs/2604.15804
