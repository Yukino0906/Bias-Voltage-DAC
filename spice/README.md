# SPICE netlists — charge-redistribution bias DAC

Both files use ngspice syntax (ideal `SW` switches, B-sources for the switch logic, `.param` code bits).
No simulator is installed on this machine, so the netlists are unverified by simulation. Expected values in the comments were computed with `model/bias_dac_v2.py` (same charge-conservation equations).

| File | Content |
|---|---|
| `cr_dac_binary_4bit.sp` | Minimal: 4-bit plain binary array, one coarse region (V_L = 375 mV, V_U = 500 mV), reset to V_L, top-plate parasitic, DEMUX/S&H with leakage and refresh. Start here. |
| `cr_dac_bwa_10bit.sp` | Paper topology: 5-bit LSB sub-array + attenuation cap C_A = 32/31 C0 + 5-bit MSB sub-array, same phases and S&H. Parameters `ALPHA` (parasitic ratio), `VUREF` (set 0.625 for the 250-mV intermediate span), `FR` (3.9 kHz / 390 kHz), `ILEAK`, `CST`, `D` (fine code). |

Phase scheme per refresh period `T_R = 1/FR` (one channel shown; `TSLOT = T_R / 8` is the channel's slot):

```
rst  : |‾‾|_______________________________________|   0 .. 10 % of TSLOT   top plates + all bottom plates to V_L
conv : |__|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|____|   10 .. 95 %            bit=1 bottom plates to V_U, top plates float
smp  : |__________|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|__________|   40 .. 90 %            DEMUX closes: charge sharing into C_storage
```

Run (batch):

```bash
ngspice -b spice/cr_dac_bwa_10bit.sp
```

The `.control` block prints `v_dac_conv` (DAC top plate during conversion), `v_st_after1/5` (storage cap after 1 and 5 refreshes) and writes `cr_dac_bwa_out.txt` for plotting. LTspice: delete the `.control` block and use `.meas`; everything else is accepted.

What to look at:
- `v(nb)` during `conv` = V_L + (V_U − V_L)·(1 − ALPHA)·D/1024. With ALPHA = 0.064 and D = 1023 it stops 8 mV short of V_U: this is the Fig. 9(a) gap.
- `v(nst)` steps toward `v(nb)` by the factor C_B,eff / (C_B,eff + C_storage) per refresh (no buffer) and droops by ILEAK·T_R/C_storage between refreshes.
