# Wiki Log

## [2026-10-10] lint | 引入本地 session 与摘要翻译卡片

- 将阅读对话保存为本地主题 session：一个 session 包含多轮 turn，每轮回答继续按论文问题树分层，并生成 Codex 可链接的静态页面。
- Session 默认被 Git 忽略且不发布；只有用户明确要求写入时，才从完整讨论综合 glance、deepnote、concept、topic 与 thread。
- deepnote 新增全文阅读后完成的忠实摘要翻译，并使用独立的 Abstract Translation 卡片与分析正文分开。

## [2026-10-10] lint | 将 deepnote 改为分块精读与交互式页面

- 在深度判断后新增“分层阅读地图”阶段：先恢复问题背景、相关工作与挑战、观察与猜想、方法、实验论证、贡献和局限，再递归拆分复杂块。
- 将精读讨论改为按块推进，默认在每个一级块后暂停；用户追问、纠偏和判断绑定回对应块。
- 同步生成关键图表计划：截取许可允许再发布的方法图与结果，版权不明时改用带来源的重绘或 Markdown 表格重建。
- 要求最终 deepnote 沿用讨论形成的 `## / ###` 层级，固定模板降为覆盖检查表。
- 构建器根据内容层级生成语义卡片、嵌套阅读地图、阅读进度、折叠/展开、聚焦阅读和块链接复制；无 JavaScript 时保留完整正文。

## [2026-10-04] ingest | OmniVChat: Synthesizing, Benchmarking, and Training for Native Audio-Visual Dialogue

- 新增 arXiv v2 来源指针与 48 页全文 deepnote，重建 OmniVChat 的任务定义、Single-turn / Multi-turn 数据生成、证据回标、tiered rubric 和 OmniVChat-RL 逐步训练机制。
- 将 rubric score、组内回复效率、style reward、GSPO 序列级概率比和 LoRA 配置连接到主结果与奖励消融；保留完整奖励牺牲部分 correctness 以换取简洁度的权衡。
- 新增跨模态 Grounding 归因线索，记录缺少单模态、ASR-text、模态错配、独立 judge 与人类盲评对照的问题；同步扩展全模态架构阅读地图的数据与评测轴。
- 核对官方发布：合成 benchmark、媒体、scorer 与 reward 已公开；Studio、360 条人工录制集和论文多轮协议的前序 reference replies 尚未完整公开。
- 未复制本地 PDF 或论文图像，未记录私人附件路径；后续研究检索截止 2026-10-04。

## [2026-10-04] lint | 强化方法总结的原文忠实度

- 要求 glance 与 deepnote 先恢复论文的 problem setting / formulation、输入输出、符号、假设和原始流程，再增加直觉解释。
- 将 deepnote 方法部分拆为 formulation、论文原始方法流程和解释性例子三层，明确区分训练与推理，禁止用常见实现补全论文未披露的步骤。
- 将这一偏好同步到总规范、对话流程、论文规则与读者背景；本次未改写现有来源笔记。

## [2026-10-03] lint | 引入 glance / deepnote 阅读深度

- 将单一 `source` 页面类型拆成 `glance` 与 `deepnote`，新增价值判断、速览和十三项精读模板，并同步对话路由、构建器与使用说明。
- 新增精简读者背景：保留理解 LLM 论文所需的数学、LLM、扩散语言模型与 sparse attention 基础，删除无助于控制解释深度的个人信息。
- 将现有两篇 Qwen 来源页迁移为 deepnote，并基于此前全文阅读补齐思路重建、pipeline、数学、实验问答、最小复现、反例、后续研究与 follow-up idea。
- 扩展静态构建器以识别新类型，并正确渲染有序列表、代码块、粗体和 Markdown 数学公式；来源页面的公开 URL 继续保留在 `sources/` 下。
- 保留证据边界：作者 claim、相关研究、分析推断与未知猜测分开；后续研究检索截止 2026-10-03。

## [2026-10-02] lint | 按新概念模板重构 RoPE

- 将 RoPE 页的机制说明统一收进“原理”，保留旋转矩阵、相对位置恒等式、多频率实现及 M-RoPE/TMRoPE 推导。
- 将术语辨析、实验依据和多模态位置设计争议改为“原理”的三级小节，使页面符合修订后的概念页结构。
- 未改变来源范围与核心判断；继续区分论文实验结果、数学分析和未经验证的设计猜想。

## [2026-10-02] ingest | Qwen2.5-Omni Technical Report 与 RoPE

- 新增 Qwen2.5-Omni 来源指针和全文阅读笔记；实际依据为官方 arXiv v1 HTML 全文，本地 PDF 未复制或公开路径。
- 围绕 Thinker–Talker、音视频输入、TMRoPE、两秒交错、流式语音、训练信号和证据边界整理对话结论。
- 新增 RoPE 概念页，从二维旋转、相对位置恒等式、多频率实现讲到 M-RoPE/TMRoPE，并吸收 Qwen2-VL 相关章节与苏剑林文章对兼容性、等价性、对称性的分析。
- 更新全模态架构阅读地图与 Qwen3.8-Omni 前代连接；保留 TMRoPE 消融不足、训练数据细节有限和多模态位置设计取舍等开放问题。

## [2026-09-29] ingest | Qwen3.8-Omni: Towards Native Omni-Modal Agents

- 新增论文来源指针和全文阅读笔记；实际阅读范围为官方 arXiv v1 HTML 全文，本地附件未复制或公开路径。
- 围绕 AuT、Spatial AuT、时间表示、Thinker–Talker、GDN/QSA、四阶段预训练、多教师蒸馏和统一 RL 汇总对话结论。
- 新增“全模态 Agent 栈”概念，明确模型、工具、Harness 与执行环境的边界，并区分 QSA 内部检索和 Agent 外部取证。
- 新增全模态架构阅读地图；除 Qwen3.8 外，其余论文目前只核对公开摘要与贡献说明，保留为下一步阅读而非已完成结论。
- 新增能力归因开放线索，记录缺少的消融、成本和跨 Harness 对照实验。
