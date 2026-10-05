---
title: OmniVChat：从合成音视频对话到分层 Rubric 与策略优化
slug: omnivchat
type: deepnote
summary: 重建原生音视频对话的数据合成、证据回标、分层评测与 OmniVChat-RL，并审视合成到真实迁移的归因边界。
updated: 2026-10-04
accent: moss
source_kind: paper
source_url: https://arxiv.org/abs/2609.21465
source_version: arXiv v2
read_scope: full-text
status: reviewed
---

# OmniVChat：从合成音视频对话到分层 Rubric 与策略优化

## 为什么读

[[qwen2-5-omni]] 与 [[qwen3-8-omni]] 解释全模态模型怎样接入音频、视频和语音输出，OmniVChat 补上另一半问题：如何获得“用户直接对着摄像头说话”的训练数据，如何给开放式回复评分，以及如何把评分转成后训练信号。它值得保留为 deepnote，因为论文把数据生成、标注、评测和 RL 串成一个可复用闭环，也暴露了新的归因问题：模型分数提高究竟来自跨模态 grounding，还是来自对 rubric、judge 和回复风格的适配。

## 摘要（忠实转述）

论文将 OmniVChat 定义为用户与全模态模型之间的原生音视频对话：模型同时接收用户的音频和视频并返回文字，问题直接存在于音视频中，不另给文字问题，也不依赖外部 caption 或 ASR。作者认为该任务受限于真实设备录制数据稀缺，以及开放式回复难以用关键词评测。为此，论文提出多 Agent 数据引擎 OmniVChat-Studio，合成单轮与多轮音视频对话；用合成数据建立覆盖五类基本对话能力的 OmniVChat-Bench；再用同时优化正确性、效率与风格的 OmniVChat-RL 微调 Qwen3-Omni-Instruct。作者报告，合成数据训练同时提高合成 benchmark 和人工录制的 OmniVChat-Bench-Human 分数。

## 贡献

**论文声称。** 第一，OmniVChat-Studio 将任务配置、脚本、音视频渲染、媒体观察、定向问答、修复、reference reply 和 rubric 生成拆成可重用模块。第二，OmniVChat-Bench 用 2,800 个合成对话和分层 criterion 评测 17 个子类别。第三，OmniVChat-RL 将同一 rubric score 与格式、回复效率和口语风格组合成 GSPO 奖励。第四，360 条中文人工录制单轮对话显示合成训练可以迁移到同一任务定义下的真实拍摄条件。

**分析判断。** 最可迁移的贡献是“渲染结果才是事实源”：脚本只表达生成意图，reference reply 与 rubric 必须根据实际音视频重新建立。RL 结果有价值，但训练和评测共享 rubric 与 qwen3.7-max judge，使其独立性弱于数据工程贡献。

## 研究问题与价值

OmniVChat 的输入是用户音频和视频，输出是文字回复。问题没有独立文本版本，因此模型必须从语音恢复请求，并在需要时结合手势、物体、摄像头方向、说话人、情绪和历史 turn。这个 setting 比一般音视频问答多出三项要求：问题本身是感知对象；输出是允许多种自然表述的开放回复；正确行为可能是等待、澄清或拒绝错误前提，而非总要给出事实答案。

若这一任务可训练和评测，原生 Omni 助手可以少依赖 ASR 级联，并保留语调、环境声和同步视觉证据。论文没有测量端到端延迟或计算成本，因此“减少延迟和外部计算”仍是架构动机，不是本文直接验证的结果。本文也只返回文字，不覆盖流式语音输出、实时打断和全双工交互。

## 已有解法与缺口

ASR 级联先把语音压成文字，再交给视觉语言模型。它实现简单，但可能丢失韵律、情绪、重叠说话和非语音声音，并引入转写误差。已有音视频 benchmark 常把媒体和文字问题分开，测到的是素材理解，不完全对应用户面对摄像头自然发问。人工录制更真实，却难以大规模覆盖摄像头切换、错误前提、多人换班和多轮回忆等罕见状态。

直接从脚本生成视频也不能得到可靠标签。视频生成器可能改变对象颜色、左右位置、人物数量和实际说出的内容。若 reference answer 继续依据原脚本，标签会与模型真正看到的媒体冲突。OmniVChat-Studio 的核心缺口判断是：监督必须从渲染结果重新建立，不能把生成提示当成 ground truth。

## 作者思路重建

以下为基于论文发表前技术条件的分析性重建，不代表作者自述。

1. 真实原生音视频对话昂贵且长尾明显，但带同步音频的视频生成器已经能覆盖一部分日常短场景，因此可以把生成用于理解数据，而不只用于内容创作。
2. 生成器不会严格执行脚本，需要把“观察媒体”和“判断是否合格”分开：Reviewer 描述实际音视频，Director 决定接受、定向提问或修复，Validator 负责机械规则。
3. 开放式回复没有唯一字符串，但可以拆成有先决关系的原子 criterion。语言与核心事实放在低 tier，细节和自然表达放在高 tier，既容许改写，又保留任务优先级。
4. 同一 rubric score 可以直接成为 RL correctness reward；在同一输入的多个候选回复中再比较单位长度得分与口语风格，就能训练“答对、简洁、适合说出口”的策略。
5. 最后用相同子类别的人工录制对话检查迁移。如果合成集和真实集随训练共同提高，至少说明策略没有只记住具体合成视频；但这还不能分离感知、回复策略与 judge 适配。

## 核心直觉

论文的核心是“先生成一个世界，再从这个世界重新标注”。计划事实描述系统想生成什么，观察事实描述视频实际出现什么，监督事实只保留模型能听到或看到的证据。reference reply 和 rubric 依据观察事实生成，使随机渲染误差不会静默变成错误标签。

OmniVChat-RL 则把同一输入下的回复变成组内竞争：内容更完整、单位长度获得更多 rubric credit、口语风格更合规的回复得到更高 advantage。它主要优化已有 Omni 感知表示之上的文字回复策略，并未重新训练音视频编码 tower。

## 方法：问题设定与原始流程

### 任务定义与数据对象

单轮实例包含一段带同步音频的视频、一个 reference reply 和一组 tiered rubric。被测模型只接收音视频并输出文字。多轮实例包含连续用户视频和对应的历史助手回复；所有模型接收相同历史，只生成并评分最后一轮回复。论文将能力分为五类、17 个子类别：对话状态与连接感知、跨模态实体对齐、模型自我认知、抗幻觉和情绪识别。

OmniVChat-Studio 使用四种角色。Director 处理文本规划、语义审核、答案与 rubric；Renderer 生成同步音视频；Reviewer 观察媒体并产出 caption、质量报告或定向问答；Validator 执行格式、时间线、说话速度和配置约束等确定性检查。固定模块跨子类别复用，能力特有行为通过配置与可变 prompt 注入。

### Single-turn：从配置到最终标注

1. **Attribute & Corpus Sampling。** 系统按子类别配置采样语言、场景领域、摄像头、人物数量、音视频干扰和问题变体，并从文本语料抽取主题素材。采样任务在修复期间保持不变，避免困难配置被替换成容易配置。
2. **Description、Plan & Review、Script Generation。** Director 先生成故事轮廓，再细化人物、摄像头、关键对象和用户请求，最后写成带时间轴的结构化脚本。Validator 检查机械规则，Director 再判断报告是否为上下文允许的例外；Script Review 检查任务是否真的依赖目标模态、是否有歧义或泄漏。
3. **Video Plan、Generation 与证据回标。** Director 把脚本转成视频提示，Renderer 生成 1080p、44.1 kHz 立体声片段。Reviewer 实际观看视频，写 caption 和七方面质量报告；关键事实不清时，Director 提出聚焦 Video Q-A。Video Review 可以接受、换随机种子、返回脚本重写或丢弃。
4. **Reply 与 Rubric。** Reply Plan 只使用被实际视频支持的事实。Reply Generation 生成自然口语 reference reply 与分层 criterion；Reply Review 检查每条 criterion 是否二元、可由回复独立判断、符合 tier 顺序且被媒体证据支持。最终实例还经过人工检查。

以用户询问左右两扇会议室门为例，脚本希望左门关闭、右门打开。Reviewer 的 caption 无法确认门状态，于是 Video Q-A 明确画面左右门的开闭；Director 再结合前后摄像头决定用户坐标中的左右，并据此生成答案。若视频与脚本冲突，答案跟随视频。

### Multi-turn：联合计划与依赖感知修复

多轮系统先建立覆盖全部 turn 的联合 Plan，明确早期出现的物体、话题转移、摄像头或说话人变化，以及后续需要引用的旧 clip、音轨或最后一帧。Plan Review 在渲染前检查跨轮依赖和 media-reference budget。

每个 turn 的 Prompt Generation 直接结合联合计划与已接受媒体，替代单轮流程中分开的 Script Generation 和 Video Plan。Prompt Review 检查引用是否存在、当前轮是否泄漏答案以及与上一轮能否衔接。随后仍执行 Video Generation、Caption、Q-A、Video Review、Reply Generation 和 Reply Review；当前轮通过后，其媒体与 reference reply 才进入历史。

最终 Validation 检查完整记录、跨轮引用和必需字段。局部渲染缺陷只重试当前 turn；若 Turn 5 的问题来自 Turn 2 没有生成关键对象，系统从最早受影响的 turn 更新计划并重建后续链。论文评测只评分最后一轮，以隔离早期模型回复差异；这也弱化了对真实误差累积的测试。

### Rubric 标注系统

Rubric 将 reference reply 拆成有先决关系的 criterion。Tier 0 通常检查回复语言，不计分但失败后整题归零。Tier 1 表达任务成立所需的核心事实；Tier 2 补充关键细节；Tier 3 奖励语气、上下文贴合或附加帮助。当前 tier 可以部分得分，只有整层完成才解锁下一层。

最终 LLM judge 只读取候选回复、模型身份和 criterion，不读取视频、caption 或 reference reply。因此 criterion 必须自包含，不能写“符合上面的 caption”。reference reply 的作用是证明存在一个自然回复能够满足全部 criterion，而不是充当字符串匹配目标。

OmniVChat-Bench-Human 使用不同的前端取证流程。演员按十二个单轮子类别的中文指南选择变体，在真实环境用手机即兴录制；每个子类别 30 条，共 360 条。每段录制先生成三份独立 caption，其中一份含转录；系统合并事实并标记颜色、数量或位置冲突，再由人对照原视频修正。初始 caption 在 62 条视频中漏掉用户语音，说明人工事实校正不可省略。后续模型只读取已校正事实记录，最多经过三轮生成、验证和修改，产生 3 至 5 条 criterion 的 reference reply 与 rubric。

## 数学与训练机制

### 配置组合的无放回采样

令 $D$ 为属性集合，$V_d$ 是属性 $d$ 的可选值。一个 assignment $a$ 为每个属性选择 $a_d$，其权重为

$$
w(a)=
\prod_{d\in D}p_d(a_d)
\prod_{\pi\in\Pi(a)}m_\pi,
$$

其中 $p_d(a_d)$ 是目标边际概率，$m_\pi$ 是命中偏好规则后的乘数；排除项权重为零。对正权重组合采样 $U_a\sim\operatorname{Uniform}(0,1)$，计算

$$
k_a=\frac{\ln U_a}{w(a)},
$$

并选取最大的 $n$ 个 key。该 exponential race 与 Gumbel-top-$k$ 具有相同采样律，在一批数据内实现按权重无放回选择。它控制计划分布，但后续生成失败和质量过滤仍会改变最终交付分布。

### Tier-gated rubric score

令 $K_t$ 为 Tier $t$ 的 criterion 集合，$H(y)$ 为 judge 判定回复 $y$ 满足的 criterion。单实例分数为

$$
r(y)=
\frac{
\sum_{t=1}^{T}|K_t\cap H(y)|
\prod_{s=0}^{t-1}\mathbf{1}[K_s\subseteq H(y)]
}{
\sum_{t=1}^{T}|K_t|
}.
$$

乘积要求所有前置 tier 完整通过；分母包含全部非 Tier 0 criterion，包括因前置失败而锁住的项。早期 criterion 的一次误判会非线性屏蔽后续得分，这是层级表达能力的代价。

总体 Mean 先在每个子类别内部平均 $r(y)$，再对 17 个子类别等权平均，避免样本较多的子类别支配榜单。

### OmniVChat-RL 的一次更新

对输入 $x$，旧策略 $\pi_{\theta_{\mathrm{old}}}$ 采样 $N=4$ 个回复 $G(x)=\{y_1,\ldots,y_N\}$。每个回复的总奖励为

$$
R(y)=r(y)+\lambda_{\mathrm{fmt}}f(y)
+\lambda_{\mathrm{eff}}e(y)
+\lambda_{\mathrm{sty}}s(y),
$$

论文实验使用 $\lambda_{\mathrm{fmt}}=0.5$、$\lambda_{\mathrm{eff}}=0.1$、$\lambda_{\mathrm{sty}}=0.5$。$f(y)$ 检查非空回复和推理标签格式；$s(y)$ 只有在 qwen3.7-max 判定七项口语风格全部满足时才为一。

效率项只比较同一输入的四个回复。令 $w_i=\max\{w(y_i),1\}$，其中每个汉字或连续拉丁字母/数字串计一个单位。原始效率为

$$
\rho_i=\frac{r(y_i)}{w_i}.
$$

论文先用组均值归一化长度再计算 $z_i$，但公共正因子会在 min-max 中消去，等价于直接归一化 $\rho_i$：

$$
e(y_i)=
\frac{\rho_i-\rho_{\min}}
{\rho_{\max}-\rho_{\min}}.
$$

相同问题内，完整而短的回复会优于同样正确但冗长的回复；跨问题不直接比较长度。该设计对四样本组的极值敏感，也会奖励部分正确但非常短的回复，因此 correctness 主项仍不可缺少。

GSPO 用组均值作为 baseline，不训练 value model：

$$
A_i=R(y_i)-\frac{1}{N}\sum_{j=1}^{N}R(y_j).
$$

策略概率比按回复长度取几何平均：

$$
q_i(\theta)=
\left(
\frac{\pi_\theta(y_i\mid x)}
{\pi_{\theta_{\mathrm{old}}}(y_i\mid x)}
\right)^{1/|y_i|},
$$

降低整序列概率比对长度的依赖。目标对 $q_iA_i$ 使用非对称 clipping，提升高于组均值的回复概率并压低低奖励回复。训练没有 KL penalty，依靠极小 clip、$10^{-6}$ 学习率和 LoRA 限制漂移。

基础模型为 Qwen3-Omni-30B-A3B-Instruct。视觉与音频 tower 冻结；Thinker 的 Attention 和 MoE projection 使用 rank-64、$\alpha=256$ 的 LoRA，约 325M 可训练参数。每次迭代取 32 个输入、每个输入四个回复，共 128 个 completion；视频以 2 FPS、每段最多 16 帧输入。训练 1,000 步，每 20 步保存 checkpoint，按 560 条合成开发集的最高 Subcategory Mean 选择 step 940。

## 实验：问题、验证与答案

### Benchmark 能否区分系统？

**问题。** 分层 rubric 是否能在相同系统提示下区分不同 Omni 模型？

**实验。** 作者比较十一种已发布系统、OmniVChat-RL 和两个奖励消融，所有系统接收音频和视频。合成 benchmark 含 2,550 个单轮和 250 个多轮实例，覆盖 17 个子类别与 22 个场景领域。

**答案。** 已发布系统中，Gemini-3.5-Flash 的合成 Mean 最高，为 0.667；Gemini-3.7-Flash 的 Human 为 0.575。不同数据集的领先者不同，说明合成与人工录制排名并非简单复制。由于没有 audio-only、video-only、ASR-text 或时间打乱对照，榜单不能证明每个子类别都要求真正的联合音视频推理。

### 合成数据 RL 是否改善合成评测？

**问题。** 在 OmniVChat-Bench-Train 上优化 rubric、效率和风格后，模型是否在未重叠视频上提高？

**实验。** Qwen3-Omni-Instruct 训练 1,000 步，以开发集选择 step 940，再评测 OmniVChat-Bench。

**答案。** 合成 Mean 从 0.465 提至 0.652；训练 rollout 的 rubric 从 0.308 提至 0.629。结果支持模型更会生成满足该 rubric 系统的回复。训练 reward 与测试 metric 共享 scorer 和 qwen3.7-max judge，因此不能把全部增益解释为独立能力提高。

### 是否迁移到人工录制对话？

**问题。** 只在合成对话上训练，能否提高真实手机录制场景？

**实验。** OmniVChat-Bench-Human 含 360 条中文单轮录制，十二个单轮子类别各 30 条；不参与训练。模型 Human 分数从 0.402 提至 0.632，同期中文合成子集从 0.437 提至 0.634。

**答案。** 结果支持相同子类别和相同评分协议下的合成到真实迁移。它不覆盖多轮、英语真实录制、实时延迟或自然线上分布；人工集仍使用相同 rubric form 与相同 judge，因此没有提供独立的人类回复质量判断。

### Auxiliary reward 分别改变什么？

| 奖励设计 | 合成 Mean | Human | Reply Efficiency | Style |
| --- | ---: | ---: | ---: | ---: |
| 完整奖励 | 0.652 | 0.632 | 18.38 | 0.992 |
| 去掉 efficiency | 0.697 | 0.691 | 7.12 | 0.987 |
| 去掉 style | 0.661 | 0.632 | 13.70 | 0.788 |

去掉 efficiency 后正确性反而更高，说明完整奖励用内容完整性换取了更短回复；完整模型是多目标折中，不是 rubric accuracy 最优。去掉 style 主要损伤风格分数。Format 在训练中始终约为 1.0，经组均值中心化后没有实际学习信号。

### LLM judge 是否稳定？

**问题。** 排名是否只是 qwen3.7-max 的偶然偏好？

**实验。** 六个 GPT 与 Qwen judge 对同一组 Gemini-3.7-Flash 回复重新判断。criterion-level agreement 为 87.8% 至 96.5%，Cohen's $\kappa$ 为 0.532 至 0.845，17 个子类别画像的 Pearson 相关至少为 0.936。

**答案。** 结果支持不同 judge 对固定回复集的总体难度画像相近。该实验没有用六个 judge 重新测量 OmniVChat-RL 从 0.465 到 0.652 的增益，也没有人类评价候选回复，因此没有消除 reward–evaluator coupling。

## Takeaways

- **问题**：怎样构造、标注、评测和训练没有独立文字问题的原生音视频对话？
- **核心 idea**：生成音视频后重新观察，以渲染事实而非脚本生成 reference reply 和 tiered rubric；同一 rubric 再进入组内 GSPO 奖励。
- **可信结论**：OmniVChat-RL 显著改变回复策略，使其更符合任务 criterion、更短并更符合指定口语风格；同一评分协议下的中文真实录制集也提高。
- **仍未证明**：提高主要来自更强的跨模态 grounding，而非类别策略、rubric 适配或 judge 偏好。
- **可复用启发**：生成数据需要区分计划事实、观察事实和监督事实；开放式任务可用先决关系表达必要答案与附加质量。
- **不应外推**：实时、全双工、多轮真实用户闭环、英语真实场景和长期部署可靠性。

## 最脆弱的假设

最脆弱的假设是：人工录制集上的 rubric 增益主要来自更好的音视频 grounding。RL 冻结了视觉和音频 tower，judge 只读取回复与 rubric，许多子类别又存在稳定策略，例如等待未说完的用户、否认不存在的证据或简短确认连接。模型可能主要学会了更好的输出策略和 judge-compatible 表达。

这个假设若失效，论文仍然证明了有效的数据与策略优化闭环，但“合成数据改善原生跨模态理解”的结论要收窄为“合成任务改善同构开放式回复指标”。模型身份和物理行动边界还依赖部署配置；公开数据为 Physical Limitation Awareness 额外提供具身与无身体两套相反 rubric，进一步说明总体 Mean 混合了感知能力和产品策略。

## 一周最小复现

目标是判断增益是否依赖音视频证据，不复现 30B 训练。

1. 从公开数据选 SVMR、AR/DR、SPSD 和 ER 四类共约 400 条，它们分别需要摄像头方向、语音指代、说话人和声画情绪证据。
2. 为每条样本制作原始、静音、单帧、音频错配和 ASR 文本加静态图五种输入；另外录制约 60 条匹配子类别的手机视频。
3. 用可运行的 3B 至 7B Omni 模型做小规模 LoRA，比较 rubric-only 与完整 reward；固定数据、rollout 数、训练步数和系统提示。
4. 同时用论文 judge、一个独立 judge 和少量人工 pairwise 评价，记录 rubric、回复长度、模态干预下降与真实录制迁移。
5. 只有当完整音视频增益显著高于 ASR-text，静音与错配产生符合任务预期的下降，且独立 judge 和人类保留大部分增益时，才把结果解释为 grounding transfer。

## 如何反驳：反例设计

构造最小反事实对：保持语音不变只替换被指对象；保持画面不变只改变说话人或情绪语调；保持对象和语音内容不变只切换摄像头朝向；再把同一语义从生成视频替换为真实录制。每组都包含 audio-only 足够、video-only 足够和必须联合两者三种条件。

若 OmniVChat-RL 在原始输入上提高，却在关键媒体被替换后仍给出相同答案，说明它主要学会了类别模板。若 ASR-text 条件获得相近增益，sim-to-real 更接近回复策略迁移。该结果不会否定 Studio 的标注价值，但会反驳“跨模态感知本身得到显著改善”的强解释。

## 后续研究与新认知

检索截止 2026-10-04，距 arXiv v1 发布约两周，尚未找到独立复现、扩展或正式反驳。官方已发布 2,800 条合成 benchmark、约 28 GB 媒体、evaluation scorer、reward 与 trainer adapter。当前没有发布 OmniVChat-Studio 实现和 360 条 OmniVChat-Bench-Human；公开多轮 JSON 也不含论文协议向所有模型提供的前序 reference replies，因此无法只用发布文件完整复现多轮评测。

公开代码确认 training 和 evaluation 导入同一 tier scorer。代码模板默认只启用 rubric 与 format，efficiency 和 style 默认关闭；复现论文实验必须显式使用论文的 $0.5/0.1/0.5$ 辅助权重，不能把模板默认值当作论文配置。数据采用 CC BY-NC-ND 4.0，限制了商业使用与衍生分发。

## Follow-up idea

**分析提案：因果模态 rubric。** 现有 rubric 只描述答案应该包含什么，没有描述答案必须对哪段证据敏感。可为每条实例增加最小必要音频、最小必要视觉、是否需要历史 turn，以及只改变一个关键事实的音频与视频反事实。训练时同时奖励原样本与反事实答案正确，并惩罚关键证据改变后回复保持不变。

这会把监督对象从“生成符合 rubric 的语言”改成“对造成答案变化的证据作出正确响应”。最小证伪实验是在 SVMR、AR、SPSD 和 ER 上比较普通 rubric RL 与因果配对 RL；若后者不能提高反事实一致性或增大必要模态被移除时的性能下降，该方向就没有成立。

## 与 Wiki 的连接

- [[qwen2-5-omni]] 提供 TMRoPE、音视频编码和 Thinker–Talker 的模型基础；本文补充训练数据、开放式评测与 Thinker 回复策略优化。
- [[qwen3-8-omni]] 将 Omni 模型扩展到长上下文和 Agent 取证；本文说明即使输入接口已经原生，多模态能力仍受数据、rubric、judge 和运行协议共同决定。
- [[omni-model-architecture-paths]] 因本文增加一条与架构正交的比较轴：模型是否在模态干预下表现出真正的因果敏感性。
- [[omnivchat-grounding-attribution]] 追踪合成数据、感知 grounding、回复策略和 judge 适配的贡献分解。

## 来源与证据边界

- Haolin He 等，OmniVChat: Synthesizing, Benchmarking, and Training for Native Audio-Visual Dialogue，arXiv:2609.21465v2：https://arxiv.org/abs/2609.21465
- 官方 HTML 全文：https://arxiv.org/html/2609.21465
- 官方代码：https://github.com/HarlandZZC/OmniVChat
- 公开数据：https://huggingface.co/datasets/Harland/OmniVChat
- 阅读日期：2026-10-04。
- 阅读范围：用户提供的 arXiv v2 PDF 全文 48 页，包括正文、全部方法与实验附录、合成和人工录制样例；同时核对官方代码、数据结构、默认 reward 配置和发布缺口。附件未复制进仓库，也未记录私人路径。
- 用户关注：Single-turn 与 Multi-turn 数据生成、rubric 分数和 OmniVChat-RL 的逐步训练机制；这些部分在本文中按论文原始流程展开。
- “作者思路重建”“最脆弱的假设”“反例设计”和 Follow-up idea 均为分析，不代表作者原话。后续研究只报告检索到的一手来源与明确时间边界。
