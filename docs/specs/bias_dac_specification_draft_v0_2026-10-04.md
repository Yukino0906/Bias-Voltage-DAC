# Bias Voltage DAC Specification Draft v0 revision 2

October 4, 2026 | Full-text update | Working design baseline from Week 7

## Design policy

Starting in Week 7, use these specifications to select circuit parameters and plan simulations unless a later project decision changes them. The working points below are provisional internal design targets selected from the discussion ranges; they are not mentor-approved system requirements or achieved performance.

Use this document for circuit sizing and simulation decisions by default from Week 7 unless the user or mentor changes the direction. Record each change against a metric ID, conditions, target and result. Keep the existing 3-bit regression; evaluate 8-bit scaling before committing to a 12-bit architecture.

## Current evidence

3-bit TSMC65 CDAC; six TG reference switches, ideal reset/references, behavioral driver. TT 27 C, 1 V supply/reference span, no added load. Ascending 000-111 marker error: -8.4 to +3.9 uV. This is not formal INL/DNL, noise, mismatch or cryogenic validation. Reset implementation remains unfinished.

## Specification worksheet

| Metric | Priority | Literature evidence | Range and working point | Rationale and limits |
| --- | --- | --- | --- | --- |
| Resolution and DC accuracy | P1 | Broad architecture set: 8-18 nominal bits [R15,R09,R01,R04,R24J]. Steps are not directly comparable across spans. | CDAC scope 11-13 bits; work at 12 bits / 1 V. Max &#124;INL&#124; ceiling range 0.5-2 LSB; work at <=1 LSB. &#124;DNL&#124; <=0.5 LSB goal; DNL > -1 required. | A manageable CDAC design objective, not the entire literature range or a 12-bit ENOB claim. At 1 V, 10 uV steps require at least 17 bits; application choice remains open. |
| Power per channel | P2 | R01 3.18 uW/ch; R09 5.8 uW/DAC. R03 about 20 uW/8 outputs, or 2.5 uW/output by allocation. R24J about 60 uW/dual-DAC chip in DC mode. | Budget range 3-10 uW/ch at 1-4 kupdate/s; working ceiling 5 uW/ch at 1 kupdate/s. Include allocated reference, control and buffer power. | Low heat motivates the goal. Different circuit/accounting boundaries prevent direct ranking. Partial schematic energy cannot establish total power. |
| Temperature robustness | P3 | R04 INL grows 2.9x on cooling. R15 max INL 0.63 to 2.96 LSB (300 to 4.2 K). R24J calibration changes with temperature. | Intended envelope 4.2-300 K; validate only supported model/measurement points. Same accuracy/power limits; 1-2x RT settling ceiling range, working cap 2x (20 us). | No mK commitment or blanket percentage allowance. Calibration policy must accompany each result. Temperature extrapolation is not validation. |
| Reference and supply | S | R01/R03 1 V span; R24J 1.2 V span. R03 supply rails are 1.2/2.5 V, not its output span. | Working bench VDD=1 V; Vu/Vl=1/0 V. Supply exploration 0.9-1.1 V only inside PDK ratings; output polarity/span pending interface agreement. | Preserve the working TSMC65 bench. Literature supply domains do not authorize overvoltage on our devices. |
| Settling and update | S | R09 3.9 kHz update; R03 3.8941 kHz/channel refresh with 10 MHz internal clock. R15 100 MS/s is estimated. | Range 1-4 kupdate/s and 10-100 us settling. Work at 1 kupdate/s and <=10 us to +/-0.25 LSB12 (+/-61.0 uV) at RT. | Engineering timing budget for slow bias. Start timing at the update request, include dead time, and require the result to remain in band through the valid window. |
| Hold drift and refresh | S | R03 0.96 uV/s clock-off drift; 275 uVpp refresh ripple at 3.8941 kHz. R02 125 uV/s in a different setup. | Drift allowance 0.1-0.25 LSB12 over 1 ms; work at <=61.0 uV/1 ms. Explore refresh 0.1 Hz-4 kHz; do not assume low-rate operation passes. | Separate injection, ripple and long-term slope. R03 low-rate/pW scaling is extrapolated, not a measured multichannel operating result. |
| Noise and reference stability | S | R24J zero-code noise: 8.6/2.6/3.8 uVrms at 300 K/4 K/60 mK over 1 Hz-50 kHz; acquisition conditions differ. | Range 0.1-0.25 LSB12 rms; working ceiling 61.0 uVrms over 1 Hz-10 kHz. Also report 1 Hz-50 kHz for comparison. Reference budget not yet allocated. | The working limit is an engineering allocation. Evaluate multiple codes, include reference noise and sampled kT/C; zero-code noise alone is insufficient. |
| Load and switching disturbance | S | R04 >480 pF measured load; R24J about 200 pF cable load slows modulation. Present CDAC total C is about 0.885 pF. | Load probes: added C=0,10 fF,100 fF,1 pF,10 pF; leakage=10 fA-10 pA. During valid hold window, explore ripple <=24-61 uVpp; work at <=61 uVpp. | 0 added C is a regression control, not a load specification. Peak/area during the blanking window are measured separately; device stress limits still apply. |
| Area and capacitor choice | S | Comparable CDAC core/block areas span 0.008-0.14 mm2 [R09,R01]; R24J reports 0.377 mm2/ch for R-2R. | No area acceptance ceiling yet. Keep MIM baseline; compare one legal MOM option at equal capacitance, with matching and parasitics. | Area boundaries and architectures differ. The three added papers do not prove TSMC65 MOM is superior to MIM. |
| FoM and effective resolution | S | No universal bias-DAC FoM; compare only stated energy events and boundaries. | At 1 kHz, budget 3-10 nJ/ch/update; working ceiling 5 nJ/ch/update from 5 uW. Report idle power separately; no ENOB-normalized target. | P/f is an amortized energy allocation, not necessarily the incremental switching energy. Nominal bits cannot stand in for effective resolution. |

At 12 bits and 1 V: LSB12=244.140625 uV; 0.1 LSB12=24.414 uV; 0.25 LSB12=61.035 uV; maximum output=4095/4096 V. Use native LSB for 3-bit/8-bit INL and DNL. Future 12-bit absolute error allocations can be tested on a lower-bit core but do not demonstrate its resolution.

These are metric-specific engineering screens, not a closed total-error budget. Agree load, voltage span/polarity, reference error, calibration and application temperature with the mentor. Update the working point and recalculate downstream budgets when any of these change.

## Core literature and temperature trends

| Study | Architecture | Performance | Power and area | Temperature interpretation |
| --- | --- | --- | --- | --- |
| R01 Vliex 2020 | 65 nm; coarse/fine CDAC with 8 S&H outputs | 6 K; 13-bit code; 1 V span | 3.18 uW/ch with clock buffer; 3.9 kHz refresh | No complete like-for-like RT/cold DAC metric set extracted; do not infer degradation from the op-amp measurements. |
| R09 Miki 2022 | 40 nm; 11-bit split CDAC; 6 fF MOM | 300 K and 8 K; INL about +/-2 LSB; DNL -2 to +0.5 LSB after calibration | 5.8 uW at 3.9 kHz; 0.008 mm2 core | Similar plotted RT/cold linearity; retention improves on cooling. DNL does not demonstrate monotonicity. |
| R04 Enthoven 2022 | 22 nm FinFET; integrating DAC; >480 pF measured load | 300 to 4.2 K: step 68.3 to 57.1 uV; INL 12.6 to 36.5 LSB; DNL 0.6 to 0.8 LSB | 138 to 157 uW; 62 kHz clock; 0.076 mm2 core | Cold/RT ratios: power 1.14, step 0.84, INL 2.90, DNL 1.33. Noise 192 to 188 uVrms. Do not treat small steps as equal accuracy. |

## Added full-text evidence

| Study | Circuit and scope | Verified results | Limits |
| --- | --- | --- | --- |
| R03 SiGe 2023 | 65 nm CDAC; 13 bits, 0-1 V; 8 S&H outputs. Same research line as R01/R02. | Measured: about 20 uW DAC, 40 uW whole IC; 0.96 uV/s drift with clock off; 275 uVpp ripple at 3.8941 kHz. | MC 44 mK, holder 180 mK, electrons about 400 mK. 64.5 pW/ch and 0.1 Hz scaling are extrapolated. |
| R15 Zurita 2020 | 28 nm FDSOI; 8-bit current steering; 6.6 mV differential span, about 26 uV step. | At 4.2 K: 7.3 uW static including digital; max DNL 0.64 LSB, max &#124;INL&#124; 2.96 LSB. No calibration. | RT max DNL/INL: 0.11/0.63 LSB. 350 ns measured RT rise at 35.2 pF; 100 MS/s is estimated, not measured at cryo. |
| R24J Xiling 2026 | 65 nm R-2R; dual 18-bit DACs; 1.2 V span, 4.58 uV step; RNC + OEM calibration. | At 4 K after calibration: &#124;INL&#124;, &#124;DNL&#124; <=0.8 LSB. Chip DC power 61.6/52.1/59.9 uW at 300 K/4 K/60 mK. | Reusing 4 K calibration at 10 K: DNL +6/-2, INL +5/-8 LSB. 60 mK is environment; SET electron estimate about 900 mK. |

Retention and ripple [R03]: the 0.96 uV/s drift was reconstructed from a SET over 13 minutes with the clock stopped. The 275 uVpp ripple includes refresh and inter-channel coupling. The extrapolated 64.5 pW/ch is not measured eight-channel power. Test clock-off hold, active refresh and cross-coupling separately.

Noise [R24J]: Table I gives 8.6, 2.6 and 3.8 uVrms over 1 Hz-50 kHz at 300 K, 4 K and 60 mK. Measurements use zero DAC code to suppress supply influence; 4 K ground noise is deembedded, while 60 mK retains residual refrigerator noise. The 4.1 nV/sqrt(Hz) value is at 10 kHz, not integrated noise. Our nonzero-code/reference-noise tests remain necessary.

Calibration and temperature [R24J]: uncalibrated 4 K DNL is +5/-10 LSB and INL +25/-45 LSB; OEM plus RNC yields +/-0.8 LSB. Reusing those coefficients at 10 K degrades both metrics. Report raw, fixed-calibration and recalibrated performance separately. These resistor results cannot be copied into TSMC65 capacitor/mismatch models.

Scope and speed [R15]: 26 uV steps come from an approximately 6.6 mV fine range, not from high resolution over 1 V. Its 100 MS/s claim is extrapolated from an RT load-dependent rising-time test; no cryogenic dynamic test was possible. Keep update rate, internal clock, RC time constant and precision settling distinct.

R03 is a system follow-up of R01/R02. R24J and the 2025 ISSCC paper are the same research line. R15 is a distinct current-steering design. They broaden the architecture comparison but do not replace the requirement for matched application/load comparisons.

### Resolution and application choice

R24J motivates about 10 uV steps for selected quantum-device uses. A 1 V span / 10 uV step needs ceil(log2(100000)) = 17 bits; 12 bits permits a fine span of at most 40.96 mV at 10 uV/step. Keep 12 bits / 1 V as a manageable working CDAC target, not as a demonstrated solution for every spin-qubit gate. The actual application may require coarse/fine operation or a different final resolution.

### Temperature and calibration evidence

R15 measured max DNL 0.11 to 0.64 LSB and max |INL| 0.63 to 2.96 LSB from 300 to 4.2 K. R24J Table I: chip DC power 61.6/52.1/59.9 uW at 300 K/4 K/60 mK; integrated noise 8.6/2.6/3.8 uVrms under the stated acquisition conditions. R24J linearity is established at 4 K with calibration, not automatically at 60 mK. R03 reports MC/holder/electron temperatures of 44/180/about 400 mK; R24J reports environment 60 mK and estimates SET electrons about 900 mK. Do not identify any of these with a measured CMOS junction temperature.

## Energy comparison

R01: 3.18 uW/ch / 3.9 kHz = 0.815 nJ/ch/refresh, clock buffer included, external reference excluded. R09: 5.8 uW / 3.9 kHz = 1.49 nJ/DAC/update. R03: about 20 uW / 8 = 2.5 uW/output, and /3894.1 Hz = 0.642 nJ/output/refresh (derived allocation; 40 uW whole IC). R04: 157 uW / 62 kHz = 2.53 nJ/integration cycle, not per settled update. R15 7.3 uW is static; R24J about 60 uW is dual-DAC DC mode and about 300 uW at its highest three-point modulation setting. Do not divide by estimated/max speeds to report a measured switching FoM. No nominal-bit-based ENOB FoM is claimed.

## Verification matrix

| Check | Simulation | Acceptance evidence |
| --- | --- | --- |
| Static transfer | Ascending/descending all-code sweeps; fixed sample delay; repeated initial states. Use native LSB for each implemented resolution. | Report raw error, endpoint INL/DNL, offset/gain, minimum step and hysteresis. Working eventual limits: &#124;INL&#124;<=1, &#124;DNL&#124;<=0.5 LSB; monotonic. |
| Switch and transient | 011<->100 and 000<->111 on 3-bit core; sweep edge, dead time, W and output voltage. Confirm timestep convergence. | <=10 us request-to-settle at RT within 61.0 uV of its own final level; also report final target error. Peak, area and valid-window ripple separately. |
| Retention and noise | Hold 1 ms; sweep leakage/load and codes. Separate clock-off drift, refresh ripple, and random sampled/reference noise. | Working limits: drift <=61.0 uV/1 ms; ripple <=61 uVpp in valid window; rms noise <=61.0 uV over 1 Hz-10 kHz. Not a combined accuracy claim. |
| Power and load | Integrate energy at every physical supply/reference/control port; separate idle/update; sweep Cload and reference impedance. | Behavioral-driver output energy is load-delivered energy, not a model of decoder internal power. Recheck output range under load. |
| Robustness | Supported PVT, MOS/cap mismatch and PEX. Low-temperature cases require validated models or measurements; save calibration per temperature. | Compare uncalibrated, fixed-calibration and recalibrated results. Same accuracy/power caps, RT settling <=10 us and cold <=20 us. Record actual temperature location. |

## Week 7 sequence

| Order | Task | Decision enabled |
| --- | --- | --- |
| 1 | Save the 3-bit baseline and complete reset TG implementation | Compare against the ideal-reset case; preserve the original regression. This closes the remaining ideal switch before sizing decisions. |
| 2 | Create spec-linked ADE measurements | Ascending/descending codes, major-carry/full-scale transitions; raw/static errors, settling, ripple and timestep convergence. |
| 3 | Determine load and error sensitivities | Run the listed C/leakage probes; identify gain loss and hold limits. Agree the real interface with the mentor before qualifying a loaded design. |
| 4 | Choose TG and capacitor sizes from the failed limits | Use settling, injection, noise and power together. Keep MIM until equal-C MOM evidence warrants a change; assess 8-bit scaling before 12 bits. |

Retain the fast 400 ns full-code test as a functional regression. Add a slow spec test with 1 ms command spacing, 10 us RT settling deadline, then a separate 1 ms clock-off hold test after settling. Measure request-to-settle (including dead time) to the final value and separately report error from the ideal code. The plateau must stay inside the 61.0 uV settling band throughout the valid window. A drift/noise limit does not conceal a large static offset.

Timestep convergence: use effective simulator accuracy/time-step controls, rerun tighter, and compare peak, area and settling. Do not rely on a maxstep setting reported as ignored by Spectre X. Ideal references/Verilog-A driver remain bench models; power measurements must identify missing physical blocks.

## Circuit sizing constraints

Ron follows Req <= t_settle/[Ceff*ln(deltaV/error)] for a first-order model. For a single branch with floating top plate and other bottom plates AC grounded, Ceff=Cb*(Ctotal-Cb)/Ctotal; the present MSB is about 221 fF. Multi-bit switching requires full transient simulation. Do not optimize Ron alone: increasing W also changes injection, parasitics and control energy.

Droop approximately equals Ileak*Thold/Chold. A 1 pF hold node with 61 uV over 1 ms permits about 61 fA. Adding 1 pF to the present 885 fF top plate yields a simple charge-sharing gain about 0.469. It affects final voltage, not only delay.

Keep MIM until a legal MOM PCell is compared at equal C for metal stack, geometry, density, matching, voltage coefficient, parasitic terminals, DRC and PEX. R09 small MOM units and R10 191-to-197 fF cryogenic change in 40 nm do not prove TSMC65 MOM superiority. The newly added resistor results also do not supply TSMC65 capacitor/mismatch parameters.

## Mentor decisions

1. Actual bias destination, load/current, voltage span and polarity.
2. Required voltage step and total accuracy; whether a fine range or calibration is acceptable.
3. Temperature locations, valid model range and measurement resources.
4. Power allocation, channel count, quiet window, reference noise and allowable refresh ripple.

## Complete references

[R01] P. Vliex et al.. **Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications**. IEEE Solid-State Circuits Letters, vol. 3, pp. 218-221, 2020. DOI: [10.1109/LSSC.2020.3011576](https://doi.org/10.1109/LSSC.2020.3011576). [Open full text](https://juser.fz-juelich.de/record/888069/files/FINAL%20VERSION_QC.pdf). Evidence: Sections IV and V; Tables I and II.

[R09] T. Miki, R. Takahashi, and M. Nagata. **An 11-bit 0.008 mm2 charge-redistribution digital-to-analog converter operating at cryogenic temperature for large-scale qubit arrays**. IEICE Electronics Express, vol. 19, no. 8, article 20220099, 2022. DOI: [10.1587/elex.19.20220099](https://doi.org/10.1587/elex.19.20220099). [Open full text](https://da.lib.kobe-u.ac.jp/da/kernel/90009517/90009517.pdf). Evidence: Section 4; Figures 7-9; Table I.

[R04] L. Enthoven, J. van Staveren, J. Gong, M. Babaie, and F. Sebastiano. **A 3V 15b 157uW Cryo-CMOS DAC for Multiplexed Spin-Qubit Biasing**. IEEE Symposium on VLSI Technology and Circuits, pp. 228-229, 2022. DOI: [10.1109/VLSITechnologyandCir46769.2022.9830309](https://doi.org/10.1109/VLSITechnologyandCir46769.2022.9830309). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/154843798/A_3V_15b_157W_Cryo_CMOS_DAC_for_Multiplexed_Spin_Qubit_Biasing.pdf). Evidence: Page 229, Table 1 and Figure 6.

[R02] R. Otten et al.. **Qubit Bias using a CMOS DAC at mK Temperatures**. IEEE ICECS, 2022. DOI: [10.1109/ICECS202256217.2022.9971043](https://doi.org/10.1109/ICECS202256217.2022.9971043). [Open full text](https://confcats-event-sessions.s3.amazonaws.com/icecs22/papers/6353.pdf). Evidence: Sections II and III; Table I.

[R10] B. Patra et al.. **Characterization and Analysis of On-Chip Microwave Passive Components at Cryogenic Temperatures**. IEEE Journal of the Electron Devices Society, vol. 8, pp. 448-456, 2020. DOI: [10.1109/JEDS.2020.2986722](https://doi.org/10.1109/JEDS.2020.2986722). [Open full text](https://repository.tudelft.nl/file/File_6d4cc63f-f0aa-4ad1-8d39-9942b3c07726). Evidence: Section III and Table 1.

[R11] P. A. t Hart et al.. **Characterization and Modeling of Mismatch in Cryo-CMOS**. IEEE Journal of the Electron Devices Society, vol. 8, pp. 263-273, 2020. DOI: [10.1109/JEDS.2020.2976546](https://doi.org/10.1109/JEDS.2020.2976546). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/71537207/09015956.pdf). Evidence: Sections IV and V.

[R18] J. van Staveren et al.. **Cryo-CMOS Voltage References for the Ultrawide Temperature Range From 300 K Down to 4.2 K**. IEEE Journal of Solid-State Circuits, vol. 59, no. 9, pp. 2884-2894, 2024. DOI: [10.1109/JSSC.2024.3378768](https://doi.org/10.1109/JSSC.2024.3378768). [Open full text](https://pure.tudelft.nl/ws/portalfiles/portal/230892395/Cryo-CMOS_Voltage_References_for_the_Ultrawide_Temperature_Range_From_300_K_Down_to_4.2_K.pdf). Evidence: Sections IV and V.

The [full literature review](../cryogenic_bias_dac_literature_review_2026-10-04.md) contains all 24 screened records and reading status. The core assigned/reference-paper identity should be confirmed with the mentor.

[R03] L. Schreckenberg et al. **SiGe Qubit Biasing with a Cryogenic CMOS DAC at mK Temperature**. IEEE ESSCIRC, pp. 161-164, 2023. DOI: [10.1109/ESSCIRC59616.2023.10268801](https://doi.org/10.1109/ESSCIRC59616.2023.10268801). [Local full text](papers/SiGe_Qubit_Biasing_with_a_Cryogenic_CMOS_DAC_at_mK_Temperature.pdf). Evidence: Sections II-III; Table I; Figure 3 (PDF pp. 2-3).

[R15] M. E. P. V. Zurita et al. **Cryogenic Current Steering DAC With Mitigated Variability**. IEEE Solid-State Circuits Letters, vol. 3, pp. 254-257, 2020. DOI: [10.1109/LSSC.2020.3013443](https://doi.org/10.1109/LSSC.2020.3013443). [Local full text](papers/ESSCIRC_DAC_paper-revised.pdf). Evidence: Sections III-V; Figures 7-9; Table I (author manuscript pp. 3-4).

[R24J] Y. Li, Y. Zhang, H. Lin, and C. Wang. **Xiling: Cryo-CMOS Manipulator Using Dual 18-bit R-2R DACs for Single-Electron Transistor at 60 mK**. IEEE Journal of Solid-State Circuits, vol. 61, no. 8, pp. 4193-4205, 2026. DOI: [10.1109/JSSC.2026.3671795](https://doi.org/10.1109/JSSC.2026.3671795). [Local full text](papers/Xiling_Cryo-CMOS_Manipulator_Using_Dual_18-bit_R-2R_DACs_for_Single-Electron_Transistor_at_60_mK.pdf). Evidence: Section V; Figures 20-25; Table I (PDF pp. 9-12).

## Reading status

All three requested PDFs have been read. R15 is an author manuscript; the other two are published IEEE PDFs. Original filenames are retained. The full literature review now marks R03, R15 and the R24 journal extension as full-text reviewed. No additional paper download is required for this revision.
