# Cryogenic Bias DAC：文献检索与应用选择

日期：2026-10-04。状态：mentor 讨论材料；不是已批准的系统规格。配套：[Specification draft v0](bias_dac_specification_draft_v0_2026-10-04.md)。

## 建议先讨论的结论

推荐把本项目暂定为 **面向 semiconductor quantum-dot / spin-qubit gate 的低速、低功耗 programmable DC bias block**。先做单通道，再研究多通道 sample-and-hold / refresh；不要同时承诺 microwave control、高速任意波形和 mK 测量。这个定位最接近已有 charge-redistribution DAC + TG 工作，也与原始参考论文的实际用途相符。[R01–R03, R06, R09, R13]

有三项比“最终用几 bit”更先决定：输出相对什么参考地、实际负载与连接长度、DAC 放在 4 K 还是 mK。0–1 V 适合当前实验，但不是所有 Si/SiGe、Si-MOS 或 GaAs gate 的通用范围。4 K 控制器驱动 mK 器件和控制器自身处于 mK，是不同任务。[R02, R06, R09, R19]

本轮保留 **24 项文献记录**，包括同一工作的会议/期刊扩展和后续系统实证，不能当成 24 个独立 DAC benchmark。核心全文重点阅读为 R01、R02、R04、R05、R06、R07 的公开预印本、R09–R13、R18；R08/R19/R20 读取开放网页的相关实验章节。其余按摘要/出版信息筛选，状态在文献表中逐项标明。检索从原论文参考文献及后续同团队研究扩展到 IEEE、Nature、AIP、IEICE、arXiv，以及 Delft、Jülich、EPFL、Kobe 等作者机构存档。不是系统综述，也不宣称穷尽所有工作。

## 应用路径及边界

| 路径 | Bias DAC 实际作用 | 主要约束 | 与当前项目的关系 |
|---|---|---|---|
| **A：QD electrostatic DC bias，推荐** | 保持 plunger/barrier gate 工作点；低速调谐与刷新 | 小步进、可校准准确度、低频噪声、droop、reference、低功耗 | CDAC + TG + 高阻负载适合做起点；尚未证明完整 qubit control |
| B：4 K bias/control ASIC 的慢速辅助偏置 | 给 cryogenic analog/readout/control 电路提供偏置 | 负载电流、PSRR、启动、drive capability | 更容易形成工程闭环；若驱动电阻性负载，可能必须加 buffer；与早期 ΣΔ modulator 合作是否同一需求待确认 |
| C：mK charge-lock + fast gate pulse | 外部或共享 DAC 先设置 DC，局部电容再产生快速脉冲 | pulse fidelity、feedthrough、数字串扰、热化 | 可作远期扩展；不能把 CLFG 的低脉冲能耗算作包含 DAC 的总系统功耗 [R07–R08] |
| 不宜混合：microwave / superconducting flux control | GHz 载波或持续电流/磁通控制 | 相位噪声、RF bandwidth、时序或输出电流 | 不应直接借用其速度和功耗作为本项目验收条件 [R14–R15] |

## 核心证据摘记

以下页码优先为论文印刷页码；没有印刷页码时注明 PDF 页。机构封面可能使 PDF 页码多 1–3 页。数值是各论文自己的测试条件，不是对本项目的保证。

### R01：最直接的架构参考，实测温度是 6 K

65 nm、8 路、13-bit 编码的 coarse/fine capacitive DAC，输出 0–1 V；Table I 的约 250 µV/12-bit 与 100 mK 是应用要求，最终实现/测量不能混为一列。Fig. 8–9 展示 coarse 区域边界的寄生引起的覆盖缺口及补偿。Table II：DAC core 77 nW、reference 抽取 3 nW、digital 21 µW；21.1 µW/8 = 2.63 µW/ch，加入 4.3 µW clock buffer 后为 3.18 µW/ch。**3 nW 不包含外部 reference generator 功耗**。默认输出无 buffer，测量输入阻抗会影响结果。证据：Sec. II–IV、Table I–II、Fig. 8–9。

### R02：mK refrigerator 不等于 mK silicon

延续 R01 的 65 nm、8 路 DAC。测量时 mixing chamber 为 37 mK，IC 附近 interposer 为 965 mK，qubit electron temperature 约 500 mK；全 IC 30 µW、DAC 部分 13 µW（1.6 µW/ch），refresh 3894.1 Hz。约 100 µVpp ripple 与 125 µV/s drift 分别有刷新/停钟条件。标题/摘要中的 **4 nW/ch 是扩展推算**，不是当时 8 路芯片的实测值。证据：pp. 2–4，Fig. 2、Table I。GaAs 的相对负偏压通过提升 2DEG reference 实现，不说明普通 0–1 V DAC 可直接提供任意负电压。

### R04–R05：小 LSB、noise、INL 是三个数

22 nm FinFET integrator-based DAC：4.2 K、0.3–3.3 V、57.1 µV step、157 µW、0.076 mm²，测量负载约 480 pF。R05 pp. 7–8：单次 ramp 统计 noise 约 188 µVrms；去除部分高频测量贡献后的 accumulated noise 为 76 µVrms；amplifier noise 在 1 Hz–2.5 MHz 积分为 44 µVrms。这些不能互换。未校正 INL 36.5 LSB，经过 gain/offset 和 polynomial correction 后 2.1 LSB。数万 electrode 是负载估算的扩展能力，并非实测数万通道。证据：R04 p. 229 Table 1、R05 Fig. 7–12/Table I。作者结论与摘要存在 188/192 µVrms 表述差异，此处采用测量正文。

### R06：真实系统的 ESD、负载、温度与漂移

22 nm、96 路 S&H、每路 15 pF（60 × 60 µm²），结合 quantum-device array。Sec. III-C 的约 120 µW 是以 refrigerator heater/温升比较估计，非直接 supply-current measurement；66 mK 是测得 MXC 温度，不能自动当作 junction temperature。保持漂移从初期 18 mV/s 降至约 200 s 后 60 µV/s，强烈依赖 bias；不是一个全范围恒定 leakage。Fig. 5 用 7 mV switch differential voltage 测 Ron；Fig. 6 指出 ESD 路径可能主导 leakage。证据：Sec. II、III-B/C、Fig. 5–6、12–15，PDF pp. 6–14。这是当前 TG 与保持误差分析的重要参考。

### R07–R08：sample-and-hold 有实证，但不等于集成完整 DAC

R07 的公开预印本 pp. 3–6、Fig. 2–4：28 nm FDSOI、32 CLFG cells，DC bias 与 pulse rails 来自外部；开关关断偏移和耦合通过软件校准。qubit 近端温度与 mixing-chamber 温度有明显差异。R08 在 silicon spin-qubit 上进一步比较真实 single-/two-qubit 操作；Fig. 1 和 Experimental platform 说明仅 J/B 两个 gate 接 cryo-CMOS，其余部分仍由室温仪器驱动。故“与 qubit 兼容”需要系统实验，不能只靠 DAC 阶梯图证明。

### R09：小 MOM 单元需要面对 mismatch/calibration

40 nm、8 K 测量，11-bit split CDAC，6 fF unit MOM，DAC core 90 × 90 µm² ≈ 0.008 mm²，3.9 kHz 时 5.8 µW。pp. 2–4/ Fig. 2、6–9 / Table I 说明数字与 level shifter 占明显成本。正文报告 calibrated INL ±2 LSB、DNL −2 至 +0.5 LSB，**不能转述为已保证单调**。校准改善在这个 mismatch 较小的样品上不明显，强改善主要由仿真展示。摘要的 0.3 mm² 与标题、版图和结论不一致，采用可核对的 core 尺寸并保留这个原文矛盾。buffer 的系统功耗归属仍需进一步核实。

### R10：MOM 低温数据有价值，但不是 MIM/MOM 胜负证明

TSMC 40 nm 的特定 stacked interdigitated MOM，金属 M1–M5、poly shield。Table 1 p. 451：提取的 C 从 RT 191 fF 到 4 K 197 fF，约 +3.1%；Cpar 从 28 到 26.5 fF。正文“<1%”指测量精度，不是温度变化量。此研究主要针对 microwave passives，忽略的 DC leakage 不可视为零；也没有给出我们 TSMC65 的 MIM/MOM matching 对照。证据：Sec. III、Fig. 2–3、Table 1。

### R11：温度变化、尺寸与 mismatch 的相互作用

40 nm bulk CMOS，300–4.2 K 的器件测量。Pelgrom scaling 仍可用于这些实测样本；Croon 模型覆盖 moderate–strong inversion，边缘器件需要 dummy。固定 gate bias 下温降可能同时改变工作区，不能用统一 mobility multiplier 推导所有 TG 的 Ron。证据：Fig. 6–11、Sec. IV–V；这不是 capacitor matching 数据，也不适用于未经验证的 TSMC65 cryo 参数。

### R12：最近综述可补架构/封装背景

作者报告 40 nm、11-bit CDAC，以及 cryogenic ADC、silicon interposer、Cu–Cu integration。DAC 与 RF block 在系统图上被区分。其 DAC 叙述与 R09 属同一研究线，不能把综述再当作一个独立性能纪录。公开 advance manuscript 有排版错误；以最终文章 pp. 499–507、Sec. 2/Fig. 1–6 为定位。适合 mentor 讨论应用、buffer 和封装层次，不作为我们 65 nm 可用工艺选项的依据。

### R13：注入与随机噪声必须分开

Si/SiGe 自制 transistor/cap/QD 单片结构，不是标准 TSMC CMOS。Table I / pp. 144002-2–4：三个结构的关断偏移显著依赖 capacitor/switch 尺寸；device B 约 0.697 pF，初期 40 s 平均漂移约 2.8 µV/s。系统偏移可校准，而背景低频 charge noise 不因此消失。实验 refrigerator base <10 mK，不是直接 silicon thermometer。对本项目的启发是分别测 turn-off step、hold slope、input-to-held-node coupling，不把一次 +3.2 mV 全部叫作 leakage。

### R18：reference 不是免费且 weak inversion 并非禁区

40 nm reference 实测覆盖 300–4.2 K，使用 weak-inversion MOS；DEM、body effect、温度曲率和 startup 都重要。Fig. 12 的部分功耗图还排除了额外 divider 电流，提醒统一统计边界。Sec. IV/V、Table I 不能支持“任意 PDK 设低温即可预测”，却足以否定“cryo 下 weak inversion 全部不可用”的概括。

## 从证据得到的设计判断

**TG Ron 是必要条件，但不应独立最小化。** 固定允许的 settling error 与负载，再得到 Ron 上限；扩大 W 会同时增加 charge injection、clock feedthrough、clock-drive power 与寄生负载。整机最终误差还取决于 reset switch、reference impedance、控制互补时序、hold switch 和输出负载。R06 的具体 20–40 Ω 开关目标针对其布线和 15 pF storage，不适合直接抄到本项目。

**MIM 暂时保留作 baseline，MOM 是值得评估的候选。** R09 展示小 MOM unit 的面积优势和 mismatch/calibration 成本；R10 展示实际金属层、shield、Cpar 与温度变化的重要性。当前没有足够证据说“TSMC65 MIM 不适合 cryogenic”或“MOM 必然更线性”。需要本 PDK 的允许 metal stack、可用 PCell、minimum geometry、density、matching model、voltage coefficient、terminal parasitics、layout/DRC 代价；实际低温 matching/leakage 则仍需测量或可信文献。不要用 symbol 画得大来判断物理面积。

**低功耗 CDAC 合适的前提是高阻、小且已知的负载。** 大互连电容改变 charge-sharing gain 与速度，泄漏消耗保持误差预算；若每次更新必须驱动长 cable/大阵列，buffer/integrator 或隔离式 S&H 会改变面积与功耗最佳点。[R01, R05, R09] 本周直接把 unit 从 111 fF 改成论文的 6 fF，不能得到论文性能。

**冷热模型应分层。** 当前 foundry nominal 仿真是室温 electrical baseline。常规温区内的 PVT 可以用确认适用的 model corners；4 K/mK 必须检查模型校准范围。单纯输入 −269 °C、手动 Vth+150 mV 或 mobility×1.5，只能标为 sensitivity study，不能证明 cryogenic spec。[R11, R16–R18]

**对旧研究笔记的限定。** `phase2_cryo_architecture_research.md` 保留作为历史探索，本轮不改写它。但其“capacitor 几乎不变”“weak/moderate inversion 不可用”“零静态功耗”“简单统一 cryo corners”应按上述证据收窄；4T+6B、coarse overlap 等仍是待验证方案，不是 mentor 已批准架构。LSB、σDNL、max DNL、ENOB 也不能互换。

## 可核实的文献目录

作者较多时采用第一作者 et al.；链接到 DOI 或作者/机构原始来源。F = 已取得全文并重点阅读相关架构/实验章节；H = 阅读开放 HTML 相关章节；A = 本轮仅摘要；B = 仅出版信息/官方介绍；S = 补充筛选而未深入阅读全文。摘要记录不提供未经证实的页内细节。

| ID / 状态 | Title / 作者 / 年份 / venue | DOI 与开放来源 | 本轮用途 |
|---|---|---|---|
| R01 F | **Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications** — P. Vliex et al., 2020, IEEE SSC-L 3, 218–221 | [10.1109/LSSC.2020.3011576](https://doi.org/10.1109/LSSC.2020.3011576) · [全文](https://juser.fz-juelich.de/record/888069/files/FINAL%20VERSION_QC.pdf) | 原项目 paper；6 K baseline |
| R02 F | **Qubit Bias using a CMOS DAC at mK Temperatures** — R. Otten et al., 2022, ICECS | [10.1109/ICECS202256217.2022.9971043](https://doi.org/10.1109/ICECS202256217.2022.9971043) · [全文](https://confcats-event-sessions.s3.amazonaws.com/icecs22/papers/6353.pdf) | R01 芯片的系统后续；温度/功耗边界 |
| R03 F | **SiGe Qubit Biasing with a Cryogenic CMOS DAC at mK Temperature** — L. Schreckenberg et al., 2023, ESSCIRC, 161–164 | [10.1109/ESSCIRC59616.2023.10268801](https://doi.org/10.1109/ESSCIRC59616.2023.10268801) · [机构摘要](https://juser.fz-juelich.de/record/1018304) | R01 后续；全文核实 0.96 µV/s、275 µVpp ripple、20 µW DAC；64.5 pW/ch 为外推 |
| R04 F | **A 3V 15b 157μW Cryo-CMOS DAC for Multiplexed Spin-Qubit Biasing** — L. Enthoven, J. van Staveren, J. Gong, M. Babaie, F. Sebastiano, 2022, VLSI Technology and Circuits, 228–229 | [10.1109/VLSITechnologyandCir46769.2022.9830309](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830309) · [全文](https://pure.tudelft.nl/ws/portalfiles/portal/154843798/A_3V_15b_157W_Cryo_CMOS_DAC_for_Multiplexed_Spin_Qubit_Biasing.pdf) | 大负载与高压方案 |
| R05 F | **Cryo-CMOS Integrator-Based DAC for Scalable Biasing of Semiconductor Qubits** — L. Enthoven et al., 2026, IEEE TCSI, early access | [10.1109/TCSI.2026.3692714](https://doi.org/10.1109/TCSI.2026.3692714) · [全文](https://repository.tudelft.nl/file/File_3ad3cb9c-a2c0-44a8-8e7a-b4bafd65c4cf) | R04 扩展；不能重复计为独立芯片 |
| R06 F | **Cryo-CMOS Bias-Voltage Generation and Demultiplexing at mK Temperatures for Large-Scale Arrays of Quantum Devices** — J. van Staveren et al., 2025, IEEE TQE 6, 3101618 | [10.1109/TQE.2025.3580377](https://doi.org/10.1109/TQE.2025.3580377) · [全文](https://pure.tudelft.nl/ws/portalfiles/portal/249952283/Cryo-CMOS_Bias-Voltage_Generation_and_Demultiplexing_at_mK_Temperatures_for_Large-Scale_Arrays_of_Quantum_Devices.pdf) | 96 路 S&H 集成；系统/ESD/漂移 |
| R07 F(preprint) | **A cryogenic CMOS chip for generating control signals for multiple qubits** — S. J. Pauka et al., 2021, Nature Electronics 4, 64–70 | [10.1038/s41928-020-00528-y](https://doi.org/10.1038/s41928-020-00528-y) · [作者预印本](https://arxiv.org/abs/1912.01299) | 预印本题名 *A Cryogenic Interface for Controlling Many Qubits*；本轮数字以该版本定位 |
| R08 H | **Spin-qubit control with a milli-kelvin CMOS chip** — S. K. Bartee et al., 2025, Nature 643, 382–387 | [10.1038/s41586-025-09157-x / 全文](https://www.nature.com/articles/s41586-025-09157-x) | R07 研究线的真实 qubit 操作后续 |
| R09 F | **An 11-bit 0.008 mm² charge-redistribution digital-to-analog converter operating at cryogenic temperature for large-scale qubit arrays** — T. Miki, R. Takahashi, M. Nagata, 2022, IEICE Electronics Express 19(8), 20220099 | [10.1587/elex.19.20220099](https://doi.org/10.1587/elex.19.20220099) · [全文](https://da.lib.kobe-u.ac.jp/da/kernel/90009517/90009517.pdf) | MOM / split-CDAC / calibration |
| R10 F | **Characterization and Analysis of On-Chip Microwave Passive Components at Cryogenic Temperatures** — B. Patra et al., 2020, IEEE JEDS 8, 448–456 | [10.1109/JEDS.2020.2986722](https://doi.org/10.1109/JEDS.2020.2986722) · [全文](https://repository.tudelft.nl/file/File_6d4cc63f-f0aa-4ad1-8d39-9942b3c07726) | 40 nm MOM 低温实测，非65 nm matching 数据 |
| R11 F | **Characterization and Modeling of Mismatch in Cryo-CMOS** — P. A. ’t Hart, M. Babaie, E. Charbon, A. Vladimirescu, F. Sebastiano, 2020, IEEE JEDS 8, 263–273 | [10.1109/JEDS.2020.2976546](https://doi.org/10.1109/JEDS.2020.2976546) · [全文](https://pure.tudelft.nl/ws/portalfiles/portal/71537207/09015956.pdf) | MOS mismatch / model validity |
| R12 F | **Cryogenic CMOS Analog Circuits and Chip Packaging Techniques towards Large-Scale Silicon Quantum Computers** — T. Miki, M. Taguchi, M. Nagata, 2025, IEICE Trans. Electronics E108-C(10), 499–507 | [10.1587/transele.2024CTI0001 / 全文](https://globals.ieice.org/en_transactions/electronics/10.1587/transele.2024CTI0001/_f) | 综述；R09 研究线与封装 |
| R13 F | **On-chip integration of Si/SiGe-based quantum dots and switched-capacitor circuits** — Y. Xu et al., 2020, Applied Physics Letters 117, 144002 | [10.1063/5.0012883](https://doi.org/10.1063/5.0012883) · [全文](https://repository.tudelft.nl/file/File_c08f6c33-0bee-49bd-ba90-a25ceb7d0183) | 保持/注入/电容尺寸及单片QD |
| R14 A/S | **CMOS-based cryogenic control of silicon quantum circuits** — X. Xue, B. Patra, J. P. G. van Dijk et al., 2021, Nature 593, 205–210 | [10.1038/s41586-021-03469-4](https://doi.org/10.1038/s41586-021-03469-4) · [开放版本](https://repository.tudelft.nl/file/File_43b3c29b-b2d8-45fb-be5e-32846230d631) | 微波控制路径；不把其要求移植到 DC DAC |
| R15 F(author manuscript) | **Cryogenic Current Steering DAC With Mitigated Variability** — M. E. P. V. Zurita et al., 2020, IEEE SSC-L 3, 254–257 | [10.1109/LSSC.2020.3013443](https://doi.org/10.1109/LSSC.2020.3013443) · [IEEE摘要](https://ieeexplore.ieee.org/document/9153813/) | 全文核实 8 bit、6.6 mV、7.3 µW static；RT 350 ns/35.2 pF 实测，100 MS/s 为估算，未测 cryo dynamics |
| R16 A/S | **Characterization and Compact Modeling of Nanometer CMOS Transistors at Deep-Cryogenic Temperatures** — R. M. Incandela et al., 2018, IEEE JEDS 6, 996–1006 | [10.1109/JEDS.2018.2821763](https://doi.org/10.1109/JEDS.2018.2821763) · [机构记录/全文入口](https://research.tudelft.nl/en/publications/characterization-and-compact-modeling-of-nanometer-cmos-transisto/) | 0.16 µm/40 nm 模型校验；非我们的65 nm model |
| R17 S | **Characterization and Modeling of 28-nm Bulk CMOS Technology Down to 4.2 K** — A. Beckers, F. Jazaeri, C. Enz, 2018, IEEE JEDS 6, 1007–1018 | [10.1109/JEDS.2018.2817458](https://doi.org/10.1109/JEDS.2018.2817458) · [作者稿](https://infoscience.epfl.ch/bitstreams/62c1691b-7714-4202-a7e4-0abfa0224549/download) | 器件物理与 compact model 背景，未逐项提取参数 |
| R18 F | **Cryo-CMOS Voltage References for the Ultrawide Temperature Range From 300 K Down to 4.2 K** — J. van Staveren et al., 2024, IEEE JSSC 59(9), 2884–2894 | [10.1109/JSSC.2024.3378768](https://doi.org/10.1109/JSSC.2024.3378768) · [全文](https://pure.tudelft.nl/ws/portalfiles/portal/230892395/Cryo-CMOS_Voltage_References_for_the_Ultrawide_Temperature_Range_From_300_K_Down_to_4.2_K.pdf) | reference / weak inversion / 校准边界 |
| R19 H | **A quantum dot crossbar with sublinear scaling of interconnects at cryogenic temperature** — P. L. Bavdaz et al., 2022, npj Quantum Information 8, 86 | [10.1038/s41534-022-00597-1 / 全文](https://www.nature.com/articles/s41534-022-00597-1) | 测到平均 pinch-off 1.17 V；0–1 V 范围非通用 |
| R20 H | **Scalable on-chip multiplexing of silicon single and double quantum dots** — H. Bohuslavskyi et al., 2024, Communications Physics 7, 323 | [10.1038/s42005-024-01806-3 / 全文](https://www.nature.com/articles/s42005-024-01806-3) | 64 路 MUX、custom SOI；device screening 不等于集成DAC |
| R21 A | **Multiplexed cryo-CMOS control of an isolated double quantum dot** — M. Darnas et al., 2026, arXiv preprint | [10.48550/arXiv.2604.11266 / 摘要及全文入口](https://arxiv.org/abs/2604.11266) | 摘要：0.5 K DQD、sequential refresh 与 pulsing；未取全文数值作规格 |
| R22 A | **Memristor-based cryogenic programmable DC sources for scalable in-situ quantum-dot control** — P.-A. Mouny et al., 2022 preprint / related 2023 IEEE TED paper | [arXiv:2203.07107](https://arxiv.org/abs/2203.07107) · [10.1109/TED.2023.3244133](https://doi.org/10.1109/TED.2023.3244133) | 元件4.2 K实测 + DC source 仿真，非完整source实测 |
| R23 A | **Towards scalable cryogenic quantum dot biasing using memristor-based DC sources** — P.-A. Mouny et al., 2024, arXiv preprint | [10.48550/arXiv.2404.10694](https://arxiv.org/abs/2404.10694) | 摘要1.2 K离散原型；集成65 nm的10 µW是模拟，不推荐本周改架构 |
| R24 B | **Xiling: Cryo-CMOS 18-bit Dual-DAC Manipulator with 4.6μV Precision and 4.1nV/Hz^0.5 Noise Co-Integrated with the Single Electron Transistor at 60mK** — Y. Li, Y. Zhang, H. Lin, C. Wang, 2025, ISSCC 13.4, 242–244 | [10.1109/ISSCC49661.2025.10904579](https://doi.org/10.1109/ISSCC49661.2025.10904579) · [作者机构介绍](https://news.uestc.edu.cn/info/1005/38495.htm) | 会议记录；期刊扩展 R24J 已全文阅读，非独立设计 |

R24 期刊扩展（同一工作，不重复计数）：**Xiling: Cryo-CMOS Manipulator Using Dual 18-bit R-2R DACs for Single-Electron Transistor at 60 mK**, Y. Li et al., IEEE JSSC, 2026，[10.1109/JSSC.2026.3671795](https://doi.org/10.1109/JSSC.2026.3671795)。用户已提供期刊全文，标记 R24J F：JSSC 61(8), 4193–4205。4 K 校准后 INL/DNL ±0.8 LSB；60 mK 噪声 3.8 µVrms（1 Hz–50 kHz）；DC 功耗约 60 µW 为双 DAC 芯片。详细条件见 specs revision 2。

## 补充全文阅读状态

此前请求的 R03、R15 和 R24 期刊扩展均已收到并阅读全文；PDF 保留于 `specs/papers/`。不再需要下载这三篇。R15 文件名为 `ESSCIRC_DAC_paper-revised.pdf`，实际内容是所请求 SSC-L 论文的作者稿。

- R03：20 µW DAC、40 µW total IC；13 min clock-off 测得 0.96 µV/s；3.8941 kHz refresh 下 275 µVpp ripple。44 mK 是 mixing chamber，holder 180 mK，electron 约 400 mK。64.5 pW/ch 为扩展外推。
- R15：4.2 K static power 7.3 µW，DNLmax 0.64 LSB，|INL|max 2.96 LSB；300 K 对应 0.11/0.63 LSB。100 MS/s 是由 RT 350 ns、35.2 pF 测试外推，不能当 cryogenic 动态实测。
- R24J：4 K 未校准 DNL +5/-10 LSB、INL +25/-45 LSB；OEM+RNC 后均 ±0.8 LSB。沿用 4 K 校准到 10 K 后 DNL +6/-2、INL +5/-8 LSB。噪声为 zero-code，4 K 值去除了 refrigerator ground noise；不能移作非零码含 reference-noise 的保证。

从 Week 7 起，以 `specs/bias_dac_specification_draft_v0_2026-10-04.md` revision 2 的工作指标推进设计。本文早期讨论建议服从该更新及后续 mentor 决定。
