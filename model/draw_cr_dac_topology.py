# Draws docs/figures/cr_dac_topology.png.  Requires: pip install schemdraw.  Run from repo root.
import schemdraw
from schemdraw import elements as elm

YT, YB, YU, YL = 7.2, 4.6, 1.6, 0.6
FS = 9
L = lambda x, y, t, **k: d.add(elm.Label().at((x, y)).label(t, fontsize=k.pop("fs", FS), halign=k.pop("ha", "center"), **k))

with schemdraw.Drawing(file="docs/figures/cr_dac_topology.png", show=False, dpi=160) as d:
    d.config(unit=2.0, fontsize=FS, lw=1.3)

    def cell(x, cname, wlabel, bit):
        d.add(elm.Capacitor().at((x, YT)).down().to((x, YB)))
        L(x + 0.15, (YT + YB) / 2 + 0.05, f"{cname}\n{wlabel}", ha="left")
        d.add(elm.Dot().at((x, YB)))
        d.add(elm.Line().at((x, YB)).left().length(0.45))
        d.add(elm.Switch().at((x - 0.45, YB)).down().to((x - 0.45, YU)))
        L(x - 0.75, (YB + YU) / 2, f"{bit}", ha="right")
        d.add(elm.Dot().at((x - 0.45, YU)))
        d.add(elm.Line().at((x, YB)).right().length(0.45))
        d.add(elm.Switch().at((x + 0.45, YB)).down().to((x + 0.45, YL)))
        L(x + 0.75, (YB + YU) / 2, f"/{bit}", ha="left")
        d.add(elm.Dot().at((x + 0.45, YL)))

    # LSB sub-array (node A)
    xs_l = [1.4, 4.0, 7.0]
    cell(xs_l[0], "C_L0", "C0", "b0"); cell(xs_l[1], "C_L1", "2C0", "b1")
    L(5.5, (YT + YB) / 2, "...", fs=14)
    cell(xs_l[2], "C_L4", "16C0", "b4")
    xd = 9.0
    d.add(elm.Capacitor().at((xd, YT)).down().to((xd, YB))); L(xd + 0.15, (YT + YB) / 2 + 0.05, "C_dummy\nC0", ha="left")
    d.add(elm.Line().at((xd, YB)).down().to((xd, YL))); d.add(elm.Dot().at((xd, YL)))
    d.add(elm.Line().at((xs_l[0], YT)).right().to((xd, YT)))
    L(5.2, YT + 0.45, "node A: LSB sub-array top plate")

    # attenuation cap
    xa1 = 11.2
    d.add(elm.Capacitor().at((xd, YT)).right().to((xa1, YT)))
    L((xd + xa1) / 2, YT + 0.5, "C_A = 32/31 C0 (attenuation)")

    # MSB sub-array (node B)
    xs_m = [12.0, 14.6, 17.6]
    cell(xs_m[0], "C_M0", "C0", "b5"); cell(xs_m[1], "C_M1", "2C0", "b6")
    L(16.1, (YT + YB) / 2, "...", fs=14)
    cell(xs_m[2], "C_M4", "16C0", "b9")
    xb_end = 20.8
    d.add(elm.Line().at((xa1, YT)).right().to((xb_end, YT)))
    L(15.4, YT + 0.45, "node B: MSB sub-array top plate = DAC output")

    # parasitic
    xp = 19.4
    d.add(elm.Dot().at((xp, YT)))
    d.add(elm.Capacitor().at((xp, YT)).down().length(1.6)); L(xp + 0.15, YT - 0.8, "C_p\n(parasitic)", ha="left")
    d.add(elm.Ground().at((xp, YT - 1.6)))

    # reset switch to V_L
    d.add(elm.Dot().at((xb_end, YT)))
    d.add(elm.Switch().at((xb_end, YT)).up().length(1.6)); L(xb_end - 0.5, YT + 1.0, "RST", ha="right")
    d.add(elm.Line().at((xb_end, YT + 1.6)).left().to((0.8, YT + 1.6)))
    L(0.8, YT + 1.9, "V_L (reset reference: pins region start at V_L)", ha="left")

    # DEMUX + S/H
    d.add(elm.Switch().at((xb_end, YT)).right().length(2.0)); L(xb_end + 1.1, YT + 0.5, "DEMUX ch. k (1 of 8)")
    d.add(elm.Resistor().at((xb_end + 2.0, YT)).right().length(2.0)); L(xb_end + 3.0, YT + 0.5, "R_series")
    xs = xb_end + 4.0
    d.add(elm.Dot().at((xs, YT)))
    d.add(elm.Capacitor().at((xs, YT)).down().length(1.6)); L(xs - 0.15, YT - 0.8, "C_storage", ha="right")
    d.add(elm.Ground().at((xs, YT - 1.6)))
    xi = xs + 1.6
    d.add(elm.Line().at((xs, YT)).right().to((xi, YT))); d.add(elm.Dot().at((xi, YT)))
    d.add(elm.SourceI().at((xi, YT)).down().length(1.6).reverse()); L(xi + 0.35, YT - 0.8, "I_leak", ha="left")
    d.add(elm.Ground().at((xi, YT - 1.6)))
    d.add(elm.Inductor().at((xi, YT)).right().length(2.0)); L(xi + 1.0, YT + 0.5, "bond wire")
    xe = xi + 2.0
    d.add(elm.Capacitor().at((xe, YT)).down().length(1.6)); L(xe + 0.15, YT - 0.8, "C_electrode\n(qubit gate)", ha="left")
    d.add(elm.Ground().at((xe, YT - 1.6)))
    L(xs + 1.8, YT + 1.2, "S/H channel k  (x8, one per output; DEMUX selects one at a time)")

    # rails
    d.add(elm.Line().at((0.6, YU)).right().to((xs_m[2] - 0.45, YU)))
    L(0.6, YU - 0.35, "V_U = ladder tap k+1   (ladder: 0..1 V in 125 mV steps; 6-bit MUX selects V_U and V_L independently)", ha="left")
    d.add(elm.Line().at((0.6, YL)).right().to((xs_m[2] + 0.45, YL)))
    L(0.6, YL - 0.35, "V_L = ladder tap k", ha="left")
    L(0.6, YL - 0.9, "switch b_i closes to V_U when bit i = 1;  /b_i closes to V_L when bit i = 0 (and for all bits during reset)", ha="left", fs=8)

    L(0.6, -1.2, "Conversion cycle:  (1) RST closed, all bottom plates at V_L   ->   (2) RST open, bit=1 bottom plates to V_U:  "
                 "V_B = V_L + (V_U - V_L) * C_on(D) / (C_tot + C_p)   ->   (3) DEMUX ch. k closed: charge sharing into C_storage (no buffer)   ->   repeat every T_R = 1/f_R", ha="left", fs=8)
    L(0.6, YT + 2.7, "Charge-redistribution bias DAC topology (after Vliex et al., IEEE SSC-L 2020, Fig. 2 and Fig. 3b): split array 5+5 bit with attenuation cap C_A.  "
                     "C_p, RST-to-V_L and I_leak are our inference / behavioral assumptions.", ha="left", fs=10)
