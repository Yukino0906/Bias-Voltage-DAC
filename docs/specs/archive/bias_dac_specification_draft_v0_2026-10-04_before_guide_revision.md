# Bias-Voltage DAC — Specification Draft v0

Date: 2026-10-04 · For mentor discussion · Not approved / not yet demonstrated

配套证据与 Rxx 文献编号见 [Literature review](cryogenic_bias_dac_literature_review_2026-10-04.md)。下面数值分为 **[Current] 当前条件**、**[Proposal] 工程建议**、**[Derived] 计算得到**、**[Literature] 文献依据**、**[TBD] 需系统确认**。当前的 3-bit / 1 V / 111 fF 都不自动成为最终 specification。

## 1. 推荐的 block 定位

**A low-power, programmable DC bias-voltage DAC for high-impedance electrostatic gates in semiconductor quantum-dot systems, with a staged path toward cryogenic operation.**

先以单通道 transistor-level CDAC 为验收对象；reference 与数字输入可外部提供，但功耗表必须说明统计边界。之后再决定是否共享 DAC + 多路 S&H。当前采用 TSMC65 TG 和 MIM 作 baseline，并不锁死最终 switch flavor、capacitor technology、bit depth、温度或输出范围。

优先目标是 DC tuning / hold，不是 microwave source 或 arbitrary waveform generator。先在 27 °C 完成结构与误差预算，再以经过验证的模型或实测讨论 4.2–6 K；mK 是长期系统研究目标，不能仅靠 Spectre temperature setting 验收。[Literature: R01–R03, R06, R09, R16–R18]

## 2. 阶段 A：当前 3-bit 原型应先证明什么

| 项目 | 验证条件 / 暂定判据 | 来源 / 如何验证 |
|---|---|---|
| Process / temperature | TSMC65 nominal，27 °C；确认当前 model section 与实际 netlist | [Current] 环境证据；输出 model path / section / DUT cell 名 |
| 电容阵列 | C/2C/4C + dummy，8 个约 110.659 fF unit | [Current] 记录原理图及 instance 参数，非尺寸优化结论 |
| Reference / supply | Vu = 1 V、Vl = 0 V；TG VDD = 1 V、VSS = 0 V；核对器件允许端电压 | [Current] 理想 reference 与控制源可保留，必须标明 |
| 全码功能 | code 000→111→000；约 0、0.125、…、0.875 V；检查 011↔100 与 000↔111 | [Derived] 无额外负载/理想比例时 Vout = code × 1 V/8；real PDK parasitic 会改变结果 |
| 可接受的首次功能偏差 | 建议先用 nominal settled error ≤0.25 LSB =31.25 mV；这是初步功能门槛，不是最终精度 | [Proposal] 同时输出真实 mV 误差，不以“通过”掩盖 charge injection |
| 单调性 | 8 个稳定电平严格递增；必须报最小实际 step | [Proposal] 对各 code 固定时间窗取值；不从平滑曲线外观判断 |
| Settling | 首先报告达到 ±0.25 LSB 所需时间；已有测试可先在 code 改变后 20 ns 检查，未满足则诊断 | [Proposal] 20 ns 是本地调试观察点，不是 qubit 应用要求 |
| Control sequence | reset / code update / hold 可辨认；Vu/Vl 两支参考开关不能产生持续短路；EN/ENB 互补 | [Proposal] 同画控制和 reference currents；检查同时导通、悬空窗口 |
| TG integration | 所有实际替换/未替换位置逐项记录，特别是 reset switch | [Current] 仅替换 b2 pair 不能称为“全部 transistor-level DAC” |
| Off-state / hold | 单独报告关断前后 ΔV、随后 dV/dt、input 改变时 held-node 耦合 | [Current + Proposal] 已观察独立TG约 +3.2 mV，但不能假定集成后仍是同一个值 |
| Load sensitivity | 先无附加外部 C；再试 10 fF、100 fF、1 pF，不在本阶段承诺无 buffer 可驱动1 pF | [Proposal] 同时报 gain 与 settling 的变化；模拟源与量测不能意外 clamp Vout |

**当前最重要的交付物：** 一张带 code/reset/reference-select 波形的全码阶梯图、一张 code→settled-Vout 表、一张 Ron vs signal voltage 图。比先把每项论文规格写进报告更有价值。

## 3. 阶段 B：下一轮可以实现的工程目标

阶段 A 通过后再考虑 **8-bit 单通道 feasibility**。不是现在立刻把 schematic 扩成 256 unit；先比较 plain、split、segmented 的 capacitance/寄生/mismatch 成本。

| 项目 | Draft target | 理由与测试 |
|---|---|---|
| Resolution / range | 8-bit、1 V reference span，LSB =3.90625 mV；最大 binary code 为255/256 V | [Proposal/Derived] 便于从3-bit跨到可量化精度；不声称足够满足qubit最终要求 |
| Static linearity | nominal gain/offset-corrected INL、DNL 目标各 ±0.5 LSB；必须 DNL >−1 LSB | [Proposal] 提供 raw 及 corrected 两组，全256码；若失败先定位再修改目标/结构 |
| Settling / update | 初始设计点1 kupdate/s，±0.25 LSB内 settling ≤10 µs | [Proposal] 为低速bias保留大余量；不是从GHz控制论文复制的速度 |
| Load | 先以总外部1 pF为系统探索条件，验证range是否仍可达；失败时在cap size、隔离S&H或buffer间选择 | [Proposal] bufferless输出不可直接假设外部C只影响速度 |
| Hold / disturbance | turn-off、droop、refresh glitch分别列出；1 ms内droop探索目标≤0.25 LSB | [Proposal] leakage current source sweep + 瞬态；真正负载TBD |
| Variability | nominal → 支持的PVT → capacitor/MOS mismatch Monte Carlo；报告样本数和分布，不先声称yield | [Proposal] 先确认PDK mismatch option和统计模型确实生效 |
| Power | 报总power及其随refresh/update rate变化，不暂定严格pass/fail | [Proposal] 必须包含TG控制源和reference提供的能量；共享部分另外列 |
| Capacitor | MIM baseline vs一个可用MOM候选，同电容、同拓扑比较 | [Proposal] model + layout/PEX evidence；不在模型缺失时硬比“cryo精度” |

## 4. 阶段 C：给 mentor 讨论的 cryogenic 应用目标

推荐先讨论 **“1 V span、12-bit nominal step、单通道→8通道、4 K class characterization”** 这个相互关联的组合。它是原参考研究附近的可解释起点，不是追平18-bit论文，也不暗含真实目标gate一定接受0–1V。

| 项目 | 建议草案 | 证据 / 未决条件 | 验证方式 |
|---|---|---|---|
| Application | QD plunger/barrier 的慢速DC bias | [Proposal] R01/R02/R06/R13；具体device与工作点[TBD] | mentor确认gate用途与允许扰动 |
| Output span / polarity | 暂定相对Vl的1 V span；绝对offset/负压[TBD] | [Proposal] R01提供先例；R19说明1 V并非通用 | end-point、loaded-range、端电压stress检查 |
| Nominal resolution | 12 bit，即244.14 µV/LSB；13 bit作为stretch而非必选 | [Derived + Proposal] 参照R01应用级量级；不是12-bit absolute accuracy | 全码transfer、最小step、可达范围 |
| Static error | 校准后 INL ≤±0.5 LSB，DNL目标±0.5 LSB且必须>−1；raw也保留 | [Proposal] 允许gain/offset calibration；是否允许per-code LUT[TBD] | code sweep、endpoint/best-fit方法声明、MC/PEX |
| Temporal settling | nominal≤100 µs到±0.25 LSB；所有实际负载重验 | [Proposal] 与1 ms refresh slot相容；不是文献的统一要求 | 大步进/major-carry及最差前后code，含reference source Z |
| Refresh / retention | 初始扫描10 Hz、100 Hz、1 kHz、4 kHz；设计讨论点1 kHz，每次hold 1 ms的droop≤0.25 LSB≈61 µV | [Proposal] R01/R06显示refresh与leakage依赖；最终period[TBD] | turn-off后去掉初始跳变，测最坏code的slope与最大偏差 |
| Noise | 起草值≤0.1 LSB≈24 µVrms；先规定1 Hz–10 kHz的连续时间输出噪声，并另报sample-to-sample variance | [Proposal] **不是由qubit fidelity推导**；实际frequency weighting[TBD] | 合适noise/PSS+pnoise或transient-noise；reference/clock贡献分列 |
| Injection / refresh glitch | hold平台的可重复offset可校准；随机残差与瞬时glitch单独分配预算 | [TBD] 不能用固定+3.2mV推定全码可校准 | input/common-mode、edge/skew、width及code-dependent sweep |
| Load | 高阻electrostatic gate；Cload和Ileak尚未确认；探索10 fF–10 pF与10 fA–10 pA | [Proposal sweep] 这是探索范围，不是允许的最终负载范围 | 量化gain/settling/droop；查pad/ESD/互连并PEX |
| Power | 暂讨论8ch摊销后≤5 µW/ch，refresh约1 kHz；单独为共享reference/clock/decoder等分账 | [Proposal] R01/R02同量级启发；不能给当前未设计digital直接记零 | 对每电源/控制/参考端积分，idle和update单列；热预算由系统确认 |
| Total heat | 例如8ch×5µW=40µW只是DAC分账；完整系统限额[TBD] | [Derived] 必须另加reference generation、I/O、buffer以及同温区其他block | 按热化位置统计总功耗；mK最终需要热实验 |
| Area | 先报告cap-only、DAC core、每hold channel、含pad的总面积；不强定mm² | [TBD] R09细胞面积不可跨工艺直接照抄 | floorplan / PEX / density与routing检查 |
| Temperature | 27°C baseline；4.2–6K为首个cryo验证目标；100mK级留远期 | [Proposal] 低温model/measurement可用性[TBD] | 可校准模型+实验；报告bath、package、chip/电子温度区分 |

这些误差分项**还不是闭合的总精度预算**：0.5 LSB static +0.25 LSB settling +0.25 LSB drift 已占1 LSB，noise、reference误差与注入随机量尚未并入。如果系统只允许总误差0.5 LSB，必须重分配而不是宣称此表已满足。校准后的精度需连同reference准确度与温漂重新定义。

### 为什么不先写“1 V、10 µV精度、零功耗、mK”

步进的算术关系为 N ≥ ceil(log2(Vspan/ΔV))。1 V范围下，12-bit步进244 µV；10 µV步进需要至少17 bit，1 µV步进至少20 bit。**步进足够小仍不保证相应accuracy/noise**。R05的小step与更大noise/INL正说明这个差别；R24的标题指标要等全文确认频带和校准条件。若真实需求是1 V粗调+10 mV窗口内细调，可以研究coarse/fine，但不等价于全范围绝对10 µV准确。

## 5. 把 specification 连接到 Ron、cap 和负载

### Ron 从 settling 预算反推

对单极点近似：

`|error(t)| = |ΔVinitial| exp(−t / (Req Ceff))`

`Req ≤ tsettle / [Ceff ln(|ΔVinitial| / ε)]`

例：1 V初始误差、12 bit、ε =0.25 LSB =61 µV，ln项约9.70。若**电路实际等效负载**为1 pF、tsettle=100 µs，近似Ron上限约10.3 MΩ。这说明慢速bias未必需要几十Ω；实际设计还要考虑reference源阻抗、多极点、时序余量与保持误差。这个数不是TG尺寸推荐。

本原型Ctot=8×110.659 fF=885.272 fF。当只有一支bottom plate通过电阻改变，其余bottom plates是AC ground、top浮置且无附加载荷时，该支看到的等效电容为 `Cb(Ctot−Cb)/Ctot`；MSB Cb=4C时为2C≈221 fF。**不能一律把8C当成每个switch的Ceff**。多支同时切换/finite Ron、top parasitic和load改变等效网络，应以完整瞬态验证。

Standalone Ron test：EN=VDD、ENB=VSS，A/B平均电压扫整个有效信号范围，施加小而非零的差分（如1 mV，并用5 mV检查线性区），记录 `Ron=|VA−VB|/|IAB|`。中点附近和两端均要测；端点测试保持各端不越rail。再分别只开NMOS/PMOS进行对照。R06的7 mV方法是实验先例，不是我们的固定标准。

### Hold capacitance 与误差预算

`ΔVdroop ≈ Ileak,total × Thold / Chold,eff`；即使低温降低channel leakage，ESD、gate leakage、load和charge jumps仍可能限制保持。[R06/R13]

按上述12-bit草案，61 µV/1 ms要求：若 Chold=1 pF，总leakage≤61 fA；若仍只有111 fF，则≤6.8 fA。两个数是**推导出来的限制**，不是PDK能达到的承诺。10 pA负载若要保持同样误差，需要约164 pF，随后面积/速度/能耗都会变。这是必须先问“load是什么”的原因。

简单sampled thermal noise基线为 `sqrt(kT/C)`。111 fF约为300 K时193 µVrms、4.2 K时23 µVrms；整个885 fF若确实作为单一sampling capacitance，则约68 µVrms与8.1 µVrms。实际CDAC含多次采样、开关和reference噪声，此公式只是数量级检查，不能据此宣称低温noise已满足。

若当前885 fF浮置top直接增加一个最初无电荷、接地的1 pF load，简单模型的step gain会乘以885/(885+1000)≈0.469。该load还改变reset条件；**外部电容既影响稳态比例，也影响速度**。选大cap、校准、增加隔离S&H或buffer前必须弄清负载连接方式。

## 6. Mentor 五问的初稿回答

| 问题 | 初稿回答 |
|---|---|
| What specifications should this block meet? | 一个可校准、单调、稳定的高阻gate DC bias source；先3-bit闭环，下一阶段8-bit工程可行性，再讨论1 V span/12-bit/低µW每路的cryogenic目标。绝对电压、负载、温区、noise频带与热预算仍需系统指定。 |
| What simulations verify the specs? | 全码transfer和INL/DNL；major-carry/大跳变settling；TG Ron vs common mode；turn-off step、feedthrough、hold droop；reference/clock power积分；load与leakage扫参；正常温区PVT、mismatch MC与PEX；有可信低温model后再做cryo矩阵，最终实验确认。 |
| Why is this block a proper choice? | Capacitor ratios减少对精密static transistor bias的依赖；高阻负载允许低static core power，刷新可稀疏发生；TG传输范围比单NMOS更适合当前0–1V跨度。但reference、digital和buffer功耗不能忽略；大负载或持续电流场景可能换buffer/integrator架构更合适。 |
| Main challenges? | 低温model不确定；Vth/headroom导致Ron峰值；mismatch/寄生导致非线性与不可达电压；charge injection/clock feedthrough；hold leakage及ESD；输出range/负载；reference noise、数字串扰、自热与冷却资源。 |
| Circuit/system solutions? | 从settling budget定W并权衡注入；按允许端电压评估器件flavor；非重叠控制与适当reset/采样顺序；匹配版图、dummy/屏蔽和PEX；校准/overlap按错误机制选择；programmed refresh、安静保持时段；高阻隔离与必要buffer；合理封装与thermal anchoring；模型/测量联合迭代。 |

## 7. 本周三小时的优先级

| 时间 | 工作 | 可展示结果 |
|---|---|---|
| 0–15 min | 核对最新DUT、供电、control、symbol/netlist；列出哪些switch仍ideal | 一份明确的test condition记录 |
| 15–75 min | 跑TG替换后的现有3-bit DUT；先code100，再全8码；排查reference shoot-through及reset | 阶梯图 + code/voltage表；若有故障先定位 |
| 75–135 min | Standalone TG Ron sweep，至少nominal；需要时比较少量W组合 | Ron–signal曲线，说明为何该尺寸足够 |
| 135–160 min | 关断step与hold slope、reference/clock current；将系统负载问题写出 | 一张误差/功耗观察表，不承诺完整优化 |
| 160–180 min | 阅读本草案并准备mentor讨论；整理证据 | 5–6个决策问题 + 当前结果 |

若netlist/功能排错耗时超过1小时，压缩尺寸扫描而保留baseline与问题记录。**MIM→MOM替换、12-bit扩展、cryo参数拟合、全PVT/Monte Carlo和layout都不要求本周完成。** 文献检索作为独立工作，不挤占手上这三小时的电路闭环。

## 8. 下次 meeting 要确认的六个问题

1. **P0 应用接口：** 实际接QD的哪类gate，还是接ΣΔ/analog bias？输入是纯电容还是有持续电流？
2. **P0 范围与精度：** 需要哪个绝对电压范围、polarity和reference？“resolution”指step、噪声还是绝对accuracy？可否校准？
3. **P0 温区与验证：** DAC实际放4K还是mK？本学期需要cryo measurement还是literature-grounded simulation？有没有可信65nm低温model？
4. **P1 Timing：** DC调谐、refresh、qubit pulse各自速率是多少？允许何时出现refresh glitch？保持多久？
5. **P1 资源：** 单路/全芯片功耗预算、channel count、load/pad/ESD/line length与area如何分配？是否包含reference、buffer和digital？
6. **P1 工艺选择：** mentor提MOM主要是minimum unit、metal stack、面积、mask/可制造性、matching还是低温经验？`nch_33_dnw`建议针对高压、隔离、漏电还是所有switch？未确认前不把它推广到所有MOS。

首次需要mentor做的最小决策：认可application A作为临时方向；认可3-bit→8-bit→12-bit讨论路径；明确温区验证边界。其余目标可带着当前baseline结果继续收敛。
