# Phase 2 — Cryogenic Bias Voltage DAC: Architecture Research Note

Date: 2026-09-12
Scope: research / architecture study + behavioral model v2. No transistor-level implementation.

Companion code:
- [model/bias_dac_v2.py](../model/bias_dac_v2.py) — v2 behavioral model（ideal cap DAC / mismatch / BWA / parasitic / gain / offset / coarse tuning / S&H / leakage / refresh / jump compensation），生成 `docs/figures/v2_*.png`
- [model/arch_compare_v2.py](../model/arch_compare_v2.py) — binary vs thermometer vs segmented Monte Carlo
- [bias_voltage_dac_model.py](../bias_voltage_dac_model.py) — v1，未改动

## 来源标注规则

| Tag | 含义 |
|---|---|
| **[Paper]** | P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE SSC-L, vol. 3, 2020，注明 Section / Fig. / Table |
| **[Paper-read]** | 从 paper figure 上读出的数值，精度受限 |
| **[Ext]** | 外部文献（文末 References） |
| **[Sim]** | 本周 v2 model / comparison script 的结果 |
| **[Assume]** | 我们的 behavioral-model 假设（paper 未给出的参数） |
| **[Inference]** | 我们基于以上材料的推导，paper 没有明说 |
| **[Hypothesis]** | 可能的 design direction，尚未被文献或 simulation 支持 |

**温度说明**：paper 的 silicon measurement 全部在约 6 K（attoDRY800 cryostat）进行 [Paper Sec. IV]；100 mK 只是目标应用环境（mixing chamber）[Paper Sec. II]，paper **没有** 展示 100 mK 下的工作结果。

---

## 0. Executive Summary

1. **Cryo 下 conventional DAC 退化的核心原因**：transistor 参数（VTH、subthreshold slope、mismatch、bias point）大幅偏离 PDK 预期，而 capacitor 几乎不变。**越少依赖 transistor analog 参数、越多依赖 capacitor ratio 的 architecture 越 cryogenic-friendly** [Ext] + [Inference]。Paper 中所有 cryo failure 都出现在 opamp / comparator，DAC 核心（switch + cap）没有报告任何 cryo-specific failure [Paper Sec. IV]。
2. **Reference paper 的 DAC** = 10-bit BWA capacitive DAC + 3-bit coarse reference selection（8 external references）+ 8 路 DEMUX S&H，无 output buffer，periodic refresh 对抗 leakage [Paper Sec. III, Fig. 2, Fig. 3]。总功耗 2.63 µW/channel，99.5% 是 digital [Paper Table II]。
3. **Binary vs Thermometer**：相同 unit-cap mismatch 下 thermometer 只改善 DNL / monotonicity，**不改善 INL** [Sim]。Full thermometer 在 10 bit 需要 1023 elements。**Segmented 4T+6B 用 21 个 elements 把 worst-case DNL 降低约 40%** [Sim]。Decoder 本身的 digital 增量可忽略，真正的代价是 element 数带来的 driver / latch / routing [Inference]。
4. **v2 model 复现了 paper 的两个关键量化结果** [Sim]：(a) BWA 的 Monte Carlo max|DNL| = 0.554 LSB，与 paper Eq. (1) 的 0.543 LSB 和实测 σ_D = 0.495 LSB 一致；(b) α = 6.4% 的 top-plate parasitic 产生 66 LSB（8.1 mV）的 region 边界 jump，intermediate 250-mV span 每个边界加 36 个 2-LSB 步即可填补，总 word 数 8444（paper Fig. 8 x 轴约 8600）。
5. **Fig. 9 的 jump 是 missing output range，不是 code labelling 问题**：global 或 per-region 2-point calibration 都无法修复（coverage 不变，6.3% 的 target 电压不可达），只有增加可达电压的方法（wider span / overlap）才有效 [Sim] + [Inference]。
6. **Preliminary recommendation** [Hypothesis]：保留 charge-redistribution + coarse external reference + DEMUX S&H + refresh 框架；fine DAC 改为 plain（无 attenuation cap）segmented 4T+6B，mismatch sensitivity 比 BWA 低约 9×；Fig. 9 问题在设计阶段用 region overlap + per-region 2-point remap 解决；refresh rate 可编程，围绕 3.9 kHz。

---

## 1. Cryogenic CMOS Bottlenecks

### 1.1 Concise table（deliverable 格式）

| Cryogenic effect | CMOS / device consequence | DAC consequence | Possible mitigation | Source |
|---|---|---|---|---|
| VTH 上升 +0.1 ~ +0.2 V（bulk 40/65 nm @ 4 K） | Overdrive 减少；mid-rail 附近的 TG 两管都可能 weak inversion；RT bias 点漂移 | Bottom-plate / S&H switch Ron 升高、settling 变慢；buffer 输入 CM range 缩小 | 提高 VDD（paper opamp 1.7 V）；bootstrapped switch；低 VT 器件；forward body bias；减少 stacking | [Ext: Incandela 2018] + [Paper Sec. IV-A] |
| Mobility 上升（low-field 1.5–2×，short channel 受 velocity saturation 限制） | gm、ID 上升，Ron 下降，部分抵消 VTH | 有利；loop gain / bandwidth 变化需重验 | 用 cryo model 重做 AC / transient | [Paper Sec. IV-A] + [Ext] |
| Subthreshold slope 变陡（理论 0.8 mV/dec，实测饱和 ~10–20 mV/dec） | Weak / moderate inversion 区间极窄，器件 on/off 近似阶跃 | Opamp pMOS pair 在 input > 0.7 V 时 clipping [Paper Fig. 6]；comparator CMFB 700 → 500 mV | 所有 analog 器件强反型；去掉 opamp（paper DAC 主路径无 buffer） | [Paper Sec. IV-A/B] + [Ext] |
| Weak / moderate inversion 不可用 | 低功耗 analog 的常用 bias 区域消失 | 无法用 subthreshold opamp / reference | 用 switch + capacitor 实现功能，避免 bias 电流 | [Paper] + [Inference] |
| Switch Ron | VTH ↑ 与 mobility ↑ 相抵，净效果依 VGS 而定；mid-rail 最差 | Settling 时间、conversion slot 长度 | Switch 只在 VL / VU 两个固定电平工作（paper 结构天然如此）；bootstrapping | [Inference] |
| Subthreshold / junction leakage 指数下降；gate tunneling 不变 | Off-switch leakage 到 fA 以下 | S&H hold 时间变长 → refresh rate 可降 → digital power 下降 | 可编程 refresh；保留 refresh（gate leakage、trapping 不随 T 消失） | [Paper Sec. IV-C] + [Inference] |
| Transistor mismatch：σ(ΔVTH) ≈ 2×；subthreshold mismatch 反常增大 | Diff pair offset、mirror mismatch 变差 | Current-steering unit current 变差；opamp offset shift 2 mV [Paper] | 精度交给 capacitor matching；transistor 只做 switch | [Ext: 't Hart 2020; Dierickx 2014] + [Paper Sec. IV-A] |
| Thermal / kT/C noise ∝ T 下降；flicker noise 不降 | 1 pF：kT/C 64 µV (300 K) → 9 µV (6 K) | S&H 采样噪声不是瓶颈；refresh ripple 才是 | 对 DC bias 输出，噪声预算由 ripple / leakage 决定 | [Inference] + [Ext: LFN 40 nm 2024] |
| Capacitor（MOM）变化数 %，ratio 更稳 | Cap-ratio DAC transfer 不随 T 变 | Charge-redistribution 核心优势 | — | [Paper Sec. III 引 [5]] + [Ext: Patra 2020] |
| Resistor：poly TCR 小；diffusion / n-well 有 freeze-out | 绝对值可变数十 %；ratio 取决于 TCR mismatch | Resistor-string 的问题是 static current 和 tap switch，不是 R 本身 | 若用 R 只用 poly；R 需极大 | [Ext] + [Inference] |
| Supply / headroom：VTH 吃掉 0.1–0.2 V | Stacked 结构不够用 | Paper 只在含 opamp 的 aux 路径提 VDD 到 1.7 V；DAC 核心 1.2 V | 最少 stacking；switch + cap 结构；boosted switch | [Paper Sec. IV-A, Table III] |
| Bias current / current mirror 精度 | Mirror mismatch ↑、rout 变、gm/ID 变 | Current-steering unit current 误差；bandgap 失效（BJT 冻结） | External reference（paper 做法）或 cryo reference（DTMOS） | [Paper Fig. 3(b)] + [Ext: Homulle 2018] |
| Compact model 无效（foundry 只到 −40 °C） | 4 K 定量 simulation 不可信 | 无法做 PVT corner；余量无法量化 | Cryo model（MOS11/PSP、EKV）；人工 corner "VTH +150 mV @ −40 °C" [Hypothesis]；选参数不敏感 topology | [Ext: Incandela 2018; Beckers 2019] |
| Freeze-out / kink / impact ionization | 高 VDS 下 ID–VDS kink、hysteresis、substrate current | 对 VDS ≈ 0 的 switch + cap 影响小；对 buffer / mirror 影响大 | 限制 VDS；body tie | [Ext: Incandela 2018] |
| Parasitic 随 T 变：junction cap 变，metal R 降 5–10× | Junction 型 C_p 随 T 变 | Fig. 9 的 α 在 RT / cryo 可能不同 → remap 需在 cryo 标定 | 把 top-plate parasitic 做成 metal 型；标定在目标温度 | [Inference] |
| Power budget：~400 µW @ 100 mK | — | 任何 static current 按 nW 计 | 无 static power topology；低 f_R | [Paper Sec. II] |
| Self-heating | 器件温度 ≠ bath 温度 | 100 mK 与 6 K 行为差异未知 | 最小化 dissipation | [Inference] |

### 1.2 Reference paper 中实际观察到的 cryogenic behavior [Paper]

| 观察 | 位置 | 数值 | 解释 |
|---|---|---|---|
| Unity-gain buffer clipping | Sec. IV-A, Fig. 6 | Cryo 1.2 V：input > ~0.7 V 输出跳到 rail；1.7 V 正常 | Paper：pMOS input pair 的 input CM 超过 VTH，steep subthreshold slope 使 moderate / weak inversion 不可行 |
| Supply 提高 | Sec. IV-A, IV-C, Table III | Opamp / ΣΔ 1.7 V；DAC 1.2 & 2.5 V | 只有含 opamp 的 aux 路径需要 |
| CMFB 调整 | Sec. IV-B | 700 → 500 mV | 同上 |
| Mobility-related | Sec. IV-A | Output 近 ground 从 54 mV → 33 mV | Paper：mobility 上升，同电流需要更小 VDS |
| Offset shift | Sec. IV-A, IV-B | Opamp ~2 mV；ΣΔ ~5 mV | Paper：在 process mismatch 范围内；ΣΔ offset 可数字减去 |
| Bandwidth | Sec. IV-A | 225 → 250 kHz（100 pF cable） | 与 mobility 上升一致 |
| Opamp power 基本不变 | Sec. IV-A | 1.2 V: 140 → 120 µW；1.7 V: 240 → 270 µW | Bias 电流为 external reference current |

### 1.3 为什么 charge-redistribution 在 cryogenic 下可能优于 resistor-string / current-steering

| 角度 | Resistor-string | Current-steering | Charge-redistribution | Source |
|---|---|---|---|---|
| Static power | I = Vref / R_total：1 V / 1 MΩ = 1 µW；nW 级需 GΩ | Full-scale current 流入 load：1 V / 10 kΩ = 100 µW | 零 static；paper core 77 nW [Paper Table II] | [Paper] + [Inference] |
| 对 transistor analog 参数的依赖 | R ratio 决定精度，tap switch Ron / leakage 进入误差 | Current-source VTH / β mismatch 决定精度，cryo 下 2× | C ratio 决定；transistor 只需 "能开能关" | [Ext: 't Hart 2020] |
| R / C 在 cryo 的行为 | R 绝对值、TCR 依类型变化 | — | C 变化数 %，ratio 更稳 | [Ext: Patra 2020] |
| Noise | R 的 thermal noise 与 bandwidth 相关 | 同 | kT/C 与 bandwidth 无关，随 T 线性下降 | [Paper Sec. III] |
| Matching / resolution | 2^N 个 R + switch | 2^N 个 unit current（或 segmented） | Binary 只需 N 个 weight | |
| Headroom | 中间 tap 的 TG 在 VTH ↑ 后可能失效 | Cascode 需要 headroom | Top plate 只在 VL ~ VU（125 mV）内；switch 只在两个固定电平切换 | [Inference] |
| Multi-channel | 每 channel 一条 string 或复杂 mux | 每 channel 一组 source | 一个 array 时分给 8 channel | [Paper Sec. III] |
| 弱点 | Static power；switch 数 | Static power；mismatch | 需要 refresh；leakage；parasitic gain；top plate 高阻 | |

**核心结论** [Inference]：RT DAC 在 cryo 退化，是因为它把精度或 bias 建立在 transistor 的 analog 参数上，而这些参数在 4 K 偏离 PDK 数十 % 且 mismatch 加倍。Charge-redistribution 把精度转移到 capacitor ratio，把 transistor 降级为 digital-like switch，无 static power，因此对 cryo 最不敏感；它的代价（leakage / refresh / parasitic gain）在 cryo 下部分缓解（leakage 下降），部分需要 digital remap（parasitic gain）。

---

## 2. Reference Paper Architecture Breakdown

### 2.1 Paper 明确给出的 quantitative values [Paper]

| 项目 | 数值 | 位置 |
|---|---|---|
| Technology | TSMC 65-nm CMOS | Abstract, Table III |
| Output range | 0 V – 1 V | Table I, Sec. II |
| Required step / resolution | 250 µV ≈ 12 bit | Table I |
| Designed step / resolution | ~125 µV，13 bit（含 margin） | Sec. II |
| Channel count | 8 | Sec. II, Table III |
| Fine DAC（cap array）resolution | 10 bit | Sec. III, Sec. IV-C, Fig. 8(d) |
| Coarse tuning | 8 external references → +3 bit；VU / VL 独立选择（0 – 1 V 每 125 mV，9 tap，6-bit 选择线） | Sec. III, Fig. 3(b) |
| Charging power 降低 | 1 V → 0.125 V，P ∝ V²fC，1/64 | Sec. III |
| Temperature | 应用 100 mK；测量 ~6 K | Table I, Sec. II, Sec. IV |
| Cooling budget | ~400 µW @ 100 mK；chip 总功耗 ≪ 1 mW | Sec. II, Table I |
| Nominal refresh rate | f_R = 390 kHz | Sec. IV-C, Fig. 8(a)–(d) |
| Sweet-spot refresh rate | 3.9 kHz | Sec. IV-C, Fig. 8(e)(f) |
| Leakage 目标 | 电压变化 "lower tens of microvolt"；DAC 驱动能力按 pA leakage 设计 | Sec. III, Sec. III-A |
| Measured DNL σ | σ_D = 0.495 LSB（direct, 3.9 kHz） | Sec. IV-C |
| Inferred capacitor mismatch | σ0 = 0.003 C0（Eq. (1)，N = 10） | Sec. IV-C |
| Eq. (1) | σ²_DNL,BWA = σ²_D ≈ 2^(3N/2) · (σ0/C0)² LSB² | Sec. III，引 [6] |
| Power @ 3.9 kHz | Core 77 nW；references 3 nW；digital 21 µW；DAC total 21.1 µW = 2.63 µW/ch；clock buffer 4.3 µW；total 25.4 µW = 3.18 µW/ch | Table II |
| Digital 占比 | 99.5% | Sec. IV-C, Sec. V |
| Supply | 1.2 & 2.5 V（DAC）；opamp / ΣΔ 测试 1.7 V | Table III, Sec. IV-A |
| Area | DAC 0.135 mm² / 0.14 mm² | Fig. 10, Table III |
| Opamp | 70 dB open-loop；offset shift ~2 mV；UGBW 225 → 250 kHz | Sec. IV-A |
| 对比 | 其他 cryo DAC 均为 current-steering BiCMOS，mW 级，单 channel | Table III |

### 2.2 Architecture diagram

```mermaid
flowchart LR
    I2C[I2C interface<br/>RT host] --> MEM[per-channel code memory<br/>13 b + coarse bits]
    MEM --> TIM[shared timing generator<br/>reset / convert / DEMUX / S&H phases]
    REFS[8 external references<br/>0..1 V step 125 mV] --> MUX[6-bit reference MUX<br/>VU, VL independent]
    MEM --> MUX
    MUX -->|VU / VL| ARR[10-bit BWA capacitor array<br/>LSB sub-array | C_A | MSB sub-array<br/>bottom plates: bit=1 to VU, bit=0 to VL]
    TIM --> ARR
    ARR -->|floating top plate<br/>V = VL + (VU-VL)(1-alpha) D/2^N| DEMUX[DEMUX 1:8]
    DEMUX --> SH1[S&H ch.1: R + C_storage]
    DEMUX --> SH8[S&H ch.8: R + C_storage]
    SH1 --> Q1[bond wire -> C_electrode -> qubit gate]
    SH8 --> Q8[bond wire -> C_electrode -> qubit gate]
    ARR -.->|second DAC copy| AUX[aux: unity-gain opamp, ΣΔ ADC, window comparator<br/>for measurement only]
```

Sources：Fig. 1（I2C，两个 DAC），Fig. 2（cap array、DEMUX、S&H、bond wire、C_electrode），Fig. 3(b)（reference ladder + 6-bit MUX），Fig. 4（aux circuits），Sec. IV-C（timing shared，memory per DAC）。Top-plate 表达式为 [Inference]，见 §4.5。

### 2.3 Design-decision Q&A

| 问题 | 回答 | Tag |
|---|---|---|
| Why charge-redistribution? | 无 static power；kT/C noise 与 bandwidth 无关；capacitor 低温变化小；方便 DEMUX 到多 channel | [Paper Sec. III] |
| Binary-weighted array + attenuation capacitor（BWA）? | 减少总电容（约 2 × 32 + 1 units 而非 1024）；代价是 mismatch sensitivity 按 2^(3N/4) 增长（Eq. (1)），比 plain binary 的 2^(N/2) 多 2^(N/4) ≈ 5.7× | [Paper Eq. (1)] + [Sim §5.2] |
| How many effective bits? | 13 bit 设计（122 µV），满足 12 bit / 250 µV 要求 | [Paper Sec. II, Table I] |
| Bits inside the cap array? | 10 bit | [Paper Sec. III, IV-C] |
| Extra bits from coarse tuning? | VU − VL = 125 mV 的 8 个 region 覆盖 0–1 V → +3 bit | [Paper Sec. III, Fig. 3(b)] |
| Why multiple reference voltages? | (a) +3 bit 不增加 cap array；(b) swing 1 V → 125 mV，CV²f 降 1/64；(c) [Inference] mismatch 只在 10 bit 内累积 | [Paper Sec. III] + [Inference] |
| Why S&H? | 一个 DAC 时分给 8 channel，C_storage 保持电压 | [Paper Sec. III] |
| Why no output buffer? | 不需要在一次 conversion 内充满 C_storage；多次 refresh 逐步逼近；省 power / area / noise；且 buffer 在 cryo 下有 clipping 问题（Fig. 6） | [Paper Sec. III, IV-A] |
| Why refresh? | S&H leakage / disturbance 使电压漂移 | [Paper Sec. III, Fig. 3(a)] |
| What determines refresh rate? | 上限：digital power ∝ f_R；下限：δV_C = I_leak · T_R / C_storage < 数十 µV；另外 code 更新后的 settling = (refresh 次数) × T_R [Inference]。Sweet spot 3.9 kHz | [Paper Sec. IV-C] + [Inference] |
| What limits resolution? | Capacitor mismatch，不加 calibration 约 10 bit | [Paper Sec. III] |
| What produces DNL? | (a) cap mismatch（Eq. (1)）；(b) coarse-region jump（Fig. 9）；(c) buffer 引入的 DNL（Fig. 8(b) vs (d)）；(d) 390 kHz 时每 1023 LSB 的周期 pattern（Fig. 8(d)），3.9 kHz 消失，paper 未解释 | [Paper] + [Hypothesis] |
| What causes the coarse-region jump? | Parasitic capacitance 引起 gain error | [Paper Sec. IV-C]，机制见 §4.5 |
| How do intermediate steps fix it? | 用 (VU, VL) = (625, 375) 的 250 mV span、2× step 走过 gap | [Paper Sec. IV-C, Fig. 9(b)] |
| What dominates power? | Digital memory & logic 21 µW / 21.1 µW；core 77 nW | [Paper Table II] |
| Shared vs duplicated? | Shared：cap array + switches、reference MUX、timing、clock buffer。Per channel：DEMUX switch、R、C_storage、bond wire、code memory。Per DAC："some digital memory circuitry" | [Paper Sec. IV-C] + [Inference] |

### 2.4 Analog vs digital bottleneck 划分 [Inference]

| Block | 类型 | 限制什么 | Paper 是否已解决 |
|---|---|---|---|
| Cap array mismatch | Analog | Fine DAC ≤ 10 bit | 用 coarse reference 绕开，未 calibrate |
| Top-plate parasitic C_p | Analog / layout | Region gain 1 − α，边界 jump | Intermediate steps（digital remap） |
| S&H leakage | Analog | Refresh rate 下限 | Refresh；cryo 下 leakage 变小 |
| Reference voltages | System | 8 根外部线的绝对精度 / IR drop → region 起点 | 外部提供，未讨论精度 |
| Memory & timing logic | Digital | 99.5% power | 指出随 node scaling，未优化 |
| Clock buffer | Digital | 4.3 µW（17%） | 未讨论 |
| Measurement / calibration | Aux | Cryo 下观察 DAC 需 on-chip ΣΔ + WC | 提供了工具，未用于 calibration |

### 2.5 复用 / 改进 [Inference / Hypothesis]

**复用**：charge-redistribution 核心；coarse reference 分区；S&H + DEMUX 共享；无 buffer；可编程 refresh；on-chip ΣΔ 作 in-situ 测量。

**改进**：(1) 去掉 attenuation cap（§5.2 显示 sensitivity 降 ~9×，面积功耗可承受）；(2) Fig. 9 remap 做成 design-time region overlap + per-region 2-point；(3) digital 是主战场，coding 方案不得增加 per-channel memory；(4) 8 根 reference 线在 mK stage 的成本未量化 [Open]。

---

## 3. Binary vs Thermometer vs Segmented

### 3.1 Binary-weighted

- Element 数 N（10 bit → 10），weight 2^k 由 2^k 个 unit 组成；无 decoder。
- **Major carry 0111…1 → 1000…0**：MSB（2^(N−1) units）打开，其余 2^(N−1) − 1 units 关闭；step 是两个大数之差，σ_step ≈ σ_u · 2^(N/2)。10 bit、σ_u = 0.3% → 0.096 LSB；σ_u = 2% → 0.64 LSB，出现 non-monotonic 风险 [Inference，与 Sim 一致]。
- **Glitch**：MSB on / LSB off 不同步时瞬态到 0 或 full scale。对本项目（DC bias、S&H 在 settle 后才连接）glitch **不进入输出**，只需 timing 上先 settle 再闭合 DEMUX / S&H switch [Inference]。与高速 DAC 的 glitch energy 问题本质不同。
- Monotonicity 不保证；layout 需 common-centroid；switch driver 数 = N，但 MSB switch 尺寸 ∝ 2^(N−1)。

### 3.2 Thermometer / unary

- 2^m − 1 个 unit（10 bit → 1023）；decoder 约 (2^m − 1)(m − 1) gate-equivalent（10 bit ≈ 9000）。
- DNL 每步只切一个 unit，σ_DNL ≈ σ_u；monotonic；**INL 与 binary 相同**（同样的 unit random walk）[Sim]。
- 在 charge-redistribution 的 reset-then-set 流程里，每次 conversion 所有 ON 元件都要重新驱动，activity 取决于 ON 元件数而非 Hamming distance [Inference]。
- 1023 条控制线 + 1023 latch + 1023 driver：element 和 routing 按 2^m 增长。

### 3.3 Segmented

M 位 thermometer MSB（2^M − 1 element，每个 2^(N−M) units）+ (N − M) 位 binary。Major carry 在 LSB sub-array 与一个 MSB unit 之间，σ ≈ σ_u · 2^((N−M)/2) · √2，比 full binary 低 2^(M/2)。

### 3.4 Simulation 结果 [Sim, arch_compare_v2.py]

Model：每个 unit cap 独立 N(0, σ_u)，weight 2^k 由 2^k 个 unit 组成，Vout = Vref · C_on / C_total（plain array，无 attenuation cap，无 parasitic），2000 MC，N = 10，σ_u = 0.003。

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

读数：INL 与 coding 无关；4T + 6B 用 21 element、45 gate 降低 worst-case DNL 约 40%，non-monotonic 风险推到 σ_u ≈ 3%；full thermometer 的 DNL 优势对 DC bias DAC 没有对应的 INL 收益。

### 3.5 Decision table（deliverable 格式）

| Architecture | Matching / DNL | Monotonicity | Glitch | Capacitor area | Switch count | Digital power | Cryogenic suitability |
|---|---|---|---|---|---|---|---|
| Binary (plain) | DNL ∝ σ_u·2^(N/2)；0.10 LSB @ σ_u=0.3% | 不保证（σ_u > 2% 开始失效） | 最大，但 S&H timing 隔离后不进入输出 | 1024 units（同 total） | 10 (+1 dummy) | 最低：0 decoder，10 driver | 好 |
| Binary + attenuation cap (paper BWA) | DNL ∝ σ_u·2^(3N/4)；0.55 LSB @ σ_u=0.3% [Sim = Eq. (1)] | 同上但更敏感 | 同上 | 最小（~65 units） | 10 + C_A | 最低 | 好，但 mismatch 余量最差 |
| Thermometer | DNL ≈ σ_u；INL 不变 | 保证 | 最小 | 1024 units | 1023 | 最高：~9k gate decoder，1023 driver / latch / routing | 差：element 数 100× 换不到 INL |
| Segmented 4T + 6B（推荐候选） | DNL 0.06 LSB @ σ_u=0.3%（−40% vs binary） | MSB 段保证 | 中 | 1024 units | 21 | 极低：45 gate，21 driver | 好 |

### 3.6 Digital power 是否值得？

[Inference] Paper 的 21 µW digital 是 **memory + timing logic**，与 coding 无关。DAC 共享给 8 channel，所以 decoder 只有一份、在 conversion 时从 binary register 解码，**每 channel 的 memory 宽度不变**。Segmented 4T+6B 的 decoder（45 gate）和 21 个 driver 对 21 µW 是 < 0.1% 的增量。Full thermometer 的 1023 latch / driver / routing 在功耗上也许只到 µW 级（§6），但 INL 没有改善、面积和 routing 100×，不合理。

**Preliminary recommendation**：后续 transistor-level 探索 **plain（无 attenuation cap）segmented 4T + 6B 的 10-bit fine DAC**，配合 3-bit coarse reference。若 PDK 的 MOM mismatch 数据显示 σ_u ≤ 0.5% 可轻松达到，plain binary 也可接受；BWA 只在面积极端受限时考虑。

---

## 4. Gain / Offset / Nonlinearity Compensation

### 4.1 统一 error model

V_actual(D) = V_offset + G · V_ideal(D) + V_nonlinear(D)，即 a · V_ideal + b + ε(D)

| 项 | 物理含义 | v1 model 的表现 | v2 model |
|---|---|---|---|
| b（offset） | Code-independent 偏移 | endpoint-fit INL 看不到；DNL 看不到 | `decompose()` 用 LSQ 提取 a, b，报告 ε(D) |
| a（gain） | 斜率误差 | INL 看不到；DNL 用 nominal LSB 时表现为常数 a − 1 | 同上；DNL 应用实际 LSB 归一化 |
| ε(D) | Mismatch、parasitic、settling | Per-code 独立 Gaussian，与真实结构不符 | Element-level mismatch，code 间强相关 |

### 4.2 Offset 来源

| 来源 | 机制 | 相关性 | Tag |
|---|---|---|---|
| Buffer input offset | Diff pair mismatch | Paper qubit 路径无 buffer；测量路径 2 mV，cryo 下 shift | [Paper Sec. IV-A] |
| Reset switch charge injection / clock feedthrough | Top plate reset 关断注入 ΔQ → ΔV = ΔQ / C_total；code-independent 部分是 offset，与 top-plate 电压相关的部分进入 ε(D) | 直接相关；C_total 越大越小 | [Inference] |
| DEMUX / S&H switch injection | 注入到 C_storage | C_storage 大则小 | [Inference] |
| Reference offset | VL_k 的绝对误差 → **per-region offset**，不是全局 b | 直接相关（8 根外部线的 IR drop、cabling） | [Inference] |
| Temperature shift | VTH 变化改变 injection；opamp offset 变化 | 需在 cryo 标定 | [Paper] + [Inference] |

**One-point**：b = V_meas(0)，D' = D − round(b / LSB)。代价：两端各损失 |b| / LSB 个 code；需 cryo 测量手段（paper 的 ΣΔ + WC）。对本架构应 **per region**（8 个 b_k）。

### 4.3 Gain 来源

| 来源 | 机制 | 相关性 | Tag |
|---|---|---|---|
| Reference error | (VU − VL) 与 125 mV 的偏差 → per-region a_k | 直接相关 | [Inference] |
| Parasitic capacitance | Top plate C_p：a = C_total / (C_total + C_p) = 1 − α | Fig. 9 成因 | [Paper Sec. IV-C] |
| Attenuation cap ratio error | C_A 偏差改变 LSB sub-array 权重 → 每 32 code 重复的 pattern（Fig. `v2_dnl_vs_code` 右上） | BWA 特有 | [Sim] |
| Buffer gain ≠ 1 | Finite loop gain | 无 buffer → 不相关 | |
| Incomplete settling | C_storage 经 n 次 refresh 后 V = V_top (1 − r^n)，r = C_storage / (C_dac + C_storage) | 相关；§5.3 | [Inference] |
| Temperature | Junction 型 C_p 随 T 变；cabling IR drop | 需 cryo 标定 | [Inference] |

**Two-point**：由 V(0)、V(D_max) 解 a、b，D' = round((V_target − b) / (a · LSB))。对本架构 per region 做（16 参数），自动包含 region 内的 gain 修正，但 **不能** 填补 gap（§4.5）。

### 4.4 Compensation ladder（按复杂度递增）与 cryo 现实性评估

| 级别 | 方法 | 修正什么 | 需要 | 代价 | 对 Fig. 9 gap 有效？ | Cryo 现实性 | Tag |
|---|---|---|---|---|---|---|---|
| 1 | Fixed digital offset correction | 全局 b | 1 次测量 | 一个减法 | 否 | 高 | [Inference] |
| 2 | Digital gain calibration（2-point） | 全局 a, b | 2 次测量 | 乘法或 shift-add | 否（coverage 不变 [Sim]） | 高 | [Sim] |
| 3 | Piecewise per-region gain / offset | a_k, b_k（region 内 slope、起点） | 16 次测量 | 16 个寄存器 + region 选择逻辑 | 否（同上） | 高，**推荐作为基础** | [Sim] |
| 4 | Lookup table | 任意 ε(D) | 8192 × 13 bit ≈ 13 kB + 全 code 测量 | Memory 是 power 主体 → 不可接受 | 否 | 低 | [Inference] |
| 5 | Foreground calibration（on-chip ΣΔ 测量） | 3 或 6 的参数在 cryo 下自动获取 | On-chip ADC（paper 有，~1 mW，只能间歇开） | 测量时间与功耗 | 视所配方法 | 中；只能 foreground | [Paper Sec. IV-B] |
| 6 | Architectural：intermediate range（paper） / region overlap（我们） | 增加可达电压 | 6-bit 独立 VU / VL 选择（paper 已有）；或 reference 间距 < fine span | 局部 step 2 LSB（paper）；或总 range 略缩 | **是** | 高 | [Paper Fig. 9(b)] + [Hypothesis] |
| — | Capacitor trimming | MSB weight 误差 | Trim cap + cryo 测量 + fuse | 面积小 | 否 | 可行 | [Inference] |
| — | Segmentation | 结构性降 DNL | 少量 decoder | 最低 | 否 | 推荐 | [Sim] |
| — | DEM | Mismatch → 随机 ripple | 随机化逻辑 | Ripple = qubit gate 上的噪声 | 否 | 不适合 DC bias | [Inference] |
| — | Background calibration | Drift | 常开 ADC | ~1 mW | — | 不可行 | [Paper] |

### 4.5 Fig. 9：region-dependent gain deviation + coarse switching discontinuity

**Paper 描述** [Paper Sec. IV-C]："Parasitic capacitance induces a gain error, creating a jump when switching coarse tuning regions."

**机制推导** [Inference]。Top plate 有对地 parasitic C_p；reset 相位所有 bottom plate 接 VL、top plate 接 VL；conversion 相位选中的 bottom plate 切到 VU，top plate 浮空。电荷守恒：

V_top(D) = VL + (VU − VL) · C_on(D) / (C_total + C_p) = VL + (VU − VL) · (1 − α) · D / 2^N，α = C_p / (C_total + C_p)

- Region 起点 D = 0：V = VL，被 reset 钉在 nominal。
- Region 终点：V ≈ VL + 125 mV · (1 − α)，比下一 region 起点低 125 mV · α。
- 每个 region 内 gain = 1 − α；边界处输出跳升 125 mV · α，中间电压 **没有任何 code 能到达**。

若 top plate reset 到 ground 而非 VL，同样的 C_p 只产生 **全局** gain (1 − α)，曲线连续（v2 model `reset_to="gnd"`，见 `v2_coarse_jump_compensation.png` 灰线）。jump 的必要条件是 "起点被 reset 钉住 + span 被 α 压缩"，所以它不是 global gain error。

**Fig. 9(a) 读数** [Paper-read]：code 4095 → 4096 从约 475.5 mV 跳到约 483.5 mV，jump ≈ 8 mV ≈ 65 LSB → α ≈ 6.4%，C_p ≈ 0.07 C_total。两个 region 起点都比 nominal 低约 16 mV，paper 未解释；[Hypothesis] 可能是 reference IR drop、S&H charge sharing 或 10 GΩ 表头 loading，属 region-independent 的 b。

**Paper 解法** [Paper Sec. IV-C, Fig. 9(b)]：region k 结束后先用 (VU, VL) = (625, 375)，span 250 mV，每步 2 LSB，覆盖 250 · (1 − α) ≈ 234 mV > 125 mV，走到下一 region 起点后再切到 (625, 500)。Fig. 3(b) 的 6-bit 独立 VU / VL 选择正是为此保留的自由度。

**v2 model 复现** [Sim]（α = 0.064）：jump 66 LSB = 8.1 mV；每个边界需 36 个 intermediate code；总 word 8444（paper Fig. 8 x 轴约 8600，量级一致）；coverage：无补偿 6.3% 的 13-bit target 不可达（max gap 66.5 LSB），global 2-pt 与 per-region 2-pt **完全不改变** coverage，intermediate 后 max gap 1.9 LSB、3.4% target 误差 > LSB/2 但全部 < 1 LSB（即 gap 内为 12-bit 精度，仍满足 Table I 的 250 µV）。

**代价** [Inference]：(1) gap 内 step 2 LSB，局部 12 bit，这正是 paper 留 1 bit margin 的意义；(2) code → voltage 映射非均匀，需 remap 逻辑，word 数 > 8192；(3) α 必须在 cryo 下测得，junction 型 C_p 的 α 随 T 变；(4) 最高 region 顶端 125·α ≈ 8 mV 无法到达（无下一 region 可借），实际 full scale ≈ 0.992 V。

**应该做成什么** [Hypothesis]：
- 明确实现为 **digital remapping / per-region calibration logic**：存 α（或 8 组 a_k）与 8 个 b_k，逻辑由 13-bit target 选 region 和 fine code。
- 设计阶段引入 **region overlap**：reference 间距设为 125 · (1 − α_max) 或 fine span 设计成 > 125 mV，使任何 α ≤ α_max 都不产生 gap，remap 只需选切换点。这把 workaround 变成 redundancy。
- 减小 α：top plate routing 用 metal shield 到 VL；避免 junction parasitic；增大 C_total。

---

## 5. Behavioral Model v2 — 结果（Task 5）

### 5.1 实现的 pipeline 与 flag

| Stage | 实现 | Flag / 参数 |
|---|---|---|
| Ideal capacitor DAC | `binary` / `segmented(M)` / `bwa`（split array + C_A，2-node 电荷守恒）+ dummy unit | `arch`, `m_therm` |
| Capacitor mismatch | 每 unit N(0, σ_u)，weight w 的相对误差 σ_u/√w；C_A、dummy 各一个 unit 误差 | `enable_mismatch`, `sigma_u`, `seed` |
| Parasitic / region gain | Top plate C_p → α；reset 到 VL 或 GND | `enable_parasitic`, `alpha`, `reset_to` |
| Gain / offset | 全局 a, b | `enable_gain_error`, `gain`, `enable_offset`, `offset` |
| Coarse tuning | 9-tap ladder，VU / VL 独立选择，8 region × 1024 = 8192 codes | `enable_coarse_tuning`, `n_regions` |
| S&H | DAC ↔ C_storage charge sharing（无 buffer），每 T_R 一次 | `SHParams.c_dac`, `c_storage` |
| Leakage / refresh | 线性 droop I_leak / C_storage，f_R | `i_leak`, `f_r` |
| Jump compensation | `intermediate_sequence()`（paper 方式）；`decompose()`（global / per-region 2-pt）；`coverage()` | — |
| Power | `power_scaled()`：paper Table II baseline 的一阶 scaling | `dyn_fraction_digital` |

Ideal sanity check：三种 arch 的 max|DNL|、max|INL| 均 ≤ 1e-12 LSB，Vmax = 0.999878 V = 1 V · 8191 / 8192 [Sim]。

### 5.2 假设参数（paper 未给出）

| 参数 | 取值 | 依据 | 敏感性 |
|---|---|---|---|
| C_unit | 5 fF | [Assume] 65 nm MOM 合理值 | 只影响绝对 C（S&H、power），不影响 DNL |
| σ_u | 0.003 | [Paper] 反推的 σ0/C0 | sweep 0.001–0.02（`v2_mismatch_sweep.png`） |
| α | 0.064 | [Paper-read] Fig. 9(a) | sweep 0–0.15（`v2_alpha_sweep.png`） |
| reset_to | VL | [Inference] 唯一能产生 jump 的假设 | GND 变体已对比 |
| C_storage | 1 pF | [Assume] | 与 I_leak 一起 sweep |
| C_dac | 5.12 pF | [Assume] 1024 × 5 fF | 决定 charge-sharing 系数 0.84 |
| I_leak | 1 pA | [Paper Sec. III-A] 仅说 "pA" 设计目标 | sweep 10 fA – 1 pA |

### 5.3 结果

**A. DNL vs code**（`v2_dnl_vs_code.png`）[Sim]：单次 MC（σ_u = 0.003）：plain binary max|DNL| 0.34 LSB（MSB transition 最大）；BWA 1.88 LSB，且每 32 code 出现 C_A 引起的重复 pattern；4T + 6B 0.07 LSB；BWA + coarse + parasitic 的 13-bit 曲线在每个 region 边界出现 65 LSB 的 DNL spike，其余部分呈现每 1024 code 重复的 pattern，与 paper Fig. 8(d) "repeating pattern for each 10-bit word" 定性一致。

**B. Mismatch → DNL vs Eq. (1)**（`v2_mismatch_sweep.png`，500 MC）[Sim]：

| Arch | std(DNL over codes) | mean max\|DNL\| | 99% max\|DNL\| |
|---|---|---|---|
| Plain binary | 0.009 | 0.099 | 0.249 |
| Seg 3T + 7B | 0.008 | 0.076 | 0.154 |
| Seg 4T + 6B | 0.008 | 0.063 | 0.112 |
| BWA 5 + 5 | 0.035 | **0.554** | 1.458 |
| Eq. (1) [Paper] | — | **0.543** | — |
| Paper measured σ_D | — | 0.495 | — |

BWA 模型在整个 σ_u 范围内与 Eq. (1) 的 2^(3N/4) · σ0/C0 吻合（< 2%），说明 v2 的 BWA 电荷守恒模型与 paper 引用的 Saberi 推导一致，paper 由 0.495 LSB 反推 σ0 = 0.003 的过程可复现。注意 Eq. (1) 描述的是 worst-code（MSB transition）的 σ，不是全 code 的 std。[Inference] Paper Fig. 8(f) 的 DNL 在所有 code 上呈白噪声状分布，而 mismatch 造成的 DNL 应集中在 binary 边界，所以实测 σ_D 很可能包含 refresh / 测量噪声，σ0 = 0.003 应视为 **上界**。要在 13-bit 系统中把 fine DAC 的 max|DNL| 压在 0.5 LSB 以下：BWA 需 σ_u ≲ 0.3%，plain binary ≲ 1.5%，4T + 6B ≲ 2.5%。

**C. S&H refresh / leakage**（`v2_sh_refresh_leakage.png`）[Sim]，假设 C_storage = 1 pF、C_dac = 5.12 pF、I_leak = 1 pA：

| f_R | Droop / period | 充电到 1 LSB 内所需 refresh 次数（charge-sharing 系数 0.84） | 对应 settling 时间 |
|---|---|---|---|
| 390 kHz | 2.6 µV | ~5 | ~13 µs |
| 3.9 kHz | 256 µV（> 2 LSB） | ~5 | ~1.3 ms |

Power–droop tradeoff：droop ∝ I_leak / (C_storage · f_R)，power 的 dynamic 部分 ∝ f_R。要在 3.9 kHz 下满足 paper 的 "lower tens of µV"（取 20 µV），需 I_leak / C_storage < 0.08 A/F，例如 78 fA @ 1 pF 或 0.8 pA @ 10 pF。[Inference] Paper 能在 3.9 kHz 工作，意味着 cryo 下的实际 leakage 远低于 1 pA 的设计目标，或 C_storage 在 10 pF 量级；这是 transistor-level 阶段必须提取的量。

**D. Coarse-region jump 与补偿**（`v2_coarse_jump_compensation.png`、`v2_jump_global_vs_region_cal.png`、`v2_alpha_sweep.png`）[Sim]：见 §4.5。Global 2-pt 拟合得 a = 0.999、b = −3.5 mV，残差 ε(D) 为 ±35 LSB 的锯齿；per-region 2-pt 使 region 内残差为零，但 target-to-nearest-achievable 误差在每个边界仍为 ~33 LSB；intermediate steps 将其降到 < 1 LSB。Jump 与 α 线性：每 1% α 约 10 LSB、约 6 个 intermediate code / boundary。

### 5.4 v2 尚未包含

Switch Ron / settling、charge injection、kT/C 与 refresh ripple 噪声、α 的 Monte Carlo、S&H 反向对 DAC top plate 的 charge sharing、cryo parameter layer（目前只是参数 sweep）、per-region overlap 方案的实现（列为下一步）。

---

## 6. Power Analysis（Task 6）

### 6.1 Baseline 与 budget [Paper Table II, Sec. II]

| Block | Paper @ 3.9 kHz | 占比 | 一阶 scaling（[Assume]） |
|---|---|---|---|
| DAC core (Sw & MUX) | 77 nW | 0.3% | ∝ f_conv · C_total · ΔV²，ΔV = 125 mV（已含 1/64） |
| DAC reference voltages | 3 nW | ~0 | 外部，常数 |
| DAC digital (memory & logic) | 21 µW | 82.7% | static + dynamic ∝ f_R；split 未知，sweep 0.1 / 0.5 / 0.9 |
| DAC total | 21.1 µW（2.63 µW/ch） | | |
| Clock buffer | 4.3 µW | 16.9% | ∝ f_clk |
| **Total** | **25.4 µW（3.18 µW/ch）** | 100% | |
| Cooling budget @ 100 mK | ~400 µW | | 一个 8-ch DAC 占 6.4%；约 15 个 DAC（~120 ch）耗尽 budget [Inference]；paper 未在 100 mK 测量 |

### 6.2 随 f_R 的 scaling [Sim, `power_scaled()`，假设 dynamic 部分 ∝ f_R]

| f_R | Digital dyn. fraction 0.1 | 0.5 | 0.9 |
|---|---|---|---|
| 3.9 kHz | 25.4 µW | 25.4 µW | 25.4 µW |
| 39 kHz | 84 µW | 159 µW | 235 µW |
| 390 kHz | 667 µW | 1.50 mW | 2.33 mW |

无论 digital 的 dynamic 占比如何，390 kHz 都超出 400 µW budget；这与 paper 选择 3.9 kHz 作为 sweet spot 一致 [Inference]。Paper 没有给出 390 kHz 的功耗，上表是外推。

### 6.3 各 block 随 architecture 的变化 [Inference]

| Block | Binary (plain) | Binary + C_A (paper) | Thermometer | Segmented 4T+6B | 备注 |
|---|---|---|---|---|---|
| Capacitor switching | C_total 1024 units：5 pF × (0.125)² × 31 kHz ≈ 2.4 nW | ~65 units：≈ 0.15 nW | 同 plain | 同 plain | 都远小于 77 nW core；core 主要是 switch driver 与 MUX |
| Switch drivers | 10 个，尺寸 ∝ weight，总 gate cap ≈ 常数 | 同 | 1023 个 min-size：~1023 × 2 fF × 1.44 V² × 31 kHz ≈ 90 nW | 21 个 | Thermometer 的 driver 功耗仍在 100 nW 量级 |
| Decoder / control logic | 0 | 0 | ~9k gate：每次 conversion 翻转 ~µW 级（65 nm，31 kHz） | 45 gate：~nW | 只有一份（DAC 共享） |
| Per-element latch（若 glitch-free 更新需要） | 10 | 10 | 1023 latch：cryo 下 leakage 极小，clock load ~100 nW | 21 | 主要代价是面积 / routing |
| Memory | 8 ch × 13 b + coarse | 同 | **同**（存 binary，conversion 时解码） | 同 | 与 coding 无关 |
| Clocking | 4.3 µW ∝ f_clk | 同 | 同 | 同 | 与 coding 无关 |
| Reference generation | 3 nW | 同 | 同 | 同 | 外部 |
| S&H refresh | ∝ f_R × N_ch | 同 | 同 | 同 | 与 coding 无关 |

**结论**：digital power 的主体（memory、timing、clock）与 coding 无关；segmented 的增量在 nW 级；full thermometer 的增量估计 ~1 µW 级（约 +5%），但换来的只有 DNL，没有 INL，且面积 / routing 100×。真正能降功耗的杠杆是 **降低 f_R（受 leakage 限制）、共享 timing、减少 memory 位宽和 clock buffer**，而不是 coding。

---

## 7. Design Implications for Our DAC

| Topic | Problem | Paper Solution | Possible Improvement | Impact on Our Design | Tag |
|---|---|---|---|---|---|
| Topology | RT DAC 依赖 transistor 参数 | Charge-redistribution，无 static power | 保持 | 基线 architecture | [Paper] + [Inference] |
| Resolution vs mismatch | Cap mismatch 限 ~10 bit；BWA sensitivity 2^(3N/4) | 10-bit BWA + 3-bit coarse | 去掉 C_A（sensitivity ↓ ~9×）+ segmented 4T+6B | Fine DAC 候选：plain segmented | [Sim] + [Hypothesis] |
| Coarse tuning | 13 bit 且低 power | 8 external refs，6-bit VU / VL 选择 | 保留；reference 间距留 overlap | 确定 reference 线数与精度预算 | [Paper] + [Hypothesis] |
| Fig. 9 jump | C_p → region gain 1 − α → gap | 250-mV intermediate span | Region overlap + per-region (a_k, b_k) remap；减小 C_p | Remap 逻辑进 digital spec | [Sim] + [Hypothesis] |
| Offset | Reference / injection 造成 per-region offset | 未讨论 | Per-region one-point | Calibration 寄存器 | [Inference] |
| Output stage | Buffer 在 cryo clipping、耗电 | 无 buffer，C_storage 逐步充电 | 保留；量化 settling 次数（~5） | Settling 时间 = 5 × T_R | [Paper] + [Sim] |
| Leakage / refresh | S&H droop | Refresh，3.9 kHz sweet spot | 可编程 f_R；cryo leakage 数据 | I_leak / C_storage 是关键提取量 | [Paper] + [Sim] |
| Power | Digital 99.5% | 指出随 node scaling | 降 f_R、共享 timing、减 memory | Coding 不是功耗杠杆 | [Paper] + [Inference] |
| Coding | Binary DNL 在 major carry 最差 | Binary（BWA） | Segmented 4T+6B | 候选方案 | [Sim] |
| Calibration 测量 | Cryo 下无法用 RT 仪器直接观察 | On-chip ΣΔ + WC（测试用） | 复用为 foreground calibration | 预留测量路径 | [Paper] + [Hypothesis] |
| Model validity | PDK 在 4 K 无效 | 实测验证 | Cryo model 或人工 corner；参数不敏感 topology | Corner 策略 | [Ext] + [Hypothesis] |

**最终问题的回答**："Given the constraints of cryogenic CMOS, what Bias-DAC architecture should we actually implement later at transistor level, and what are the dominant errors that the design must compensate?"

- **Architecture** [Hypothesis]：charge-redistribution 10-bit fine DAC（plain segmented 4T + 6B，unit cap ~5 fF 量级，C_total ~5 pF）+ 3-bit coarse external reference（VU / VL 独立选择，间距留 overlap）+ 1:8 DEMUX S&H（无 buffer）+ 可编程 refresh（3.9 kHz 附近）。
- **Dominant errors**（按对 13-bit 精度的影响排序）[Sim] + [Inference]：(1) top-plate parasitic α 引起的 region 边界 gap（65 LSB 量级，必须 architectural / remap 补偿）；(2) per-region reference offset / gain（16 参数 calibration）；(3) capacitor mismatch（BWA 时 0.5 LSB，plain segmented 时 0.06 LSB，结构性解决）；(4) S&H leakage droop 与 refresh ripple（决定 f_R 与 C_storage）；(5) switch charge injection（进入 per-region offset）。

---

## 8. Next Behavioral Model Updates（v3）

| 优先级 | Module | 内容 | 状态 |
|---|---|---|---|
| 已完成 (v2) | Error decomposition, coding arch, BWA, mismatch MC, parasitic + coarse tuning, intermediate remap, S&H charge sharing, leakage / refresh, power scaling | — | ✅ |
| 1 | Region-overlap 方案 | Reference 间距 / fine span 可配置，per-region (a_k, b_k) remap，coverage 对比 paper 方式 | 待做 |
| 1 | Per-region offset / gain 注入 | b_k、a_k 随机化（reference IR drop、injection） | 待做 |
| 2 | Switch 模型 | Ron(VGS, T) → settling 时间 vs conversion slot；charge injection ΔQ / C | 待做 |
| 2 | Noise | kT/C、refresh ripple 频谱 | 待做 |
| 3 | Cryogenic parameter layer | `temp_profile`：σ_u_scale、ron_scale、leak_scale、offset_shift、α(T) | 待做 |
| 3 | Monte Carlo on α 与 reference 误差 | 分布而非点值 | 待做 |

---

## 9. Implications for Transistor-Level Implementation（Cadence 阶段需验证）

1. **MOM unit-cap mismatch σ_u vs 尺寸**：从 PDK 提取；目标 plain segmented 4T+6B 下 σ_u ≤ 1%（max|DNL| < 0.3 LSB 余量），BWA 需 ≤ 0.3%。
2. **Top-plate parasitic C_p / α**：post-layout 提取；目标 α < 2%（jump < 20 LSB）；确认 C_p 为 metal 型而非 junction 型（温度稳定）。
3. **Bottom-plate switch**：在 VL / VU ∈ [0, 1 V] 电平、VTH +150 mV corner 下的 Ron 与 on/off 余量；TG vs bootstrapped；Ron · C_total 相对 conversion slot（8 × f_R）的 settling。
4. **Reset switch charge injection**：对 C_total 的 ΔV，是否 code / region 相关。
5. **DEMUX / S&H switch off-state leakage** 与 C_storage：决定 I_leak / C_storage，进而决定 f_R；目标 droop < 20 µV @ 3.9 kHz。
6. **C_storage 与 series R**：charge-sharing 系数、settling 次数、qubit gate 端 ripple。
7. **Reference MUX**：9 tap、6-bit 选择的 Ron、IR drop、decoupling；region 起点误差 b_k 预算。
8. **Digital**：memory 位宽 × channel、timing generator、clock buffer 在 1.2 V 下的功耗；2.5 V supply 的用途（Table III，未说明，可能是 I/O 或 switch driver）[Open]。
9. **Cryo corner 策略**：cryo compact model 可得性；否则用 VTH +150 mV、SS 饱和、mobility ×1.5 的人工 corner 做 robustness。
10. **Remap / calibration 逻辑**：per-region (a_k, b_k) 寄存器 + region 选择 + intermediate / overlap 切换的 gate count 与功耗。
11. **Noise**：kT/C（cryo 下 9 µV @ 1 pF）与 refresh ripple 对 qubit 的影响。

---

## 10. Open Questions

1. Target 温度：6 K 还是 100 mK？决定 PDK 策略与 self-heating 假设。
2. Channel 数与允许的 settling 时间（决定 f_R 与 C_storage）。
3. External reference 是否允许；若不允许，需要 cryo on-chip reference。
4. PDK 的 MOM mismatch 数据（σ_u vs 面积）。
5. Cryo compact model 可用性。
6. α 在 RT 与 cryo 是否相同（决定标定温度）。
7. Fig. 8(d) 中 390 kHz 的周期性 DNL pattern 成因。
8. Paper digital 21 µW 的 static / dynamic 构成。
9. DEMUX / S&H switch 的 charge injection 在 cryo 下的量级。
10. Qubit 对 refresh ripple 的容忍度。
11. Paper 中 2.5 V supply 的用途。

---

## References

Reference paper（本地 `paper_for_reference/`）：
- P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE SSC-L, vol. 3, pp. 218–221, 2020. DOI 10.1109/LSSC.2020.3011576.

Paper 引用且本周用到：
- [6] M. Saberi et al., "Analysis of power consumption and linearity in capacitive DACs used in SAR ADCs," IEEE TCAS-I, vol. 58, no. 8, 2011（Eq. (1) 来源；本地无 PDF，推导未核对，但 v2 model 数值复现）。
- [3] R. M. Incandela et al., "Characterization and compact modeling of nanometer CMOS transistors at deep-cryogenic temperatures," IEEE JEDS, vol. 6, 2018. https://www.researchgate.net/publication/320651319
- [5] B. Patra et al., "Characterization and analysis of on-chip microwave passive components at cryogenic temperatures," IEEE JEDS, vol. 8, 2020. https://arxiv.org/abs/1911.13084

External（仅由 web search 摘要核对，未读全文）：
- P. A. 't Hart et al., "Characterization and Modeling of Mismatch in Cryo-CMOS," IEEE JEDS, 2020. https://ieeexplore.ieee.org/document/9015956
- P. A. 't Hart et al., "Subthreshold Mismatch in Nanometer CMOS at Cryogenic Temperatures," IEEE JEDS, 2020. https://ieeexplore.ieee.org/document/9072133
- B. Dierickx et al., "Effect of deep cryogenic temperature on SOI CMOS mismatch," Cryogenics, 2014. https://www.sciencedirect.com/science/article/abs/pii/S0011227514000873
- H. Homulle et al., "Deep-Cryogenic Voltage References in 40-nm CMOS," IEEE JSSC, 2018. https://ieeexplore.ieee.org/document/8490692
- A. Beckers et al., "Cryogenic MOSFET Threshold Voltage Model," 2019. https://arxiv.org/pdf/1904.09911
- "Cryogenic Characterization of Low-Frequency Noise in 40-nm CMOS," 2024. https://arxiv.org/pdf/2405.17685
