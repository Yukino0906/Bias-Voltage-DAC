# Phase 2 — Cryogenic Bias Voltage DAC: Architecture Research Note

Date: 2026-09-12
Scope: research / architecture study, no transistor-level implementation.
Companion script: [model/arch_compare_v2.py](../model/arch_compare_v2.py) (Monte Carlo, binary vs thermometer vs segmented).

## 来源标注规则

本文每个结论都带一个 tag，避免把 paper 结论、外部文献和我们自己的推断混在一起：

| Tag | 含义 |
|---|---|
| **[Paper]** | 来自 reference paper：P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE SSC-L, vol. 3, 2020，后面注明 Section / Fig. / Table |
| **[Paper-read]** | 从 paper 的 figure 上读出的数值，精度受图像分辨率限制 |
| **[Ext]** | 外部文献（文末 References） |
| **[Sim]** | 本周 `model/arch_compare_v2.py` 的 Monte Carlo 结果 |
| **[Inference]** | 我们基于以上材料做的推导 / 解释，paper 没有明说 |
| **[Hypothesis]** | 可能的 design direction，尚未被文献或 simulation 支持 |

---

## 0. Executive Summary

1. **Cryogenic 下 conventional DAC 退化的核心原因**是 transistor 参数（VTH、subthreshold slope、mismatch、bias point）大幅偏离 PDK 预期，而 capacitor 几乎不变。因此 **越少依赖 transistor analog 参数、越多依赖 capacitor ratio 的 architecture 越 cryogenic-friendly**。这是 charge-redistribution 相对 resistor-string / current-steering 的根本优势 [Ext] + [Inference]。
2. **Reference paper 的 DAC = 10-bit BWA capacitive DAC + 3-bit coarse reference selection（8 external references）+ 8 路 DEMUX S&H，无 output buffer，靠 periodic refresh 对抗 leakage** [Paper, Sec. III, Fig. 2, Fig. 3]。总功耗 2.63 µW/channel，其中 99.5% 是 digital [Paper, Table II]。
3. **Binary vs Thermometer**：在相同 unit-capacitor mismatch 下，thermometer 只改善 DNL 与 monotonicity，**不改善 INL** [Sim]。Full thermometer 在 10 bit 需要 1023 个 elements，不可接受；**segmented（3–4 bit thermometer MSB + binary LSB）用 14–21 个 elements 把 worst-case DNL 降低 25–40%** [Sim]。Decoder 本身的 digital 增量很小，真正的代价在 switch driver、routing 和 per-element latch [Inference]。
4. **Fig. 9 的 jump 不是 global gain error**。它是 "region 内 gain = 1 − α（α ≈ 6–7%，来自 top-plate parasitic C_p）+ 每个 region 起点被 reset 钉在 nominal VL" 的组合，导致 region 边界出现 ≈ 8 mV（≈ 65 LSB）的 missing range [Paper, Fig. 9(a)] + [Paper-read] + [Inference]。Paper 用 250-mV 的 intermediate span（VU=625 mV, VL=375 mV）以 2× step size 填补 gap [Paper, Sec. IV-C, Fig. 9(b)]。这本质上是 **region-dependent digital remapping**。
5. **Preliminary recommendation**：延续 charge-redistribution + coarse reference + S&H + refresh 的框架；重新评估 attenuation capacitor（Eq. (1) 显示 BWA 的 mismatch sensitivity 比 plain binary 高 2^(N/4) ≈ 5.7×）；fine DAC 采用 segmented coding；把 Fig. 9 的 remap 提升为 design-time 的 region overlap + 2-point per-region calibration。以上为 [Hypothesis]，需 V2 behavioral model 验证。

---

## 1. Cryogenic CMOS Bottlenecks

### 1.1 Effect chain 总表

每一行按 Effect → device consequence → circuit consequence → DAC consequence → mitigation 展开。温度目标：paper 测量在 6 K，应用目标 100 mK [Paper, Sec. II, Sec. IV]。

| # | Effect（什么变了） | Why（物理原因） | Device consequence | Circuit consequence | DAC consequence | Mitigation | Source |
|---|---|---|---|---|---|---|---|
| 1 | **VTH 上升**，bulk 40/65 nm 典型 +0.1 ~ +0.2 V @ 4 K | Fermi level 随温度移向 band edge，intrinsic carrier 密度骤降；dopant incomplete ionization | 相同 VGS 下 overdrive 减少；|VGS| 接近 VDD/2 的 TG 中 nMOS/pMOS 都可能进入 weak inversion | Switch Ron 在 mid-rail 附近升高甚至断开；stacked 结构 headroom 不足；room-temperature 设计的 bias 点漂移 | Cap-array bottom-plate switch 与 S&H switch settling 变慢；buffer 输入 CM range 缩小 [Paper Fig. 6]；需要更高 VDD | 提高 VDD（paper OpAmp 用 1.7 V [Paper Sec. IV-A]）；bootstrapped / boosted switch；选低 VT 器件；forward body bias；减少 stacking | [Ext: Incandela 2018] |
| 2 | **Mobility 上升**（low-field 约 1.5–2×，short-channel 因 velocity saturation / series R 受限） | Phonon scattering 减弱 | 同 overdrive 下 gm、ID 上升，Ron 下降，部分抵消 #1 | Loop gain、bandwidth 变化；output 更接近 rail（paper：0 V input 时 output 从 54 mV 降到 33 mV [Paper Sec. IV-A]） | 总体有利；但 stability / settling margin 需重新验证 | 用 cryo model 重新做 AC / transient | [Paper Sec. IV-A] + [Ext: Incandela 2018] |
| 3 | **Subthreshold slope 变陡**：理论 kT/q·ln10 → 0.8 mV/dec @ 4 K，实测饱和在 ~10–20 mV/dec | Band-tail / interface states 限制 | Weak inversion 区间极窄，器件从 off 到 strong inversion 几乎是阶跃 | Moderate / weak inversion 偏置不可用；diff pair 输入 CM 超过 VTH 时突然失效 | Paper 的 pMOS input pair 在 input > 700 mV 时 clipping [Paper Sec. IV-A, Fig. 6]；ΣΔ comparator CMFB 要从 700 mV 降到 500 mV [Paper Sec. IV-B] | 所有 analog transistor 保持 strong inversion；rail-to-rail input 或干脆去掉 opamp（paper 的 DAC 主路径无 buffer） | [Paper] + [Ext: Incandela 2018] |
| 4 | **Subthreshold / junction leakage 大幅下降**；gate tunneling leakage 基本不随温度变 | Leakage 由 exp(−qVth/nkT) 主导 → 指数下降；tunneling 与 T 无关 | Off-switch leakage 降到 fA 量级或以下 | S&H hold 时间显著变长 | Refresh rate 可以降低 → digital power 下降；paper 在 3.9 kHz 找到 sweet spot [Paper Sec. IV-C, Fig. 8(e)(f)] | 设计 refresh rate 可编程；但仍要保留 refresh（gate leakage、辐射、charge trapping 不随 T 消失） | [Paper] + [Inference] |
| 5 | **Dopant freeze-out / kink / impact ionization** | Substrate dopant 在 <40 K 不完全电离；drain 高场下 impact ionization 电流增大 | 高 VDS 时 ID–VDS 出现 kink、hysteresis；substrate 电流增大 | 高 VDS 的 output stage、current source 行为异常 | 对 switch + cap 结构影响小（VDS ≈ 0）；对 buffer / mirror 影响大 | 限制 VDS；充分 body tie；避免高 VDS analog 器件 | [Ext: Incandela 2018] |
| 6 | **Transistor mismatch 上升**：σ(ΔVTH) 约 2×；subthreshold mismatch 反常增大 | Pelgrom 定律仍成立但 A_VT 增大；freeze-out 相关的随机性 | 相同面积下 diff pair offset、mirror mismatch 变差 | Current mirror 精度、comparator offset 下降 | Current-steering DAC 的 unit current mismatch 变差；opamp offset 变化（paper 观察 2 mV shift [Paper Sec. IV-A]） | 用 passive（capacitor）matching 决定精度；transistor 只做 switch | [Ext: Hart 2020 TU Delft; Dierickx 2014] |
| 7 | **Capacitor 稳定** | MOM / MIM 几何决定，介电常数弱温度依赖 | C 值变化在百分之几量级，ratio 变化更小 | Cap ratio DAC 的 transfer 基本不随 T 变 | Charge-redistribution 的核心优势 | — | [Paper Sec. III 引用 [5]] + [Ext: Patra 2020] |
| 8 | **Resistor 变化依类型**：poly resistor TCR 小；diffusion / n-well resistor 受 freeze-out 影响大 | 载流子浓度和 mobility 的温度依赖 | 绝对值可能变化数十 %；ratio 变化取决于 TCR mismatch | Resistor-string 的 ratio 精度尚可，但 tap 处 MOS switch 是弱点 | Resistor-string 不是因 R 本身失效，而是 switch + static current | 如用 R，只用 poly；R 值必须极大以压低 static power | [Ext: 一般 cryo-CMOS 综述] + [Inference] |
| 9 | **On-chip reference 失效**：bandgap 依赖 BJT VBE，4 K 下 BJT 冻结 | BJT 少子注入需要热激发 | 传统 bandgap 输出不再线性 | 需要 cryo-specific reference（DTMOS 等） | Paper 完全用 **external reference voltages**（Fig. 3(b)），芯片上无 reference | 短期：external reference；长期：cryo voltage reference 是独立课题 | [Paper Fig. 3(b)] + [Ext: Homulle 2018] |
| 10 | **PDK / compact model 无效** | Foundry model 只到 −40 °C；VTH、SS、mobility、freeze-out 均超出拟合范围 | Simulation 在 4 K 定量不可信 | 无法直接做 PVT corner | 设计余量无法量化 | 用 cryo model（MOS11/PSP、EKV 拓展 [Ext: Incandela 2018; Beckers 2018]）；或用 "VTH +150 mV 且 −40 °C" 的人工 corner 做 robustness check [Hypothesis]；选对参数不敏感的 topology | [Ext] + [Hypothesis] |
| 11 | **Power budget 极严** | Dilution refrigerator 在 100 mK 的 cooling power 约 400 µW [Paper Sec. II] | — | 任何 static current 都要按 nW 计 | Paper: 总芯片 < 400 µW，DAC 2.63 µW/ch [Paper Table II, Sec. V] | 无 static power 的 topology；低 refresh rate；digital 用 advanced node | [Paper] |
| 12 | **Parasitic 随温度变化**：junction cap 随 depletion width 变；metal 电阻下降 5–10× | Freeze-out 改变 depletion；phonon scattering 减少 | Top-plate 的 junction 型 parasitic C_p 可能随 T 变 | RC delay 缩短（有利）；C_p 的变化改变 gain | Fig. 9 的 α 在 RT 和 cryo 可能不同 → remap 必须在 cryo 下标定 | Layout 上把 C_p 做成 metal 型（稳定）而非 junction 型；标定在 target 温度进行 | [Inference] |
| 13 | **Noise**：thermal / kT/C 噪声随 T 下降；flicker noise 不降甚至上升 | kT/C ∝ T；1/f 来自 trap，与 T 弱相关 | 1 pF 的 kT/C：300 K → 64 µV rms，6 K → 9 µV rms | S&H 采样噪声在 cryo 下不是瓶颈 | LSB = 122 µV 时 cryo 下 C_storage 可以更小 | 对 DC bias DAC，refresh ripple 而非 kT/C 是主要 "noise" | [Inference] + [Ext: LFN 40 nm arXiv 2405.17685] |
| 14 | **Self-heating** | mK 级 bath 下器件局部温度远高于 bath | 器件实际工作温度不确定 | 100 mK 与 6 K 行为差异未知 | Paper 只在 6 K 测量 [Paper Sec. IV]，100 mK 结果未给出 | 最小化 dissipation；接受 "device sees a few K" | [Paper] + [Inference] |

### 1.2 Reference paper 中实际观察到的 cryogenic behavior [Paper]

| 观察 | 位置 | 数值 | 解释（paper 给出的 / 我们的） |
|---|---|---|---|
| Unity-gain buffer clipping | Sec. IV-A, Fig. 6 | Cryo 1.2 V 时 input > ~0.7 V 输出跳到 rail；1.7 V 时正常 | Paper：pMOS input pair 的 input CM 超过 VTH，steep subthreshold slope 使 moderate / weak inversion 不可行。[Inference] 这是 #1 + #3 的叠加 |
| Supply 提高 | Sec. IV-A, IV-C | OpAmp / ΣΔ 用 1.7 V；DAC 核心 1.2 V（Table III: 1.2 & 2.5 V） | 只有含 opamp 的 auxiliary 路径需要提高 VDD；DAC 主路径不需要 |
| CMFB 调整 | Sec. IV-B | 700 mV → 500 mV | 同 #3 |
| Mobility-related | Sec. IV-A | Output 近 ground 从 54 mV → 33 mV | Paper：mobility 上升，同电流需要更小 VDS |
| Offset shift | Sec. IV-A, IV-B | OpAmp 约 2 mV；ΣΔ 约 5 mV | Paper：仍在 process mismatch 范围内；ΣΔ 的 offset 可数字减去 |
| Bandwidth | Sec. IV-A | 225 kHz → 250 kHz（100 pF cable load） | 与 #2 一致 |
| Power 不变 | Sec. IV-A | OpAmp 1.2 V: 140 → 120 µW；1.7 V: 240 → 270 µW | 因为 bias 电流是 external reference current |

**结论**：paper 中所有明显的 cryogenic failure 都发生在 **transistor-parameter-dependent 的 analog block**（opamp、comparator）；**capacitor + switch 的 DAC 核心没有报告任何 cryo-specific failure**。这是本项目 architecture 选择的最直接证据 [Inference from Paper]。

### 1.3 为什么 charge-redistribution 在 cryogenic 下可能优于 resistor-string / current-steering

| 角度 | Resistor-string | Current-steering | Charge-redistribution | Source |
|---|---|---|---|---|
| Static power | I = Vref / R_total 恒流。1 V / 1 MΩ = 1 µW；要做到 nW 级需 R_total ≈ 1 GΩ，面积和 settling 不可接受 | 需要 full-scale current 流入 load：1 V / 10 kΩ = 100 µA = 100 µW，远超 budget | 零 static power，只有 CV²f dynamic：paper core 77 nW [Paper Table II] | [Paper] + [Inference] |
| 对 transistor analog 参数的依赖 | 精度由 R ratio 决定；但 tap switch 的 Ron 和 leakage 进入误差 | 精度由 current-source transistor 的 VTH / β mismatch 决定 → cryo 下 mismatch 2× [Ext] | 精度由 C ratio 决定；transistor 只做 switch，只要求 "能开能关" | [Ext: Hart 2020] |
| Resistor / capacitor 在 cryo 的行为 | R 绝对值和 TCR 依类型变化，n-well / diffusion 型有 freeze-out 风险 | 不适用 | C 变化 ~ 几 %，ratio 更稳 [Paper Sec. III 引 [5]; Ext: Patra 2020] | |
| kT/C / thermal noise | R 的 thermal noise 与 bandwidth 有关 | 同上 | kT/C 与 bandwidth 无关，且随 T 线性下降 [Paper Sec. III] | |
| Matching 与 resolution | R matching 好，但 2^N 个 R + switch，10 bit = 1024 R | Unit current 数量同样 2^N（或 segmented） | Binary 只需 N 个 weight；BWA 进一步减少面积，代价是 mismatch sensitivity（见 §3.4） | |
| Headroom | Tap 电压覆盖 0–Vref，中间 tap 的 TG 在 VTH 上升后可能失效 | Cascode current source 需要 headroom，VTH 上升后恶化 | Top plate 电压范围 = VL ~ VU，每个 region 只有 125 mV；switch 只在 VL / VU 两个固定电平开关 | [Inference] |
| Scalability / multi-channel | 每 channel 一条 string 或复杂 mux | 每 channel 一组 current source | 一个 cap array 可时分给 8 channel [Paper Sec. III] | |
| 弱点 | Static power；switch 数量 | Static power；mismatch | 需要 refresh；leakage；parasitic-induced gain；top plate 是高阻节点 | |

**回答 mentor 的核心问题** [Inference]：Room-temperature DAC 在 cryo 下退化的根本原因是它把精度或 bias 建立在 transistor 的 analog 参数（VTH、gm、mirror matching、weak-inversion 行为）之上，而这些参数在 4 K 偏离 PDK 数十 % 且 mismatch 加倍。Charge-redistribution 把精度转移到 capacitor ratio 上，把 transistor 降级为 digital-like switch，并且没有 static power，因此对 cryogenic 最不敏感。它的代价（leakage / refresh / parasitic gain）在 cryo 下反而部分缓解（leakage 下降）。

---

## 2. Reference Paper Architecture Breakdown

### 2.1 Paper 明确给出的 quantitative values [Paper]

| 项目 | 数值 | 位置 |
|---|---|---|
| Technology | TSMC 65-nm CMOS | Abstract, Table III |
| Output range | 0 V – 1 V | Table I, Sec. II |
| Required step / resolution | 250 µV ≈ 12 bit（qubit 要求） | Table I |
| Designed step / resolution | ~125 µV，13 bit（含 margin） | Sec. II |
| Channel count | 8 | Sec. II, Table III |
| Fine DAC（cap array）resolution | 10 bit（"repeating pattern for each 10-bit word (1023 LSBs)"；"beyond about 10 bit ... without calibration"） | Sec. III, Sec. IV-C, Fig. 8(d) |
| Coarse tuning | 8 external reference voltages → +3 bit；VU / VL 独立选择，0 – 1 V 每 125 mV 一档（9 个 tap），选择线 6 bit | Sec. III, Fig. 3(b) |
| 电压跨度对 charging power 的影响 | 1 V → 0.125 V，P ∝ V²fC，功耗降 1/64 | Sec. III |
| Application temperature | 100 mK（qubit）；测量在 ~6 K（attoDRY800） | Table I, Sec. II, Sec. IV |
| Cooling budget | ~400 µW @ 100 mK；chip 总功耗需 ≪ 1 mW | Sec. II, Table I |
| Nominal refresh rate | f_R = 390 kHz | Sec. IV-C, Fig. 8(a)–(d) |
| Sweet-spot refresh rate | 3.9 kHz | Sec. IV-C, Fig. 8(e)(f) |
| Leakage 目标 | 电压变化保持在 "lower tens of microvolt"；DAC 驱动能力按 pA leakage 设计 | Sec. III, Sec. III-A |
| Measured DNL σ | σ_D = 0.495 LSB（direct, 3.9 kHz） | Sec. IV-C |
| 反推 capacitor mismatch | σ0 = 0.003 C0（用 Eq. (1)，N = 10） | Sec. IV-C |
| Eq. (1) | σ²_DNL,BWA = σ²_D ≈ 2^(3N/2) · (σ0/C0)² LSB² | Sec. III, 引 [6] |
| Power @ 3.9 kHz | Core (Sw & MUX) 77 nW；references 3 nW；digital (memory & logic) 21 µW；DAC total 21.1 µW = 2.63 µW/ch；clock buffer 4.3 µW；total 25.4 µW = 3.18 µW/ch | Table II |
| Digital 占比 | 99.5% | Sec. IV-C, Sec. V |
| Supply | 1.2 V & 2.5 V（DAC）；opamp / ΣΔ 测试时 1.7 V | Table III, Sec. IV-A |
| Area | DAC 0.135 mm²（die photo）/ 0.14 mm²（Table III） | Fig. 10, Table III |
| OpAmp | Open-loop gain 70 dB（RT 与 cryo 相同）；offset shift ~2 mV；UGBW 225 → 250 kHz | Sec. IV-A |
| 对比 | 其他 cryo DAC 均为 current-steering、BiCMOS、mW 级、单 channel | Table III |

Fig. 8 的 x 轴延伸到约 8600 codes，超过 2^13 = 8192 [Paper-read]。[Inference] 多出来的 codes 就是 Fig. 9(b) 的 intermediate steps（7 个 region boundary × 每个约 50–70 codes）。

### 2.2 Signal / control flow [Paper Fig. 2, Fig. 3] + [Inference 标注]

```
I2C interface (RT host → chip)                                   [Paper Fig. 1]
  └─> per-channel code memory (13 bit + coarse bits)             [Paper Sec. IV-C "digital memory circuitry per DAC"]
        └─> timing generator (shared, generates reset / S&H / DEMUX phases)   [Paper Sec. IV-C]
              │
              ├─> coarse reference selection: 6-bit MUX picks VU, VL from
              │   {0, 125, ..., 1000 mV} external references          [Paper Fig. 3(b)]
              │
              ├─> 10-bit BWA capacitor array (LSB sub-array | C_A | MSB sub-array)
              │   each bottom plate switch: bit=1 → VU, bit=0 → VL     [Paper Fig. 2] + [Inference on polarity]
              │   top plate: reset switch (to a reference), then floats
              │   → V_top = VL + (VU − VL) · C_on(D) / C_total,eff     [Inference, 见 §4.5]
              │
              ├─> DEMUX: 1 of 8 switch connects top plate to channel k   [Paper Fig. 2]
              │
              └─> S&H: series R + C_storage, then bond-wire → C_electrode → qubit gate  [Paper Fig. 2]
                     C_storage 每次被驱动时向 V_top 移动一个 discrete step  [Paper Sec. III]
                     leakage 使 V 缓慢下降 δV_C，T_R 后 refresh           [Paper Fig. 3(a)]
```

### 2.3 Design-decision Q&A

| 问题 | 回答 | Tag |
|---|---|---|
| Why charge-redistribution? | 无 static power；kT/C noise 与 bandwidth 无关；capacitor 在低温下变化小；方便 DEMUX 到多 channel | [Paper Sec. III] |
| How many effective bits? | 13 bit 设计（122 µV），满足 12 bit / 250 µV 要求 | [Paper Sec. II, Table I] |
| How many bits inside the cap array? | 10 bit | [Paper Sec. III, IV-C] |
| How are extra bits obtained? | VU − VL = 125 mV 的 8 个 region 覆盖 0–1 V → +3 bit | [Paper Sec. III, Fig. 3(b)] |
| Why multiple reference voltages? | (a) 3 bit 额外分辨率不增加 cap array；(b) charging swing 从 1 V 降到 125 mV，CV²f 降 1/64；(c) [Inference] mismatch 只在 10 bit 内累积，避开 Eq. (1) 中 2^(3N/2) 的指数增长 | [Paper Sec. III] + [Inference] |
| Why is S&H used? | 一个 DAC 时分给 8 channel，每 channel 用 C_storage 保持电压 | [Paper Sec. III] |
| Why can the output buffer be removed? | 不需要在一个 conversion 内把 C_storage 充满；允许多次 refresh 逐步逼近，省 power / area / noise | [Paper Sec. III] |
| Why is refresh necessary? | S&H 电容上的 leakage 和 disturbance 会使电压漂移 | [Paper Sec. III, Fig. 3(a)] |
| What determines refresh rate? | 上限：digital power ∝ f_R；下限：δV_C = I_leak · T_R / C_storage 必须 < 数十 µV；另外 code 更新后的 settling 时间 = (需要的 refresh 次数) × 8 × T_R [Inference]。Paper 的 sweet spot 3.9 kHz | [Paper Sec. IV-C] + [Inference] |
| What limits DAC resolution? | Capacitor mismatch，simulation 显示不加 calibration 约 10 bit | [Paper Sec. III] |
| What produces DNL? | (a) cap mismatch（Eq. (1)）；(b) coarse-region 边界 jump（Fig. 9）；(c) buffer 引入的额外 DNL（direct vs via buffer 差异 [Paper Sec. IV-C, Fig. 8(b) vs (d)]）；(d) 390 kHz 时每 1023 LSB 出现周期性 pattern（Fig. 8(d)），3.9 kHz 时消失 — paper 未解释原因，[Hypothesis] 与高 refresh rate 下 top plate / C_storage 的 settling 或 measurement integration 有关 | [Paper] + [Hypothesis] |
| What causes the coarse-region jump? | Parasitic capacitance 引起的 gain error | [Paper Sec. IV-C]，机制展开见 §4.5 |
| How do intermediate steps fix it? | 不直接跳到下一个 125 mV 档，先用 250 mV 档（VU=625, VL=375）以 2× step 走过 missing range | [Paper Sec. IV-C, Fig. 9(b)] |
| What dominates total power? | Digital memory & logic 21 µW / 21.1 µW = 99.5%；core 77 nW | [Paper Table II] |
| What is shared vs duplicated? | Shared：cap array + switches、reference MUX、timing generator（甚至可跨多个 DAC 共享）、clock buffer。Per channel：DEMUX switch、series R、C_storage、bond wire、code memory。Per DAC："some digital memory circuitry" | [Paper Sec. IV-C] + [Inference] |

### 2.4 Analog vs digital bottleneck 划分 [Inference]

| Block | 类型 | 限制什么 | Paper 是否已解决 |
|---|---|---|---|
| Cap array mismatch | Analog | Fine DAC resolution ≤ 10 bit | 用 coarse reference 绕开，未 calibrate |
| Top-plate parasitic C_p | Analog / layout | Region 内 gain 1 − α，边界 jump | 用 intermediate steps 绕开（digital remap） |
| S&H leakage | Analog | 决定 refresh rate 下限 | Refresh；cryo 下 leakage 变小 |
| Reference voltages | System | 8 根外部线，绝对精度和 IR drop 决定 region 起点 | 外部提供，未讨论精度 |
| Memory & timing logic | Digital | 99.5% power | 指出随 node scaling 改善，未优化 |
| Clock buffer | Digital | 4.3 µW（17% of total） | 未讨论 |
| Measurement / calibration | Aux | 需要 on-chip ΣΔ + WC 才能在 cryo 下观察 DAC | 提供了工具，但未用于 calibration |

### 2.5 值得复用 / 值得改进 [Inference / Hypothesis]

**复用**：charge-redistribution 核心；coarse reference 分区（既加 bit 又降 power）；S&H + DEMUX 多路共享；无 output buffer；可编程 refresh rate；on-chip ΣΔ 作为 in-situ 测量手段。

**可改进**：
1. Attenuation capacitor（BWA）带来 2^(N/4) 的额外 mismatch sensitivity（§3.4）；plain binary 或 segmented 的面积在 65 nm 完全可接受 [Hypothesis]。
2. Fig. 9 的 remap 应在设计阶段做成 region overlap + 每 region 的 2-point correction，而不是事后 workaround（§4.5）。
3. Digital 占 99.5%：memory / timing 是主战场，任何 coding 方案的比较都要以 "不显著增加 memory 和 timing logic" 为前提（§3.6）。
4. 8 根 external reference 线在 100 mK stage 的 wiring 和 heat load 是 system-level 成本，paper 没有量化 [Open question]。

---

## 3. Binary vs Thermometer vs Segmented

### 3.1 Binary-weighted implementation

- **Element count**：N 个 weight（10 bit → 10 个），第 k 个 weight = 2^k 个 unit。
- **Decoder**：无，code bit 直接驱动 switch。
- **Major carry transition 0111…1 → 1000…0**：MSB element（2^(N−1) units）打开，同时其余 2^(N−1) − 1 units 全部关闭。理想 step = 1 unit，但它是两个大数之差。若每个 unit 独立 mismatch σ_u，则 step 误差 σ ≈ σ_u · √(2^(N−1) + 2^(N−1) − 1) ≈ σ_u · 2^(N/2) LSB。10 bit、σ_u = 0.3% 时 ≈ 0.096 LSB；σ_u = 2% 时 ≈ 0.64 LSB，开始出现 non-monotonic 风险 [Inference, 与 Sim 一致]。
- **Glitch**：MSB on 与 LSBs off 若不同步，瞬态输出会短暂等于 0 或 full-scale。对本项目（DC bias、S&H 在 settle 后才连接）**glitch 不进入输出**，只要 timing 上先让 array settle 再闭合 DEMUX / S&H switch [Inference]。这与高速 DAC 的 glitch-energy 问题本质不同。
- **Monotonicity**：不保证，取决于 MSB 与低位之和的 mismatch。
- **Layout**：大 weight 由 unit 并联组成，需要 common-centroid；MSB 的 routing 长。
- **Power**：switch driver 数 = N；但 MSB switch 尺寸 ∝ 2^(N−1)，总 gate capacitance 与 thermometer 相当。

### 3.2 Thermometer / unary implementation

- **Element count**：2^m − 1 个 unit（10 bit → 1023）。
- **Decoder**：binary → thermometer 需要约 (2^m − 1) 个输出、每个 m − 1 级 gate；10 bit 约 9000 gate-equivalent [Sim 估计]。
- **DNL**：每步只切换一个 unit，σ_DNL ≈ σ_u（相对 LSB）。
- **Monotonicity**：只要 unit 为正就保证。
- **INL**：unit 误差随 code 累积成 random walk，σ_INL,max ≈ σ_u · 2^(m/2) / 2，**与 binary 相同**（binary 的 weight 也由同样的 unit 构成）[Sim 验证]。
- **Switching behavior**：相邻 code 只切换 1 个 unit。但在 charge-redistribution 的 reset-then-set 流程里，每次 conversion 所有 ON 元件都要重新驱动，activity 取决于 ON 元件数而非 Hamming distance [Inference]。
- **Routing / area**：1023 条控制线 + 1023 个 latch + 1023 个 switch driver；对 65 nm 仍是数量级的差异。
- **Digital power**：decoder 逻辑 + 1023 个 driver 的 CV²f + 1023 个 latch 的 leakage / clock。

随 resolution 增长，element 和控制线按 2^m 增长，而 binary 按 m 增长，这是 full thermometer 在 ≥ 6 bit 后迅速昂贵的原因。

### 3.3 Segmented：thermometer MSB + binary LSB

M 位 thermometer MSB（2^M − 1 个 element，每个 2^(N−M) units）+ (N − M) 位 binary LSB。Major carry 发生在 LSB sub-array 与 **一个** MSB unit 之间，误差 σ ≈ σ_u · 2^((N−M)/2)·√2，比 full binary 降低 2^(M/2)。

### 3.4 Simulation 结果 [Sim]

Model（见 script docstring）：每个 unit cap 独立 N(0, σ_u)，weight 2^k 由 2^k 个 unit 组成，Vout = Vref · C_on / C_total（plain binary，无 attenuation cap，无 parasitic），2000 次 Monte Carlo，N = 10，σ_u = 0.003（取 paper 反推的 σ0/C0）。

| Scheme | Elements | Decoder gates（估） | σ_DNL | max\|DNL\| mean / 99% | max\|INL\| mean / 99% | P(non-mono) | Toggles per +1 step mean / max | Charge moved per +1 step mean / max (units) |
|---|---|---|---|---|---|---|---|---|
| Binary 10 b | 10 | 0 | 0.009 | 0.099 / 0.242 | 0.078 / 0.153 | 0 | 1.99 / 10 | 9.0 / 1023 |
| Seg 2T + 8B | 11 | 3 | 0.009 | 0.090 / 0.191 | 0.087 / 0.164 | 0 | 1.99 / 9 | 8.5 / 511 |
| Seg 3T + 7B | 14 | 14 | 0.008 | 0.076 / 0.156 | 0.088 / 0.161 | 0 | 1.99 / 8 | 7.8 / 255 |
| Seg 4T + 6B | 21 | 45 | 0.008 | 0.062 / 0.114 | 0.087 / 0.156 | 0 | 1.98 / 7 | 6.9 / 127 |
| Seg 5T + 5B | 36 | 124 | 0.007 | 0.049 / 0.083 | 0.086 / 0.156 | 0 | 1.96 / 6 | 5.9 / 63 |
| Thermometer 10 b | 1023 | 9207 | 0.003 | 0.010 / 0.013 | 0.082 / 0.154 | 0 | 1.00 / 1 | 1.0 / 1 |

σ_u sweep（max|DNL| mean / P(non-mono)）：

| σ_u | Binary | 4T + 6B | Thermometer |
|---|---|---|---|
| 0.003 | 0.100 / 0 | 0.062 / 0 | 0.010 / 0 |
| 0.010 | 0.333 / 0 | 0.208 / 0 | 0.035 / 0 |
| 0.020 | 0.666 / 0.062 | 0.415 / 0 | 0.069 / 0 |
| 0.030 | 0.999 / 0.224 | 0.623 / 0.024 | 0.104 / 0 |

**读数**：
1. INL 在所有方案下几乎相同（0.08–0.09 LSB）：coding 不改变 INL，只改变 DNL 和 monotonicity。
2. 4T + 6B 用 21 个 element、45 个 gate 把 worst-case DNL 降低约 40%，并把 non-monotonic 风险推到 σ_u ≈ 3% 才出现。
3. **与 paper 的 σ_D = 0.495 LSB 的差异**：我们的 plain-binary 模型在 σ_u = 0.003 时 σ_DNL,max ≈ 0.1 LSB，而 paper 的 BWA Eq. (1) 给出 2^(3N/4) · σ0/C0 = 181 × 0.003 = 0.54 LSB。两者相差 2^(N/4) ≈ 5.7×。[Inference] 这就是 attenuation capacitor 的代价：LSB sub-array 的误差经 C_A 传递到输出时没有 √面积 的平均效应，C_A 本身的 mismatch 也直接进入 sub-array 之间的 gain。paper 用 BWA 是为了减少总电容（约 2 × 32 + 1 units 而非 1024 units）。
4. **面积 / power 反算** [Inference]：plain 10-bit binary 用 1024 个 unit；65 nm MOM unit 取 5 fF → C_total ≈ 5 pF，面积约 0.003–0.005 mm²（DAC 总面积 0.135 mm² 的 3%）；charging power = C V² f = 5 pF × (0.125 V)² × 3.9 kHz × 8 ch ≈ 2.4 nW，远小于 77 nW 的 core。因此 **去掉 attenuation cap 在面积和功耗上都是可承受的**，收益是 DNL sensitivity 降低约 5.7× [Hypothesis，需在 V2 model 中加入 BWA 模型对比]。

### 3.5 Metric comparison table

| Metric | Binary | Thermometer | Segmented (3–4T + rest B) | Source |
|---|---|---|---|---|
| Elements (10 bit) | 10 | 1023 | 14–21 | [Sim] |
| Unit-cap area | 同 | 同 | 同 | 相同 total units |
| Decoder complexity | 0 | ~9k gates | 14–45 gates | [Sim 估] |
| Switch drivers / latches / routing lines | 10 | 1023 | 14–21 | |
| Digital power 增量 | 0 | 大（driver + latch + decoder，每次 conversion 全部翻转） | 很小 | [Inference] |
| Switching activity (charge moved at worst step) | 1023 units | 1 unit | 127–255 units | [Sim] |
| Glitch | Worst，但对 S&H DC output 不构成误差（timing 隔离） | 最好 | 中 | [Inference] |
| DNL (σ_u = 0.3%) max mean | 0.10 | 0.01 | 0.06–0.08 | [Sim] |
| INL | 0.08 | 0.08 | 0.09 | [Sim] |
| Monotonicity | 不保证 | 保证 | MSB 段保证，LSB 段 2^(N−M)/2 sensitivity | [Sim] |
| Mismatch sensitivity (DNL) | 2^(N/2)·σ_u | σ_u | 2^((N−M)/2)·σ_u | [Inference] |
| Layout matching difficulty | MSB 大元件 common-centroid | 1023 unit 阵列 + 控制线穿越 | 中 | |
| Scalability with N | 好 | 差（2^N） | 好（固定 M） | |
| Cryogenic suitability | 好：最少 digital | 差：digital 主导功耗时最不利 | 好：digital 增量可忽略，DNL 改善明显 | [Inference] |

### 3.6 Does improved analog linearity justify the extra digital power at cryogenic temperature?

[Inference] 需要拆开看 paper 的 21 µW digital：它是 **memory + timing logic**，与 coding 无关。以 3.9 kHz refresh、8 channel 计算，一次 conversion 的 switch-control 翻转在 nW 量级；即使 full thermometer 的 1023 个 driver 每次全翻，driver 本身的 CV²f 也只是 core 77 nW 的量级。真正随 element 数线性增长的是 **每个 element 的 latch / level shifter 的 leakage 与 clock load、以及 routing 面积**。所以：

- Full thermometer：不合理，1023 个 latch + routing 的静态和 clock 成本在 cryo power budget 下不可接受，且 INL 没有改善。
- Segmented 3–4 bit：decoder 45 gate、element 21 个，对 21 µW 是 < 0.1% 量级的增量；换来 DNL 降低 25–40% 和 MSB 段 guaranteed monotonicity。**值得**。
- 但如果最终采用 per-region 2-point calibration + 足够大的 unit cap，plain binary 也可能满足 13 bit；segmentation 的必要性要在 V2 model 中用真实 σ_u（来自 PDK 的 MOM mismatch 数据）判断 [Open question]。

---

## 4. Gain / Offset / Nonlinearity Compensation

### 4.1 统一 error model

V_actual(D) = a · V_ideal(D) + b + ε(D)，V_ideal(D) = D · LSB

| 项 | 名称 | 物理含义 | 在 v1 model 中的表现 |
|---|---|---|---|
| b | offset | code-independent 偏移 | 由 `OFFSET_ERROR_V` 加入；endpoint-fit INL 完全看不到；DNL 看不到 |
| a | gain factor | 斜率误差 | 由 `GAIN_ERROR_PCT` 加入；endpoint-fit INL 看不到；DNL 用 nominal LSB 时表现为常数 (a − 1) |
| ε(D) | code-dependent nonlinearity | mismatch、parasitic、settling 等 | 由 per-code Gaussian 加入，但真实 ε(D) 在 code 间强相关（见 §3） |

**定义规则**（建议 V2 采用）：
- 先用 endpoint（或 least-squares）拟合得到 (a, b)，再定义 ε(D) = V_actual − a·V_ideal − b。
- DNL 用 **实际 average LSB = a · LSB_nominal** 归一化，否则 gain error 会伪装成 DNL。
- 同时报告 raw error（含 a, b）与 fit 后的 INL / DNL，避免 v1 中 "offset 存在但 INL 为零" 的混淆。

### 4.2 Offset

| 来源 | 机制 | 对本架构的相关性 | Tag |
|---|---|---|---|
| Output / buffer input offset | Opamp diff pair mismatch | Paper 的 qubit 路径无 buffer，只有测量路径有（2 mV，cryo 下再 shift） | [Paper Sec. IV-A] |
| Reset switch charge injection / clock feedthrough | Top plate 的 reset switch 关断时注入 ΔQ → ΔV = ΔQ / C_total；若与 code 无关则为 offset，若与 top-plate 电压相关则进入 ε(D) | 直接相关；C_total 越大越小 | [Inference] |
| DEMUX / S&H switch injection | 同上，注入到 C_storage | 直接相关；C_storage 大则小 | [Inference] |
| Reference offset | VL 的绝对误差 → 该 region 的起点偏移；每个 region 不同 → 这是 **region-dependent offset**，不是全局 b | 直接相关（8 根 external 线的 IR drop、cabling） | [Inference] |
| Temperature-induced shift | VTH 变化改变 injection 电荷；opamp offset 变化 | 需在 cryo 下标定 | [Paper Sec. IV-A] + [Inference] |

**One-point calibration**：b = V_meas(0)，V_corr = V_meas − b。数字实现：D' = D − round(b / LSB)。代价：range 两端各损失 |b| / LSB 个 code；需要 cryo 下的测量手段（paper 的 ΣΔ + WC 就是这个用途）。**对本架构，one-point 应按 region 做（8 个 b_k）**，因为 offset 主要来自 VL_k [Inference]。

### 4.3 Gain

| 来源 | 机制 | 相关性 | Tag |
|---|---|---|---|
| Reference error | (VU − VL) 与 nominal 125 mV 的偏差 → 该 region 的 a_k | 直接相关，且 per region | [Inference] |
| Parasitic capacitance | Top plate 对地 C_p：a = C_total / (C_total + C_p) = 1 − α | Paper 明确指出（Fig. 9 的成因） | [Paper Sec. IV-C] |
| Attenuation cap ratio error | C_A 偏差改变 LSB sub-array 相对 MSB sub-array 的权重 → 不是全局 gain，而是每 2^(N/2) code 重复的 INL pattern | BWA 特有 | [Inference] |
| Output buffer gain ≠ 1 | Finite loop gain | 无 buffer → 不相关 | |
| Incomplete settling | C_storage 若 refresh 次数不足，V_storage = V_top · (1 − r^n)，表现为 gain < 1 且随时间变化 | 相关，取决于 refresh 次数与 C_total / C_storage 比 | [Inference] |
| Temperature | C_p 若含 junction 成分则随 T 变；reference cabling IR drop 变 | 需 cryo 标定 | [Inference] |

**Two-point calibration**：用 V(0) 与 V(D_max) 解 a、b，再 D' = round((V_target − b) / (a · LSB))。要求：测量精度 < LSB/2；correction 需要 multiplier 或 LUT；code range 缩小 (1 − a)。**对本架构应 per region 做 2-point（16 个参数），这自动包含 Fig. 9 的修正**（§4.5）。

### 4.4 Code-dependent nonlinearity

Global gain / offset calibration 对 ε(D) 无效：它只能旋转和平移整条曲线，不能消除 mismatch 造成的每个 code 的独立偏差。

| 方法 | 修正什么 | 需要 | 代价 | Cryo 评估 | Tag |
|---|---|---|---|---|---|
| LUT（全 code） | 任意 ε(D) | 8192 × 13 bit ≈ 13 kB memory + 全 code 测量 | Memory 是 paper 中 power 主体 → 极不利 | 不推荐 | [Inference] |
| Per-region 2-point（16 参数） | a_k、b_k，含 Fig. 9 jump | 16 个测量点 | 少量 memory + 一个 multiply 或 shift-add | 推荐 | [Inference] |
| Capacitor trimming（foreground，一次性） | MSB weight 误差 | Trim cap 阵列 + cryo 下测量 + fuse / register | 面积小、power 零；需在 target 温度 trim | 可行 | [Inference] |
| Segmentation | 结构性降低 DNL（§3） | 少量 decoder | 最低 | 推荐 | [Sim] |
| DEM | 把 mismatch 转成随机 ripple | 随机化逻辑 | 对 DC bias 输出，ripple = qubit gate 上的噪声 | 不适合 | [Inference] |
| Redundancy（sub-radix-2 + digital cal） | Mismatch | 额外 weight + 数字校正 | Logic 增加 | 中；主要用于 ADC | |
| Background calibration | Drift | On-chip ADC 持续测量 | ΣΔ 约 1 mW [Paper Sec. IV-B] → 不能常开 | 只能 foreground | [Paper] |
| Matching improvement | σ_u 本身 | 更大 unit cap，common-centroid，dummy | 面积 | 65 nm 下面积充足（§3.4） | [Inference] |

### 4.5 Fig. 9：region-dependent gain deviation + coarse switching discontinuity

**Paper 的描述** [Paper Sec. IV-C]："Parasitic capacitance induces a gain error, creating a jump when switching coarse tuning regions."

**机制推导** [Inference]。设 top plate 有对地 parasitic C_p，reset 相位所有 bottom plate 接 VL、top plate 接 VL（reset 到 region 的下参考）；conversion 相位选中的 bottom plate 切到 VU，top plate 浮空。电荷守恒给出

V_top(D) = VL + (VU − VL) · C_on(D) / (C_total + C_p) = VL + (VU − VL) · (1 − α) · D / 2^N，α = C_p / (C_total + C_p)。

- Region 起点 D = 0：V = VL，**被 reset 钉在 nominal**。
- Region 终点 D = 2^N − 1：V ≈ VL + 125 mV · (1 − α)，**比下一个 region 的起点低 125 mV · α**。
- 结果：每个 region 内 gain = 1 − α；region 边界处输出跳升 125 mV · α，中间的电压 **没有任何 code 能到达** → missing output range。

注意：若 top plate 被 reset 到 ground 而非 VL，同样的 C_p 只会产生 **全局** gain (1 − α)，曲线连续、无 jump。所以 jump 的必要条件是 "region 起点由 reset 钉住、region span 被 α 压缩"。这就是为什么它 **不是 global gain error**，2-point global calibration 修不掉它。

**从 Fig. 9(a) 读数** [Paper-read]：code 4095 → 4096 处输出从约 475.5 mV 跳到约 483.5 mV，jump ≈ 8 mV ≈ 65 LSB → α ≈ 8 / 125 ≈ 6.4%，即 C_p ≈ 0.07 C_total。另外两个 region 的起点都比 nominal（500 mV）低约 16 mV，paper 未解释；[Hypothesis] 可能是 reference 线的 IR drop、DEMUX / S&H 的 charge sharing 或直接测量时 10 GΩ 表头的 loading，属于 region-independent 的 b。

**Paper 的解法** [Paper Sec. IV-C, Fig. 9(b)]：在 region k 结束后不直接切到 (VU, VL) = (625, 500)，而是先用 (625, 375)，即 span 250 mV。此时同一个 fine DAC 的每一步是 2 LSB，覆盖 250 · (1 − α) ≈ 234 mV > 125 mV，足以从 475.5 mV 走到下一 region 起点 483.5 mV，然后再切到 (625, 500)。Fig. 3(b) 的 6-bit 独立选择 VU / VL 正是为此保留的自由度。

**为什么有效**：intermediate span 的可达范围与相邻两个 region 都有 overlap，控制器只需在 overlap 内选择切换点。

**代价** [Inference]：
1. Gap 内 step = 2 LSB，局部分辨率退化到 12 bit。仍满足 Table I 的 250 µV 要求，这正是 paper 留 1 bit margin 的意义。
2. Code → voltage 映射不再是均匀的 13-bit 二进制，需要 remap 逻辑：每个 boundary 一个阈值 + 一个 span 切换，输入 word 总数超过 8192（Fig. 8 x 轴到 ~8600）。
3. α 必须在 cryo 下测得；若 C_p 含 junction 成分则 RT 与 cryo 的 α 不同。
4. Fig. 9(b) 中 intermediate 段的具体 code 数从图上无法精确读出。

**应该做成什么** [Hypothesis]：
- 把它明确实现为 **digital remapping / per-region calibration logic**：存 8 组 (a_k, b_k)（或只存 α 与 8 个 b_k），输入 13-bit target 由逻辑选 region 和 fine code。
- 设计阶段引入 **region overlap**：让 fine DAC nominal span 略大于 125 mV（例如 (VU − VL) = 125 mV 但 fine DAC 满码对应 ~135 mV，或 reference 间距略小于 fine span），使 α 在合理范围内都不产生 gap，remap 只需选切换点。这把 workaround 变成 redundancy。
- 减小 α：top plate routing 用 metal shield 到 VL 而非 ground；避免 junction 型 parasitic；增大 C_total（§3.4 表明面积 / power 允许）。

---

## 5. Design Implications for Our DAC

| Topic | Problem | Paper Solution | Possible Improvement | Impact on Our Design | Tag |
|---|---|---|---|---|---|
| Topology | RT DAC 依赖 transistor 参数，cryo 下失效 | Charge-redistribution，transistor 只做 switch，无 static power | 保持 | 基线 architecture 候选：charge-redistribution | [Paper] + [Inference] |
| Resolution vs mismatch | Cap mismatch 限制 ~10 bit | 10-bit array + 3-bit coarse reference | 去掉 attenuation cap（sensitivity ↓ 5.7×）；segmented 3–4T | V2 model 加 BWA vs plain binary vs segmented 对比 | [Sim] + [Hypothesis] |
| Coarse tuning | 需要 13 bit 且低 power | 8 external references，VU / VL 独立 6-bit 选择 | 保留；研究 on-chip 生成的可能性（cryo reference 是独立课题） | 需要确定 external reference 线数与精度预算 | [Paper] + [Open] |
| Fig. 9 jump | Top-plate C_p → region gain 1 − α → 边界 gap | 250-mV intermediate span，2× step | Region overlap by design + per-region (a_k, b_k) remap；减小 C_p | V2 加 `enable_parasitic` 与 coarse-region remap 模块 | [Paper] + [Hypothesis] |
| Offset | Reference / injection 造成 per-region offset | 未讨论（测量端数字减去） | Per-region one-point | V2 calibration 模块 | [Inference] |
| Output stage | Buffer 在 cryo 下 clipping、耗电 | 无 buffer，C_storage 逐步充电 | 保留；量化 settling 次数 | V2 加 S&H charge-sharing 模型 | [Paper] |
| Leakage / refresh | S&H droop | Periodic refresh，3.9 kHz sweet spot | 可编程 refresh；利用 cryo leakage 下降进一步降 f_R | V2 加 leakage + refresh 模型 | [Paper] + [Inference] |
| Power | Digital 99.5% | 指出随 node scaling | 减少 memory、timing logic 共享、低 clock；coding 方案不能增加 per-element latch | Architecture 评价指标里 digital 复杂度权重高 | [Paper] + [Inference] |
| Coding | Binary DNL 在 major carry 最差 | Binary（BWA） | Segmented 3–4T + B | 候选：4T + 6B（或 3T + 7B）plain array | [Sim] |
| Measurement / calibration | Cryo 下无法用 RT 仪器直接观察 | On-chip ΣΔ + WC（测试用） | 复用为 foreground calibration 的测量端 | 预留 calibration 测量路径 | [Paper] + [Hypothesis] |
| Model validity | PDK 在 4 K 无效 | 未讨论（实测验证） | 用 cryo model 或人工 corner；topology 对 transistor 参数不敏感 | Transistor-level 阶段的 corner 策略 | [Ext] + [Hypothesis] |

**Preliminary recommendation** [Hypothesis]：charge-redistribution + coarse external reference（VU / VL 独立）+ DEMUX S&H + refresh；fine DAC 采用 plain（无 attenuation cap）segmented 4T + 6B 或 3T + 7B；Fig. 9 问题以 region overlap + per-region 2-point remap 处理。是否需要 attenuation cap、segmentation 级别、C_total 大小，交由 V2 behavioral model 在真实 σ_u 下定量决定。

---

## 6. Next Behavioral Model Updates（V2）

原则：v1 文件 [bias_voltage_dac_model.py](../bias_voltage_dac_model.py) 不动；V2 为新文件，每个 non-ideality 有独立 enable flag。

| 优先级 | Module | 内容 | Flag | 对应本周结论 |
|---|---|---|---|---|
| 1 | Error decomposition | 用 endpoint / LSQ 拟合 (a, b)，ε(D) 为残差；DNL 用实际 LSB 归一化；同时输出 raw 与 fitted 指标 | — | §4.1 |
| 1 | Coding architecture | binary / thermometer / segmented(M)；element-level mismatch（unit-cap N(0, σ_u)）；可选 BWA（attenuation cap + C_A mismatch） | `arch`, `enable_mismatch`, `enable_attenuation_cap` | §3 |
| 1 | Coarse reference + parasitic | 8 region（VU, VL 独立）；top-plate C_p → α；reset 到 VL；region 边界 jump 复现 | `enable_coarse_tuning`, `enable_parasitic` | §4.5 |
| 2 | Calibration | one-point / two-point global；per-region (a_k, b_k)；intermediate-span remap（paper 方式）；region-overlap 方式 | `cal_mode` | §4.2–4.5 |
| 2 | Offset / gain injection | 保留 v1 的 b、a，但改为 per-region 可选 | `enable_offset`, `enable_gain_error` | §4 |
| 3 | S&H + refresh | C_total / C_storage charge sharing，n 次 refresh 后的 settling；I_leak · T_R / C_storage droop；ripple | `enable_sh`, `enable_leakage` | §2.3 |
| 3 | Cryogenic parameter layer | 作为参数集而非物理模型：`sigma_u_scale`, `ron_scale`, `leak_scale`, `offset_shift`, `alpha_shift(T)`；RT 与 cryo 两套 | `temp_profile` | §1 |
| 4 | Monte Carlo + power proxy | 批量 run，输出 max|DNL| 分布、P(non-mono)；element / latch / driver 计数作 digital 复杂度 proxy | — | §3.4–3.6 |

第一步建议只做优先级 1 的三个 module，重现 Fig. 9(a) 的 jump 和 Fig. 8(f) 量级的 DNL，作为 V2 的 sanity check。

---

## 7. Open Questions（transistor-level 之前需要回答）

1. **Target 温度**：6 K（paper 测量）还是 100 mK（应用）？决定 PDK 策略和 self-heating 假设。
2. **Channel 数与 refresh 预算**：多少 channel、允许的 settling 时间（决定 f_R 与 C_storage）。
3. **External reference 是否允许**：8 根线在 mK stage 的 wiring 成本；若不允许，需要 cryo 的 on-chip reference 或 on-chip 分压 + 精度预算。
4. **PDK 的 MOM capacitor mismatch 数据**（σ_u vs 面积）：决定 unit cap 尺寸和是否需要 segmentation / trimming。
5. **Cryo model 可用性**：是否有 foundry 或学术的 65 nm cryo compact model；否则用什么人工 corner。
6. **Fig. 9 的 α 在 RT 与 cryo 是否相同**：决定 calibration 在哪个温度做。
7. **Fig. 8(d) 中 390 kHz 的周期性 DNL pattern 成因**：影响 refresh rate 上限的选择。
8. **Digital 21 µW 的构成**：memory leakage 还是 clock / timing 动态功耗？决定降功耗的方向和 coding 方案的 digital 预算。
9. **DEMUX / S&H switch 的 charge injection 在 cryo 下的量级**：决定 per-region offset 的预算。
10. **Qubit 端对 refresh ripple 的容忍度**：决定 C_storage 与 series R 的选择。

---

## References

Reference paper（本地 `paper_for_reference/`）：
- P. Vliex, C. Degenhardt, C. Grewing, A. Kruth, D. Nielinger, S. van Waasen, S. Heinen, "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. DOI 10.1109/LSSC.2020.3011576.

Paper 引用且本周用到的：
- [6] M. Saberi, R. Lotfi, K. Mafinezhad, W. A. Serdijn, "Analysis of power consumption and linearity in capacitive digital-to-analog converters used in successive approximation ADCs," IEEE TCAS-I, vol. 58, no. 8, 2011（Eq. (1) 来源，本地无 PDF，未核对推导）。
- [3] R. M. Incandela et al., "Characterization and compact modeling of nanometer CMOS transistors at deep-cryogenic temperatures," IEEE JEDS, vol. 6, 2018. https://www.researchgate.net/publication/320651319
- [5] B. Patra et al., "Characterization and analysis of on-chip microwave passive components at cryogenic temperatures," IEEE JEDS, vol. 8, 2020. https://arxiv.org/abs/1911.13084

External（仅由 web search 摘要核对，未读全文）：
- P. A. 't Hart et al., "Characterization and Modeling of Mismatch in Cryo-CMOS," IEEE JEDS, 2020. https://ieeexplore.ieee.org/document/9015956 （σ(ΔVTH) 约 2× @ 4.2 K，Pelgrom 仍成立）
- P. A. 't Hart et al., "Subthreshold Mismatch in Nanometer CMOS at Cryogenic Temperatures," IEEE JEDS, 2020. https://ieeexplore.ieee.org/document/9072133
- B. Dierickx et al., "Effect of deep cryogenic temperature on SOI CMOS mismatch," Cryogenics, 2014. https://www.sciencedirect.com/science/article/abs/pii/S0011227514000873
- H. Homulle et al., "Deep-Cryogenic Voltage References in 40-nm CMOS," IEEE JSSC, 2018. https://ieeexplore.ieee.org/document/8490692
- A. Beckers et al., "Cryogenic MOSFET Threshold Voltage Model," 2019. https://arxiv.org/pdf/1904.09911
- "Cryogenic Characterization of Low-Frequency Noise in 40-nm CMOS," 2024. https://arxiv.org/pdf/2405.17685
