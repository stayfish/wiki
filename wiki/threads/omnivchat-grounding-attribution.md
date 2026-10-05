---
title: 如何分离 OmniVChat 的跨模态 Grounding 与评分器适配
slug: omnivchat-grounding-attribution
type: thread
summary: 追踪合成数据、感知使用、回复策略、rubric 和 LLM judge 各自对 OmniVChat 增益的贡献。
updated: 2026-10-04
accent: deep
---

# 如何分离 OmniVChat 的跨模态 Grounding 与评分器适配

## 为什么重要

[[omnivchat]] 在合成 benchmark 和人工录制单轮集上都报告显著增益，但训练 correctness reward 与最终评测使用同一 tiered rubric 和 qwen3.7-max judge。视觉与音频 tower 在 RL 中冻结，许多子类别又包含稳定的对话策略。若不做模态干预，最终分数无法说明模型是否更依赖正确的音视频证据。

## 当前理解

最稳妥的结论是：OmniVChat-RL 让 Thinker 更会生成满足实例 criterion、简洁且符合指定口语风格的文字回复。360 条中文人工录制对话说明这种策略能跨过一部分生成域差异。现有证据尚不能把增益分配给跨模态 grounding、类别级回复模板、system prompt 适配或 judge 偏好。

这个问题与 [[native-omni-agent-attribution]] 结构相似：前者分解数据与评分闭环，后者分解模型、工具与 Harness。两者都要求在控制其他系统变量后才归因给模型权重。

## 支持证据

- 合成 Mean 从 0.465 提至 0.652，人工录制 Human 从 0.402 提至 0.632，说明同一评分协议下存在稳定行为改变。
- 合成中文子集与人工集的长期学习曲线共同上升，支持相同子类别上的粗粒度迁移。
- 去掉 efficiency 后正确性进一步提高，说明完整 reward 的一部分作用是改变回复长度，而非单调增强任务能力。
- 六个 judge 对固定 Gemini 回复的子类别画像相关较高，说明 rubric 难度结构不是 qwen3.7-max 独有。

## 反例或冲突

- Judge 在训练和评测中只看候选回复与 criterion，不看原始音视频；模型可能学习 judge-compatible phrasing。
- 视觉与音频编码 tower 冻结，RL 的直接作用点主要是 Thinker 的 Attention、MoE projection 与输出策略。
- 多 judge 实验没有重新评测训练前后差值，无法证明 0.465→0.652 对 judge 选择稳健。
- Human probe 与合成数据共享子类别、rubric form 和 grader，只改变媒体来源；它不是独立的人类回复质量评估。
- Benchmark 没有系统提供 audio-only、video-only、ASR-text、模态错配和时间打乱对照。

## 缺少什么

需要同一批样本上的因果干预矩阵：

| 对照 | 要回答的问题 |
| --- | --- |
| 完整音视频 | 原始任务表现 |
| 静音 | 增益是否依赖语音、说话人或声学情绪 |
| 单帧或遮挡视频 | 增益是否依赖视觉对象、手势或摄像头方向 |
| ASR 文本 + 静态图 | 原生输入是否优于级联信息 |
| 音频错配或时间平移 | 模型是否使用正确的跨模态绑定 |
| 独立 judge | 增益是否依赖训练 judge |
| 人类盲评 | rubric gain 是否对应真实回复质量 |
| 训练前后证据敏感性 | RL 是否改变媒体干预造成的性能差，而非只改变输出风格 |

还应按子类别标注“音频充分、视频充分、必须联合、主要是部署策略”四种证据需求，避免把模型身份等任务混入跨模态感知结论。

## 下一步

1. 用公开 OmniVChat-Bench 建立四到五种输入干预，不修改 rubric 与系统提示；
2. 对 base、完整 OmniVChat-RL、无 efficiency 和无 style 四个 checkpoint 运行同一矩阵；
3. 用至少一个独立 judge 重评所有训练前后差值，而非只比较固定模型回复；
4. 在小规模真实手机录制集上做人工 pairwise 评价，并记录判断者分歧；
5. 若公开 Human probe 或 Studio 源码，检查人工集与合成集在场景、语言、语速和证据依赖上的分布差异。

## 何时算回答

当公开或可复现实验能在相同模型、系统提示和推理预算下，分别量化完整输入、单模态、级联文本、模态错配和独立 judge 的训练前后差值，并由人类盲评确认主要趋势时，可以将本线索闭合为一篇 Omni 对话评测主题页。

## 来源与连接

- [[omnivchat]]：提出 Studio、Bench 和 RL，并提供当前增益与消融证据。
- [[qwen2-5-omni]]：提供可用于时间错配和单模态干预的基础 Omni 架构。
- [[qwen3-8-omni]]：展示更长音视频和 Agent 设置下相似的能力归因问题。
- [[native-omni-agent-attribution]]：提供模型、训练、工具和运行时的平行归因框架。
