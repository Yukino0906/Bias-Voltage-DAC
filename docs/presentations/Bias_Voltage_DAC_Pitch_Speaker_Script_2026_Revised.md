# Bias Voltage DAC — revised 5-minute speaker script

Six presentation slides (5:00 total), followed by one backup slide.

## Slide 1

SUGGESTED TIME: 0:00–0:35 (35 s)

SCRIPT
Our project is a bias voltage DAC for cryogenic solid-state qubit control. Quantum-dot gates need precise DC voltages to set their operating points. As channel count grows, bringing every analog connection from room temperature creates a wiring bottleneck. Moving the electronics closer to the qubits helps, but adds heat inside the cryostat. We want one low-power DAC to generate and hold multiple accurate bias voltages. Our current progress is behavioral modeling and early circuit setup.

SOURCES
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Sections I–II.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).

TECHNICAL BACKUP
Application focus is quantum-dot spin qubits. This is a project proposal, not a claim of fabricated hardware or cryogenic measurements.

## Slide 2

SUGGESTED TIME: 0:35–1:15 (40 s)

SCRIPT
Our literature-informed targets are a zero-to-one-volt output range, a thirteen-bit nominal code grid, and eight independently held outputs. Thirteen bits gives about one hundred twenty-five microvolts per step and provides margin over the twelve-bit application requirement. Periodic refresh counters storage leakage. Power should stay in the microwatt-per-channel range. Vliex and colleagues reported six-kelvin measurements and about two-point-seven microwatts per channel in sixty-five-nanometer CMOS. Those are literature benchmarks. We still need to establish our own accuracy and power in the one-eighty-nanometer design.

SOURCES
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Sections II, IV-C, Table II, Conclusion.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).

TECHNICAL BACKUP
1 V / 8192 = 122.07 µV. 1 V / 4096 = 244.14 µV. Nominal resolution does not establish ENOB, absolute accuracy, or measured linearity. Table II: DAC total 21.1 µW for eight channels, plus 4.3 µW clock buffer = 25.4 µW total. The ≈2.7 µW/ch headline follows the paper abstract/conclusion and excludes that separate clock-buffer contribution. Final temperature, power budget and load specification remain to be agreed. No 65 nm power projection is claimed for TSMC 180 nm.

## Slide 3

SUGGESTED TIME: 1:15–2:05 (50 s)

SCRIPT
This schematic is adapted from Figures two and three of the 2020 paper by Vliex and colleagues, identified in full at the bottom of this slide. The ten-bit fine DAC uses two binary-weighted capacitor subarrays linked by an attenuation capacitor. Selecting upper and lower references adds eight coarse regions. A demultiplexer connects the shared DAC to eight storage capacitors. Repeated charge sharing charges each output without a continuous output buffer. Switching and digital control still consume power. The parasitic capacitance, lower-reference reset and leakage shown here are added modeling assumptions. We will compare this split array against plain binary and segmented alternatives.

SOURCES
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Section III, Figs. 2 and 3.
Project: docs/figures/cr_dac_topology.png, model/draw_cr_dac_topology.py, model/bias_dac_v2.py.

TECHNICAL BACKUP
Original project schematic is reused as an image excerpt. Its parasitic capacitor, reset-to-VL choice and leakage source represent modeling assumptions/inferences. Buffer-less storage generally requires multiple refreshes to settle. The ideal capacitor core has no continuous bias-current path, but the complete system does not have zero static or total power.

## Slide 4

SUGGESTED TIME: 2:05–2:55 (50 s)

SCRIPT
The current behavioral model exposes a gap at coarse-region boundaries. Parasitic capacitance reduces the fine-DAC span, so advancing the coarse reference can skip a voltage range. This example shows an eight-millivolt jump. Gain-and-offset calibration changes the mapping, but cannot create missing output levels. The right plot applies the paper’s intermediate-span idea: use a wider reference span briefly to add those levels. The maximum adjacent gap falls from about sixty-six-and-a-half to one-point-nine nominal LSBs. These are our model results under stated assumptions. The intermediate steps are coarser, and full-scale endpoint coverage remains unresolved.

SOURCES
Project: docs/figures/v2_coarse_jump_compensation.png; model/bias_dac_v2.py, plot_coarse_jump_and_compensation(), intermediate_sequence(), coverage().
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Section IV-C and Fig. 9.

TECHNICAL BACKUP
These are project behavioral simulations, not reproduction of measured silicon. The two plotted panels are reused from the original figure. α=0.064 is a paper-informed modeling point, not an extracted 180 nm parasitic. Plot (a) uses DAC input word; plot (b) uses sequence index after added settings. Maximum adjacent achievable-voltage gap: 66.5 LSB before and 1.9 LSB after intermediate steps. That metric does not include missing full-scale endpoint coverage. The repo’s target-distance plot shows a remaining top-of-range error near 1 V, so do not claim <1 LSB accuracy over the complete range. Nominal 13-bit LSB =122.07 µV; the inserted settings use a 250 mV reference span.

## Slide 5

SUGGESTED TIME: 2:55–4:10 (75 s)

SCRIPT
There are four main challenges. First, capacitor mismatch and parasitics affect DNL, INL and output coverage. We will compare coding options and combine region overlap with calibration. Second, leakage sets a tradeoff between held-voltage droop and refresh power. The storage capacitor and refresh rate must come from an extracted leakage budget, rather than assuming the literature’s refresh rate will work for our circuit. Third, real switches introduce finite settling and charge injection. These effects require transistor-level timing and sizing checks because the current model does not fully capture them. Fourth, standard room-temperature device models may not predict cryogenic behavior. We need validated cryogenic models where available. Otherwise, parameter sensitivity studies can bound risk, but cannot prove operation at cryogenic temperature.

SOURCES
Project: docs/phase2_cryo_architecture_research.md, Sections 5, 8–10; model/bias_dac_v2.py; spice/README.md.

TECHNICAL BACKUP
The behavioral model supports mismatch, parasitic, gain/offset and leakage studies. Finite switch resistance, charge injection and a calibrated cryogenic device layer need further work. A room-temperature PDK does not establish cryogenic performance.

## Slide 6

SUGGESTED TIME: 4:10–5:00 (50 s)

SCRIPT
The implementation plan follows those challenges. First, close range gaps and check endpoint coverage using intermediate settings or intentional overlap, with digital gain-and-offset compensation. Second, select a capacitor coding scheme using a common linearity and capacitance budget. Third, build the TSMC one-eighty-nanometer circuit in Cadence, verify schematics, and then check layout extraction. We will evaluate settling, injection, leakage and power, including the digital and refresh overhead. Success is a DAC with the required bias coverage and a refresh and power budget supported by circuit results. The next slide contains backup simulations for discussion.

SOURCES
Project: docs/phase2_cryo_architecture_research.md, Sections 7–10; spice/README.md; model/bias_dac_v2.py.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).
TSMC 180 nm Cadence implementation is the user-specified project direction.

TECHNICAL BACKUP
Checked-in SPICE files currently use ideal switches and behavioral sources; README marks them unverified by simulation. Do not describe them as completed transistor-level validation. Charge injection, switch Ron, noise, cryogenic parameter shifts, and post-layout parasitics require additional modeling or circuit evaluation. Standard PDK corners alone do not establish operation at 6 K. Retain temperature and leakage sensitivity studies if validated cryogenic compact models are unavailable.

## Slide 7

BACKUP ONLY: outside the 5-minute presentation

SCRIPT
The behavioral model lets us compare nonidealities before building the full circuit. On the left, the existing mismatch sweep shows that segmented coding has lower differential nonlinearity than the split array with an attenuation capacitor under these assumptions. The paper marker is only a reference comparison. On the right, leakage pulls the held voltage away from its target between refreshes. With one picoamp of leakage and a one-picofarad storage capacitor, the modeled droop is about two hundred fifty-six microvolts per period at three-point-nine kilohertz. Faster refresh reduces droop but raises switching activity. These studies guide the architecture, but they do not yet establish silicon accuracy or cryogenic performance.

SOURCES
Project: model/bias_dac_v2.py, plot_mismatch_sweep() and plot_sh_refresh(); docs/figures/v2_mismatch_sweep.png and v2_sh_refresh_leakage.png.
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Eq. (1) and Fig. 8(f), for markers already present in the project figure.

TECHNICAL BACKUP
Mismatch plot uses 150 seeds at each sigma point, per the checked-in code. The plotted statistic is mean maximum absolute DNL for a 10-bit fine DAC; the paper measured sigma_D marker is a different statistic and not a direct validation. S&H panel is the middle panel of the original image, retaining axes and legend. Droop per period is 256.4 µV at 3.9 kHz and 2.6 µV at 390 kHz for I/C=1 A/F. Absolute storage error can exceed one-period droop because of finite charge sharing. The model includes gain/offset and parasitic effects; switch charge injection, finite Ron, noise and a calibrated cryogenic parameter layer remain future work.