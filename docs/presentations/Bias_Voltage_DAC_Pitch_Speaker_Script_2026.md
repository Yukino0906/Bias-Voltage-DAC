# Bias Voltage DAC: 5-minute speaker script

## Slide 1 — 0:00–0:40 (40 s)

Our project is a bias voltage DAC for cryogenic solid-state qubit control. Quantum-dot gates need precise DC voltages to establish their operating points. As the number of bias channels grows, bringing every analog connection from room temperature becomes a wiring bottleneck. Moving electronics closer to the qubits helps with that scaling problem, but it puts their power consumption inside a very limited cooling budget. Our goal is a shared, low-power DAC that can generate and hold multiple precise bias voltages. The project is currently at behavioral modeling and early circuit setup.

### Sources
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Sections I–II.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).

### Technical backup (not part of the timed script)
Application focus is quantum-dot spin qubits. This is a project proposal, not a claim of fabricated hardware or cryogenic measurements.

## Slide 2 — 0:40–1:25 (45 s)

The starting requirements come from the pitch reference and the 2020 cryogenic DAC paper. We want a zero-to-one-volt range and a thirteen-bit nominal code grid, which is about one hundred twenty-five microvolts per step. The paper adds that extra bit as margin over a twelve-bit application requirement. Eight outputs share one DAC, and each storage capacitor needs periodic refresh. Power should stay in the microwatt-per-channel range. The paper measured operation at six kelvin and reports about two-point-seven microwatts per channel in a sixty-five-nanometer process. Those are literature benchmarks, not results from our project.

### Sources
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Sections II, IV-C, Table II, Conclusion.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).

### Technical backup (not part of the timed script)
1 V / 8192 = 122.07 µV. 1 V / 4096 = 244.14 µV. Nominal resolution does not establish ENOB, absolute accuracy, or measured linearity. Table II: DAC total 21.1 µW for eight channels, plus 4.3 µW clock buffer = 25.4 µW total. The ≈2.7 µW/ch headline follows the paper abstract/conclusion and excludes that separate clock-buffer contribution. Final temperature, power budget and load specification remain to be agreed. No 65 nm power projection is claimed for TSMC 180 nm.

## Slide 3 — 1:25–2:20 (55 s)

The starting architecture uses charge redistribution. A ten-bit fine DAC uses binary-weighted capacitors split into two subarrays, connected by an attenuation capacitor. Selecting the upper and lower references provides eight coarse regions across the one-volt range. The output then goes through a demultiplexer to one of eight storage capacitors. We omit a continuous output buffer and allow the storage voltage to settle through repeated charge-sharing events. That reduces analog overhead, although switching and digital control still consume power. The array topology is a starting point. We are also comparing plain binary and segmented alternatives before committing to the transistor-level design.

### Sources
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Section III, Figs. 2 and 3.
Project: docs/figures/cr_dac_topology.png, model/draw_cr_dac_topology.py, model/bias_dac_v2.py.

### Technical backup (not part of the timed script)
Original project schematic is reused as an image excerpt. Its parasitic capacitor, reset-to-VL choice and leakage source represent modeling assumptions/inferences. Buffer-less storage generally requires multiple refreshes to settle. The ideal capacitor core has no continuous bias-current path, but the complete system does not have zero static or total power.

## Slide 4 — 2:20–3:10 (50 s)

The behavioral model lets us compare nonidealities before building the full circuit. On the left, the existing mismatch sweep shows that segmented coding has lower differential nonlinearity than the split array with an attenuation capacitor under these assumptions. The paper marker is only a reference comparison. On the right, leakage pulls the held voltage away from its target between refreshes. With one picoamp of leakage and a one-picofarad storage capacitor, the modeled droop is about two hundred fifty-six microvolts per period at three-point-nine kilohertz. Faster refresh reduces droop but raises switching activity. These studies guide the architecture, but they do not yet establish silicon accuracy or cryogenic performance.

### Sources
Project: model/bias_dac_v2.py, plot_mismatch_sweep() and plot_sh_refresh(); docs/figures/v2_mismatch_sweep.png and v2_sh_refresh_leakage.png.
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Eq. (1) and Fig. 8(f), for markers already present in the project figure.

### Technical backup (not part of the timed script)
Mismatch plot uses 150 seeds at each sigma point, per the checked-in code. The plotted statistic is mean maximum absolute DNL for a 10-bit fine DAC; the paper measured sigma_D marker is a different statistic and not a direct validation. S&H panel is the middle panel of the original image, retaining axes and legend. Droop per period is 256.4 µV at 3.9 kHz and 2.6 µV at 390 kHz for I/C=1 A/F. Absolute storage error can exceed one-period droop because of finite charge sharing. The model includes gain/offset and parasitic effects; switch charge injection, finite Ron, noise and a calibrated cryogenic parameter layer remain future work.

## Slide 5 — 3:10–4:10 (60 s)

The strongest architectural issue in the current model appears at coarse-region boundaries. Parasitic capacitance reduces the fine-DAC span. When the lower reference advances, the output jumps across a missing voltage range. In this example, the boundary jump is about eight millivolts. A gain-and-offset correction can change the code mapping, but it cannot create voltages that the hardware cannot produce. The right plot reuses the paper’s intermediate-step idea: temporarily double the reference span and insert extra levels. In the model, the largest adjacent gap falls from about sixty-six-and-a-half to one-point-nine nominal LSBs. That is promising, but the intermediate region has coarser spacing, and full-scale coverage still needs work.

### Sources
Project: docs/figures/v2_coarse_jump_compensation.png; model/bias_dac_v2.py, plot_coarse_jump_and_compensation(), intermediate_sequence(), coverage().
[1] P. Vliex et al., "Bias Voltage DAC Operating at Cryogenic Temperatures for Solid-State Qubit Applications," IEEE Solid-State Circuits Letters, vol. 3, pp. 218–221, 2020. https://doi.org/10.1109/LSSC.2020.3011576 Section IV-C and Fig. 9.

### Technical backup (not part of the timed script)
These are project behavioral simulations, not reproduction of measured silicon. The two plotted panels are reused from the original figure. α=0.064 is a paper-informed modeling point, not an extracted 180 nm parasitic. Plot (a) uses DAC input word; plot (b) uses sequence index after added settings. Maximum adjacent achievable-voltage gap: 66.5 LSB before and 1.9 LSB after intermediate steps. That metric does not include missing full-scale endpoint coverage. The repo’s target-distance plot shows a remaining top-of-range error near 1 V, so do not claim <1 LSB accuracy over the complete range. Nominal 13-bit LSB =122.07 µV; the inserted settings use a 250 mV reference span.

## Slide 6 — 4:10–5:00 (50 s)

The next step is to turn these model findings into a circuit design. First, we will combine intermediate steps or intentional region overlap with digital gain-and-offset compensation, including the endpoint coverage. Second, we will compare capacitor coding options using the same accuracy and capacitance budgets. Third, we will move into TSMC one-eighty-nanometer Cadence schematics, simulation, layout and extraction. That stage must quantify switch settling, charge injection, storage leakage, and temperature-dependent device shifts. The cryogenic checks will depend on model availability. Success means demonstrating the required bias coverage with a refresh rate and power budget that we can justify from the circuit.

### Sources
Project: docs/phase2_cryo_architecture_research.md, Sections 7–10; spice/README.md; model/bias_dac_v2.py.
AMS_Senior_Design_Pitch_Reference.docx, Section 4, Bias Voltage DAC / Cryo-CMOS (Fall 2026).
TSMC 180 nm Cadence implementation is the user-specified project direction.

### Technical backup (not part of the timed script)
Checked-in SPICE files currently use ideal switches and behavioral sources; README marks them unverified by simulation. Do not describe them as completed transistor-level validation. Charge injection, switch Ron, noise, cryogenic parameter shifts, and post-layout parasitics require additional modeling or circuit evaluation. Standard PDK corners alone do not establish operation at 6 K. Retain temperature and leakage sensitivity studies if validated cryogenic compact models are unavailable.