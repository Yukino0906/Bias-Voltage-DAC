# Bias DAC Current Project State

Updated October 17, 2026, at Week 8 closeout. Read this file first, then the [Week 8 experiment log](experiments/week-08-2026-10-17.md). The closeout below supersedes earlier plans and intermediate readings.

## Current decision and next action

Delivery preference: every weekly report must include both Word and a matching PDF. Week8 now includes both formats, with the five-page PDF exported from the final verified Word document.

The user explicitly ended this week's work. Week 8 reporting is complete around two deliverables: (1) physical MOS reset implementation and simulations, (2) a temperature-only TT corner scan. Do not repeat the wrap-up reminder or continue experiments. The next action is the Tuesday October20 mentor discussion; further design choices await that feedback. No new mentor feedback was received during fall break.

The five-page English [Week 8 weekly report](reports/weekly%20task/BiasDAC_WeeklyTask_Week08_2026-10-17.docx) preserves all five template questions, reset comparisons and four waveform figures, and adds final temperature results. It has been visually checked and has not been submitted or sent. These results can support the next Sprint4 report; no Sprint4 deadline or submission is assumed.

### Final temperature scan results

- Three enabled corners TT_m40/TT_27/TT_85, all tt_lib, at -40/27/85 C; Nominal disabled. Same W=0.5 um MOS-reset circuit, 1 V supply/references, no added output load and second-reset driver. All three runs completed with staircase and second reset visible.
- Final code111 Vout near343 ns: -40 C=874.4884 mV (user-confirmed; exact marker time obscured),27 C=874.4570 mV at343.0198 ns,85 C=874.3085 mV at343.0218 ns.
- Differences versus27 C: +31.4 uV at-40 C and-148.5 uV at85 C. Maximum-to-minimum spread179.9 uV. This supersedes the preliminary unequal-time163.5 uV spread.
- One-code, finite-delay temperature sensitivity only. No all-code temperature INL/DNL, quantified temperature-dependent reset timing/release offsets, full PVT, retention, validated temperature-range or cryogenic claim. Numerical convergence remains unchecked.

### Confirmed reset progress and limits

- Recovered six-TG ideal-reset cell: cdac_3b_n65_tg_recover_oct17. Historical netlist backed up. A mistakenly MOS-bound reference run was excluded; the user verified the corrected I6 binding and W6 relay.
- Physical variant: cdac_3b_n65_tg_mosrst_oct17, reset nch D=Vout/G=rst/S=Vl/B=VSS, L=60 nm, nf=m=1. W was changed in place from 1 um to 0.5 um with user authorization. Previous results remain recorded; there is no separate half-width cell.
- tt_lib, 27 C, 1 V supply/reference span, no added output load, 400 ns transient. Six reference TGs unchanged. Codes000/100/111 MOS-minus-ideal differences: W=1 um -330.0194/-732.3/-1016.9 uV; W=0.5 um -184.2289/-395.6/-546.0 uV. Absolute differences improve44-46%; times are slightly unequal screenshot samples, not converged INL/DNL.
- cdac_code_driver_reset_test adds a second reset350-370 ns with1 ns edges while bottom plates remain111. W=0.5 um Vout:874.4486 mV at348.9924 ns; +3.108614 uV at368.9987 ns; -184.574 uV at374.3853 ns. Charged-output discharge is demonstrated nominally; release error remains.
- Marker365.542 ns=61.27946 uV implies about15.54 ns from assertion to near the provisional+61 uV boundary. It is slightly outside the boundary and not a precise settling time. The zigzag near zero is unresolved. Conservative/maxstep100 ps verification was suggested but NOT run. No claim of post-release61 uV accuracy, noise, long hold, PVT, PEX or cryogenic performance.
- Mentor decisions: reset error and timing budgets; speed/loading/size trade-off; appropriate compensation/topology if needed; next numerical and loaded/hold tests. Charge injection, feedthrough and parasitic loading remain hypotheses, not separately quantified mechanisms.

### Historical Week 7 closeout

The user stopped new schematic work and requested both reports. Week 7 weekly report and Sprint 3 (September 28–October 11, user-confirmed) have been consolidated in English with embedded evidence and PDF exports. The five weekly template questions and October 6 mentor feedback are retained. Sprint 3 now also includes a landscape appendix with the complete internal CDAC schematic, supplied October 11; the reset remains explicitly identified as ideal. Sprint 3 also includes the Ron testbench in Enabled TG resistance investigation; the updated six-page PDF was visually checked. No report has been submitted or sent. The next meeting is October 13.

User-confirmed report conditions: October 11 Ron and CDAC runs use tt_lib at 27 C; the CDAC has no added output load. Supply/reference span is 1 V. Sprint task supplied by the user: https://github.itap.purdue.edu/SoCETOrganization/AMS_Tracking_Fall2026/issues/48 . Do not infer additional requirements from the issue title/content; only the supplied link was recorded.

Next: review the reports with the user/mentor. Agree switch device/drive direction, actual load, area ceiling, cold-model availability and whether the next functional block is internal reset/control or companion hold/refresh. The b2 stronger-TG experiment and the proposed two-channel bias_hold_2ch_n65 remain deferred and unbuilt. The generated connection picture is an explanatory drawing, not a Cadence implementation. A previously logged single-channel/eight-unit concept is superseded; no hold-module topology or sizing is approved.

## Established circuit and stimulus

- 3-bit CDAC, C:2C:4C plus C dummy; unit 110.659 fF. Six MOS reference TGs; reset and reference sources are ideal and the driver is Verilog-A.
- TG: NMOS W/L = 1 um/60 nm, PMOS = 2 um/60 nm; nf=1, m=1; bodies tied to VSS/VDD. User confirms the same TG is used for all bits.
- Archived driver: `experiments/code/cdac_code_driver_user_2026-10-11.va`. It disconnects only changed bits. Reset release 20 ns, first break 30 ns, code interval 40 ns, dead time 5 ns, edges 1 ns, stop 400 ns. Initial make 35 ns applies 000; 011→100 breaks at 190 ns and makes at 195 ns.

## Confirmed results and limits

### Ron

EN=VDD=1 V and ENB=VSS=0 V stay fixed. A=vtest, B=vtest+1 mV; sweep 0–0.999 V, 0.01 V step. The peak near 0.52 V is about 20–21 kOhm while enabled. At 0.52 V: NMOS Vgs/Vth/Vbs/Id = 480/654.5/−520 mV / 25.65 nA; PMOS = −521/−644.6/479 mV / −22.33 nA. Summed magnitudes imply 20.84 kOhm. Both devices lack midrange overdrive, with a further body-bias threshold increase.

Rail comparisons: NMOS Vgs=1 V, Vth=601.4 mV, Id=1.546 uA; PMOS Vgs=−1 V, Vth=−575.4 mV, displayed Id=+1.19 uA (user explicitly confirmed no minus sign). These imply branch resistances about 647/840 Ohm, not the full TG resistance. Current sign interpretation and settling impact remain open. Do not attribute everything to body effect or declare a specification failure from this alone.

### Switching disturbance

000→001: 146.265 mV at 76.13409 ns versus 124.9975 mV at 80.81945 ns, a 21.2675 mV overshoot. Only this isolated-bit direction was characterized; the full set of single-bit/reverse tests is incomplete.

011→100: near-minimum 243.21157 mV at 196.06593 ns; pre-make 378.32457 mV at 194.27459 ns; plateau 499.99433 mV at 199.17518 ns. Dip is about 135.113 mV relative to pre-make or 131.788 mV below ideal 011.

Aligned markers at 196.0659 ns: b0/b1/b2 = 173.7483/436.5179/224.7282 mV and Vout=243.2116 mV. Reconstruction (b0+2*b1+4*b2)/8=243.2121125 mV. Residual over 189–200 ns is visually about −4.9 to −0.5 uV. The bottom-plate dynamics quantitatively account for the dip, but their physical cause is not isolated; injection already present on the bottom plates is not excluded. All numbers are screenshot/readout based; peak search and numerical convergence remain unverified.

### Sampled linearity

October 11 samples at 60,100,140,180,220,260,300,340 ns (25 ns after scheduled make). Nominal errors in uV: [−13.14e−12, −4.514, −4.021, +6.612, −4.020, −4.490, −2.419, −3.019]. Code 000 is effectively zero on the already scaled expression. Preserve the positive 011 value.

Endpoint L=(V7−V0)/7=124.999568714 mV. INL=(Vk−V0−kL)/L; DNL=(Vk−V(k−1))/L−1. Maximum |INL|=6.32e−5 LSB at 011; maximum |DNL|=8.85e−5 LSB at 010→011; all seven steps positive. Max nominal voltage error=6.612 uV. Nominal-denominator DNL max=8.5064e−5 LSB; do not mix normalizations. These are finite-delay nominal results, not evidence of 12-bit silicon accuracy. Historical October 4 unequal-delay markers remain in the log but are superseded for the current report.

### Area and submodules

C0 properties: tsmcN65/mimcap_3t_9m_1p0, model mimcap_sin_3t, W=L=10 um, ArrayX=ArrayY=Multiplier=1, C=110.659 fF; With Mismatch Effect unchecked on this instance. Binary arrays plus dummy at 3/8/12 bits use 8/256/4096 units, total 0.885272/28.328704/453.259264 pF, and W×L sums 0.0008/0.0256/0.4096 mm². This excludes PCell footprint overhead, legal spacing, routing, edge dummies, switches and support blocks; it is not post-layout area. No area budget has been agreed.

Candidate scope: physical reset and nonoverlap control, hold/refresh characterization, reference and load interface. Two-channel sample-and-hold was explained but deferred before construction. Direct hold-cap attachment changes charge sharing at the floating CDAC top plate; an appropriate drive/isolation interface is required before integrated claims. No new submodule was implemented this week.

## Outstanding evidence and future tests

- Raw/exported current waveforms and simulator maxstep/tolerance settings; timestep/tolerance convergence and stable sampling window.
- Complete isolated-bit/reverse tests and a controlled remedy comparison; no tg_n65_x4 result exists.
- Loaded settling, 1 ms retention, noise, power, mismatch/PVT and PEX.
- Actual MIM layout bounding box/pitch and project area budget.
- Mentor-approved load/range/temperature specification and valid cold models; no cryogenic performance is demonstrated.

## Records and reports

- [Week 7 experiment log](experiments/week-07-2026-10-11.md)
- [Week 7 weekly report](reports/weekly%20task/BiasDAC_WeeklyTask_Week07_2026-10-11.docx) and same-name PDF
- [Sprint 3](reports/sprint/sprint-03-2026-10-11.docx) and same-name PDF/Markdown
- [Working specifications](specs/README.md): v0 revision 2, provisional targets
- [Weekly workflow](reports/weekly%20task/README.md)

The original weekly template, Week 6 report and Sprint 2 are preserved. Reports contain selected original screenshots; the user maintains the image archive in OneNote. Temp sources can expire; request a specific missing image rather than claiming OneNote access. Local documentation and remote ASICFab design files are distinct. Week 7 is closed for reporting; do not repeat its old wrap-up reminder. Week 8 is active under the plan above.

## Latest Week 8 measurement

MOS reset release: Vout19.0253ns=+1.90526nV; Vout23.8987ns=-329.748uV, net shift about-329.750uV. Near-flat negative plateau shown through30ns only. Next compare against recovered ideal-reset baseline under identical conditions; do not infer mechanism or retention from this plot alone. See Week8 log for image and limits.

## Latest comparison discrepancy

The user-supplied ideal-reset reference plot also shows about-329.816uV release shift, only0.066uV different from the MOS-reset result at slightly different marker times. Actual reset primitive and CDAC binding in the new run netlist must be verified before attributing the shift to NMOS reset. UI status shows the new ideal-reference testbench, but internal simulation contents are not yet checked. See Week8 log.

## Netlist diagnosis of comparison

October17 14:16:55 ideal-reference run is confirmed to still instantiate cdac_3b_n65_tg_mosrst_oct17 at I6, with M0 (Vout rst Vl VSS) nch. Its-329.814uV result is not ideal-reset evidence. Fix the I6 master in tb_cdac_3b_idealrst_ref_oct17, then verify regenerated netlist includes recovered CDAC and relay before rerunning the comparison.

## Latest reference waveform

Latest follow-up: the user's current message explicitly identifies image1 as ideal reset and image2 as MOS reset, consistent with the prior reference timestamp and near-zero waveform. MOS-minus-ideal differences at approximately codes000/100/111 are -330.0194/-732.3/-1016.9 uV at slightly unequal marker times. The difference grows with code in addition to the initial offset; three points do not establish INL or a pure gain model. Estimated endpoint span reduction is 0.0785%. Reset MOS parasitic loading is a hypothesis, not an isolated mechanism. Next proposed experiment is an independent half-width reset variant (W=0.5 um, L=60 nm), preserving the W=1 um baseline; no width-sweep result or charged-output reset test exists yet.

New14:25:09 plot shows near-zero Vout through reset release (M4 at24.1838ns=-13.2273aV, numerical zero). User subsequently confirmed the regenerated netlist binds I6 to recover_oct17 and contains W6 relay with no reset NMOS. The reference identity is now confirmed by the user's netlist inspection, superseding the pending check above. The valid reference remains near zero versus approximately -329.750 uV MOS reset release shift. Separate charge injection/feedthrough contributions are not isolated. Next planned measurement: compare both runs at 60/220/340 ns (codes 000/100/111) to determine whether the output difference persists and depends on code; no such readings are available yet.


## Half-width reset result (October 17)

The user authorized editing the existing MOS-reset cell in place rather than creating another variant; original reset W=1 um is preserved in the preceding recorded results. Following the instruction to change only reset W to 0.5 um (L=60 nm unchanged), the user supplied codex-clipboard-aee338d8-38fe-4da4-b992-32550ab72db5.png. Treat this as the half-width run from task context; no new device-property/netlist extract was supplied. Readouts: 59.57447 ns = -184.2289 uV; 223.1007 ns = 499.6032 mV; 343.902 ns = 874.4587 mV. Against the previously verified ideal reference, differences are -184.2289/-395.6/-546.0 uV for 000/100/111. Relative to W=1 um, absolute differences decrease about 44.2/46.0/46.3 percent. Endpoint span reduction after removing zero-code offset is about 0.04135 percent versus 0.07850 percent before. Values are rounded screenshot samples at slightly unequal times, not converged accuracy or INL results.

Width dependence supports a reset-device-related contribution but does not separately establish charge injection, feedthrough or parasitic-capacitance mechanisms. No charged-output discharge test is complete. Next proposed test: retain W=0.5 um and add a second reset pulse after code111 has settled (350-370 ns), with bottom-plate code held at111; inspect discharge to Vl and the release disturbance. Preserve the ascending-driver baseline before modifying the shared driver. This is a proposed test, not an executed change or a demonstration of refresh preserving the prior output.


## Second reset pulse: charged-output discharge

User supplied codex-clipboard-40734b43-dca4-40e9-8b7c-5cd327b0b4ac.png following the reset-test driver change (second reset asserted350 ns, released370 ns, edges1 ns; bottom-plate code111 retained). In the ongoing W=0.5 um reset context, Vout markers are:348.9924 ns=874.4486 mV;368.9987 ns=+3.108614 uV;374.3853 ns=-184.574 uV. Output visibly discharges after350 ns. At roughly19 ns after the assertion command it is near zero; this supports charged-node reset operation under the nominal test conditions, not a measured settling time. Release sample minus pre-release sample is-187.682614 uV; the pre-release residual is still changing, so this is a sampled difference, not an isolated charge-injection measurement. Negative post-release offset persists and is close in magnitude to the earlier zero-code half-width result, but sampling times and initial conditions differ.

Next measurement: zoom350-370 ns and inspect entry into +/-61 uV of Vl=0, remaining inside until reset release. This is a provisional comparison band, not an approved specification. Use reset assertion at350 ns as the stated time origin; threshold crossing, numerical convergence, long-term retention and cold-temperature performance remain unmeasured.


## Approximate discharge threshold marker

Screenshot codex-clipboard-807e35ab-9f78-4dda-8463-a314c6adf968.png shows M2 at365.542 ns,61.27946 uV. Relative to the350 ns assertion command this is15.542 ns. It is slightly above the provisional +61 uV limit, so it is an approximate near-threshold time, not an exact settling measurement. Displayed trace subsequently stays visually within +/-61 uV until the370 ns reset release, then leaves the band. A coarse zigzag around zero is visible; physical ringing versus numerical/time-sampling effects is unresolved. Next recommended numerical check: conservative transient accuracy with maxstep100 ps, keeping circuit and pulse timing unchanged, then compare this crossing and release offset. No rerun is yet reported. The15.54 ns estimate describes discharge while reset is ON only, not post-release accuracy or DAC code settling.
