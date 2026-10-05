# Bias Voltage DAC Specification Draft v0

October 4, 2026 · Revised against Specification_Setting_Guide.docx · Mentor discussion only

## Scope and status

Primary priorities: P1 DC accuracy; P2 power per channel; P3 temperature robustness. Working use case is slow programmable bias into a high-impedance load. Quantum-dot gate bias is the literature context; the actual collaborator Sigma-Delta/analog bias interface must be confirmed. The guide and weekly template remain unchanged.

Current evidence: 3-bit TSMC65 CDAC, six TG reference switches, ideal reset and references, behavioral control, TT at 27 C, no added load. Ascending full-code scan gives displayed settled errors from -8.4 to +3.9 uV; this is not formal INL/DNL or cryogenic accuracy. See [Week 6 report](../reports/weekly%20task/BiasDAC_WeeklyTask_Week06_2026-10-04.docx).

## Literature grounded worksheet

| Metric | Priority | Literature evidence | Proposed range or condition | Justification and limitation |
| --- | --- | --- | --- | --- |
| Resolution and DC accuracy | P1 | 11-15 nominal bits across R09/R01/R04; 57.1-122.1 uV steps in R04/R01, with different spans. | Explore 11-13 bits; 12-bit design point (244.14 uV/LSB at 1 V). Maximum /INL/ budget: 0.5-2 LSB; /DNL/ <=0.5 LSB goal, with DNL > -1 mandatory. | Lower-bit CDAC scope; not an ENOB claim. Calibration and system error allowance need approval. [R01,R09,R04] |
| Power per channel | P2 | R01: 3.18 uW/ch including clock buffer; R09: 5.8 uW/DAC at 3.9 kHz. R04: 157 uW for a shared, heavily loaded DAC. | Explore a 3-10 uW/ch budget at 1-4 kHz; provisional 5 uW/ch design point. Include allocated reference, control and buffer power. | Low heat is a primary cryogenic constraint; published accounting boundaries differ. No current measured power. [R01,R09,R04] |
| Temperature robustness | P3 | Core comparison cryogenic points: 4.2, 6 and 8 K. R09 and R04 provide room/cold comparisons. | Characterization envelope 4.2-300 K. Retain monotonicity and approved DC limits at every supported point; allow 1-2x RT settling time as a provisional ceiling range. | A proposed validation requirement, not proof of continuous-range operation. Requires validated models or measurement. [R09,R04,R11] |
| Reference and supply | S | R01: 1 V output span; R04: 3 V span. Different supply domains. | Current condition: VDD=1 V; Vu/Vl=1/0 V. Explore 0.9-1.1 V supply only within PDK ratings; final absolute range TBD. | Bias-window and load are system decisions. 1 V span is not a universal qubit requirement. [R01,R04] |
| Settling and update | S | R09: 3.9 kHz updates. R04: 62 kHz integration clock and about 20 ms gear-shift ramp; these are different metrics. | Explore 1-4 kupdate/s; settling budget 10-100 us to +/-0.25 LSB, checked at actual load. | Timing assumption for slow bias; not derived from a common measured settling benchmark. [R09,R04] |
| Hold drift and refresh | S | R02: 125 uV/s stopped-clock drift, about 100 uVpp refresh ripple, 3.894 kHz refresh; R09: clear temperature-dependent retention. | Explore 0.1-0.25 LSB drift allowance over 1 ms (24-61 uV at 12 bit); sweep refresh 10 Hz-4 kHz. | Separate leakage slope from turn-off step and refresh ripple. Need load and leakage specification. [R02,R09] |
| Noise and reference stability | S | R04: 192 to 188 uVrms from 300 to 4.2 K; R01 does not establish a comparable integrated noise limit. | Exploratory noise allocation: 0.1-0.25 LSB rms (24-61 uV at 12 bit), provisional band 1 Hz-10 kHz. Reference error budget TBD. | Band and weighting need system approval; not comparable to R04 without matched integration conditions. [R04,R18] |
| Output load and disturbance | S | R04 drives >480 pF; current unbuffered array is about 0.885 pF total and has no added load. | Sweep external C=10 fF-10 pF and leakage=10 fA-10 pA. Glitch peak/area and allowed quiet time: TBD. | Exploration ranges, not drive guarantees. Loading changes charge-sharing gain as well as speed. |
| Area and capacitor choice | S | R09: 0.008 mm2 core, 6 fF MOM units. R01: 0.14 mm2 including eight S&H outputs; R04: 0.076 mm2 core. | Study 0.008-0.14 mm2 literature envelope; no area acceptance limit yet. Keep MIM baseline; compare one legal MOM option. | Areas have different boundaries. Need matching, density, metal-stack and PEX evidence before choosing. [R09,R01,R04,R10] |
| FoM and effective resolution | S | No universal bias-DAC FoM. Derived energy examples appear in the comparison section. | At 1 kHz, 3-10 uW/ch implies 3-10 nJ/channel/update, if all energy is assigned to each update. No ENOB-normalized target yet. | Report idle power and event definition. Nominal bits cannot substitute for measured effective resolution. |

All provisional ceilings need system approval. The guide asks for ranges supported by independent literature; the unresolved rows above explicitly distinguish evidence from assumptions rather than pretending the evidence gaps are closed. Fixed bench settings are not final application specifications.

At 12 bits and a 1 V reference span: LSB = 244.140625 uV; 0.1 LSB = 24.414 uV; 0.25 LSB = 61.035 uV; maximum code output = 4095/4096 V. At 11/13 bits, LSB = 488.281/122.070 uV. No total-error claim until static, dynamic, reference, noise and drift allocations are combined.

## Three independent studies and temperature trends

| Study | Architecture | Performance | Power and area | Temperature interpretation |
| --- | --- | --- | --- | --- |
| R01 Vliex 2020 | 65 nm; coarse/fine CDAC with 8 S&H outputs | 6 K; 13-bit code; 1 V span | 3.18 uW/ch with clock buffer; 3.9 kHz refresh | No complete like-for-like RT/cold DAC metric set extracted; do not infer degradation from the op-amp measurements. |
| R09 Miki 2022 | 40 nm; 11-bit split CDAC; 6 fF MOM | 300 K and 8 K; INL about +/-2 LSB; DNL -2 to +0.5 LSB after calibration | 5.8 uW at 3.9 kHz; 0.008 mm2 core | Similar plotted RT/cold linearity; retention improves on cooling. DNL does not demonstrate monotonicity. |
| R04 Enthoven 2022 | 22 nm FinFET; integrating DAC; >480 pF measured load | 300 to 4.2 K: step 68.3 to 57.1 uV; INL 12.6 to 36.5 LSB; DNL 0.6 to 0.8 LSB | 138 to 157 uW; 62 kHz clock; 0.076 mm2 core | Cold/RT ratios: power 1.14, step 0.84, INL 2.90, DNL 1.33. Noise 192 to 188 uVrms. Do not treat small steps as equal accuracy. |

R02 is the same DAC research line as R01 and is supplemental, not an independent comparison. R04 and its journal expansion R05 are likewise not independent designs. Current evidence does not justify a continuous cryogenic operating-range guarantee.

## Figure of merit

Use E = P/f only with an explicit event and accounting boundary. R01: 3.18 uW/ch / 3.9 kHz = 0.815 nJ/channel/refresh, including clock buffer but excluding external reference generation. R09: 5.8 uW / 3.9 kHz = 1.49 nJ/DAC/update. R04: 157 uW / 62 kHz = 2.53 nJ/integration cycle at 4.2 K, not per complete ramp or channel refresh. These are not directly interchangeable FoMs. No ENOB-normalized FoM is claimed from nominal bits.

## Verification matrix

| Check | Simulation | Evidence |
| --- | --- | --- |
| Static transfer | Sweep every code in both directions; sample after a fixed settling interval; repeat representative codes from multiple starting states. | Report raw error, endpoint-corrected INL/DNL, offset, gain and minimum code step. No mismatch-yield claim from nominal data. |
| Switch and transient behavior | Ron versus signal voltage; major-carry and full-scale transitions; sweep edge time, skew and non-overlap. | Compare settling to a stated band. Report glitch peak/area separately and confirm timestep convergence before quoting peaks. |
| Retention and noise | Hold worst-case codes with leakage/load sweeps; isolate initial injection from subsequent drift; evaluate sampled and reference noise. | Measure droop over the agreed hold interval; state RMS integration band and analysis method. |
| Power and load | Integrate energy at every physical supply/reference/control port; separate idle/update; sweep Cload and reference impedance. | Behavioral-driver output energy is load-delivered energy, not a model of decoder internal power. Recheck output range under load. |
| Robustness | Supported PVT; enabled MOS/cap mismatch Monte Carlo; PEX; cryogenic model/measurement matrix when available. | Record model range, sample count, voltage stress and calibration. Temperature extrapolation alone is not validation. |

## Physical constraints and rationale

The resolution band selects lower-cost CDAC scope from an 11-15-bit independent literature set; it is not a promise to reproduce the strongest metrics of different chips simultaneously. R09 measured DNL down to -2 LSB, so it is not a monotonicity benchmark. R04 Table 1 shows power +13.8%, step -16.4%, noise -2.1%, INL +189.7%, and DNL +33.3% from 300 to 4.2 K. A universal 10% temperature-degradation allowance would be unsupported.

R02 reports about 125 uV/s drift with the refresh clock stopped and about 100 uVpp ripple while refreshing. These are distinct quantities. The 10-100 us settling, 24-61 uV noise/drift budgets and 1 ms hold are stated engineering assumptions for discussion, not copied system requirements.

Ron must follow a settling budget: Req <= t_settle/[Ceff*ln(deltaV/error)] in a first-order model. With floating top plate and the other bottom plates AC grounded, one branch sees Ceff = Cb*(Ctotal-Cb)/Ctotal. The current MSB example is about 221 fF, not the full 885 fF. Multi-bit switching needs the complete transient circuit.

Droop approximately equals Ileak*Thold/Chold. A 1 pF hold node with a 61 uV/1 ms budget permits about 61 fA total leakage. Adding 1 pF to an ideal floating 885 fF top plate gives a simple charge-sharing gain factor of about 0.469; it cannot be treated only as extra settling delay.

Keep the current MIM baseline until a legal MOM PCell is compared at equal capacitance. Evaluate metal stack, minimum geometry, matching, parasitic terminals, voltage coefficient, density and DRC/PEX. R10's 40 nm MOM changed 191 to 197 fF between room temperature and 4 K; this is not TSMC65 mismatch evidence.

Behavioral-driver output energy counts energy delivered to its load; it does not include a physical decoder's internal consumption. Include the reference, control and any buffer in the eventual system power budget.

## Mentor decisions

1. Actual destination: quantum-dot gate or collaborator analog/Delta-Sigma bias node; required voltage and load.
2. Resolution versus total accuracy, calibration and allowable update disturbance.
3. Temperature envelope, model validity, measurement resources and required semester deliverable.
4. Per-channel/total power boundary, channel count and capacitor/MOS process options.

## Complete references used in this revision

[R01] P. Vliex et al.. **Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications**. IEEE Solid-State Circuits Letters, vol. 3, pp. 218-221, 2020. DOI: [10.1109/LSSC.2020.3011576](https://doi.org/10.1109/LSSC.2020.3011576). [Open full text](https://juser.fz-juelich.de/record/888069/files/FINAL%20VERSION_QC.pdf). Evidence: Sections IV and V; Tables I and II.

[R09] T. Miki, R. Takahashi, and M. Nagata. **An 11-bit 0.008 mm2 charge-redistribution digital-to-analog converter operating at cryogenic temperature for large-scale qubit arrays**. IEICE Electronics Express, vol. 19, no. 8, article 20220099, 2022. DOI: [10.1587/elex.19.20220099](https://doi.org/10.1587/elex.19.20220099). [Open full text](https://da.lib.kobe-u.ac.jp/da/kernel/90009517/90009517.pdf). Evidence: Section 4; Figures 7-9; Table I.

[R04] L. Enthoven, J. van Staveren, J. Gong, M. Babaie, and F. Sebastiano. **A 3V 15b 157uW Cryo-CMOS DAC for Multiplexed Spin-Qubit Biasing**. IEEE Symposium on VLSI Technology and Circuits, pp. 228-229, 2022. DOI: [10.1109/VLSITechnologyandCir46769.2022.9830309](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830309). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/154843798/A_3V_15b_157W_Cryo_CMOS_DAC_for_Multiplexed_Spin_Qubit_Biasing.pdf). Evidence: Page 229, Table 1 and Figure 6.

[R02] R. Otten et al.. **Qubit Bias using a CMOS DAC at mK Temperatures**. IEEE ICECS, 2022. DOI: [10.1109/ICECS202256217.2022.9971043](https://doi.org/10.1109/ICECS202256217.2022.9971043). [Open full text](https://confcats-event-sessions.s3.amazonaws.com/icecs22/papers/6353.pdf). Evidence: Sections II and III; Table I.

[R10] B. Patra et al.. **Characterization and Analysis of On-Chip Microwave Passive Components at Cryogenic Temperatures**. IEEE Journal of the Electron Devices Society, vol. 8, pp. 448-456, 2020. DOI: [10.1109/JEDS.2020.2986722](https://doi.org/10.1109/JEDS.2020.2986722). [Open full text](https://repository.tudelft.nl/file/File_6d4cc63f-f0aa-4ad1-8d39-9942b3c07726). Evidence: Section III and Table 1.

[R11] P. A. t Hart et al.. **Characterization and Modeling of Mismatch in Cryo-CMOS**. IEEE Journal of the Electron Devices Society, vol. 8, pp. 263-273, 2020. DOI: [10.1109/JEDS.2020.2976546](https://doi.org/10.1109/JEDS.2020.2976546). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/71537207/09015956.pdf). Evidence: Sections IV and V.

[R18] J. van Staveren et al.. **Cryo-CMOS Voltage References for the Ultrawide Temperature Range From 300 K Down to 4.2 K**. IEEE Journal of Solid-State Circuits, vol. 59, no. 9, pp. 2884-2894, 2024. DOI: [10.1109/JSSC.2024.3378768](https://doi.org/10.1109/JSSC.2024.3378768). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/230892395/Cryo-CMOS_Voltage_References_for_the_Ultrawide_Temperature_Range_From_300_K_Down_to_4.2_K.pdf). Evidence: Sections IV and V.

The [full literature review](../cryogenic_bias_dac_literature_review_2026-10-04.md) contains all 24 screened records and reading status. The core assigned/reference-paper identity should be confirmed with the mentor.

## Full text requests

- **Priority 1: SiGe Qubit Biasing with a Cryogenic CMOS DAC at mK Temperature**. L. Schreckenberg et al., ESSCIRC 2023, pp. 161-164. DOI: [10.1109/ESSCIRC59616.2023.10268801](https://doi.org/10.1109/ESSCIRC59616.2023.10268801). Confirm actual voltage window, drift conditions, local temperature and projected versus measured power.

- **Priority 1: Xiling: Cryo-CMOS Manipulator Using Dual 18-bit R-2R DACs for Single-Electron Transistor at 60 mK**. Y. Li et al., IEEE JSSC, 2026. DOI: [10.1109/JSSC.2026.3671795](https://doi.org/10.1109/JSSC.2026.3671795). Check full noise bandwidth, calibration, load and measured RT-to-cold trends. Alternative: ISSCC 2025 DOI 10.1109/ISSCC49661.2025.10904579.

- **Priority 2: Cryogenic Current Steering DAC With Mitigated Variability**. M. E. P. V. Zurita et al., IEEE SSC-L, vol. 3, pp. 254-257, 2020. DOI: [10.1109/LSSC.2020.3013443](https://doi.org/10.1109/LSSC.2020.3013443). Separate measured and expected performance; compare narrow-range fine biasing with this 1 V-span CDAC.
