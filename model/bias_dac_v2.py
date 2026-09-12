"""
Bias Voltage DAC Behavioral Model — v2 (architecture-aware)
===========================================================
Phase 2 deliverable. v1 (bias_voltage_dac_model.py) is left untouched.

Pipeline (every non-ideality has its own enable flag in DACParams):

    DAC parameters
        -> ideal capacitor DAC          (binary | segmented | bwa, + dummy unit)
        -> capacitor mismatch           (enable_mismatch, sigma_u per unit cap)
        -> parasitic top-plate C_p      (enable_parasitic, alpha)  -> region gain (1-alpha)
        -> gain + offset                (enable_gain_error, enable_offset)
        -> reference / coarse tuning    (enable_coarse_tuning, VU/VL from a reference ladder)
        -> S&H channel                  (charge sharing DAC <-> C_storage, no buffer)
        -> leakage / refresh            (I_leak, f_R, N channels)
        -> output voltage

Source tags used in comments:
    [Paper]      Vliex et al., IEEE SSC-L 2020 (Section / Fig. / Table given)
    [Paper-read] value read off a figure of the paper (limited precision)
    [Assume]     our behavioral-model assumption (not given in the paper)
    [Inference]  our derivation

Run:  python model/bias_dac_v2.py      -> writes plots into docs/figures/
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

import numpy as np
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

FIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "docs", "figures")

# ----------------------------------------------------------------------------
# Parameters
# ----------------------------------------------------------------------------
@dataclass
class DACParams:
    # --- fine capacitive DAC -------------------------------------------------
    n_fine: int = 10            # [Paper Sec. III/IV-C] ~10-bit cap array
    arch: str = "binary"        # "binary" | "segmented" | "bwa"
    m_therm: int = 0            # thermometer MSBs when arch == "segmented"
    c_unit: float = 5e-15       # [Assume] unit capacitor, only used for absolute C (S&H, power)
    # --- mismatch -------------------------------------------------------------
    enable_mismatch: bool = False
    sigma_u: float = 0.003      # [Paper Sec. IV-C] sigma0 = 0.003 C0 (inferred by the paper)
    seed: int = 0
    # --- parasitic / region gain --------------------------------------------
    enable_parasitic: bool = False
    alpha: float = 0.064        # [Paper-read Fig. 9(a)] ~8 mV jump / 125 mV span
    reset_to: str = "vl"        # "vl": top plate reset to VL (region start pinned) | "gnd"
    # --- gain / offset (global, behavioral) ----------------------------------
    enable_gain_error: bool = False
    gain: float = 1.0
    enable_offset: bool = False
    offset: float = 0.0
    # --- coarse reference tuning ---------------------------------------------
    enable_coarse_tuning: bool = True
    v_full: float = 1.0         # [Paper Table I] 0 V .. 1 V
    n_regions: int = 8          # [Paper Sec. III] 8 references -> +3 bit
    # derived
    _w: np.ndarray = field(default=None, repr=False)
    _S: np.ndarray = field(default=None, repr=False)

    # ------------------------------------------------------------------------
    @property
    def n_codes_fine(self):
        return 2 ** self.n_fine

    @property
    def n_total_bits(self):
        return self.n_fine + (int(np.log2(self.n_regions)) if self.enable_coarse_tuning else 0)

    @property
    def n_codes_total(self):
        return 2 ** self.n_total_bits

    @property
    def lsb(self):
        """Nominal LSB of the complete DAC."""
        return self.v_full / self.n_codes_total

    @property
    def region_span(self):
        return self.v_full / self.n_regions if self.enable_coarse_tuning else self.v_full


# ----------------------------------------------------------------------------
# Capacitor array construction
# ----------------------------------------------------------------------------
def build_array(p: DACParams):
    """Nominal element weights (in units of C_unit) and control matrix S[code, elem].
    A dummy unit (always at VL) is appended so that C_total = 2^n and
    full-scale = (2^n - 1)/2^n * (VU - VL)."""
    n = p.n_fine
    codes = np.arange(2 ** n)
    if p.arch == "binary":
        w = 2 ** np.arange(n)
        S = ((codes[:, None] >> np.arange(n)) & 1).astype(np.int8)
    elif p.arch == "segmented":
        n_lsb = n - p.m_therm
        n_t = 2 ** p.m_therm - 1
        w = np.concatenate([np.full(n_t, 2 ** n_lsb), 2 ** np.arange(n_lsb)])
        msb = codes >> n_lsb
        lsb = codes & (2 ** n_lsb - 1)
        S = np.concatenate([
            (np.arange(n_t)[None, :] < msb[:, None]).astype(np.int8),
            ((lsb[:, None] >> np.arange(n_lsb)) & 1).astype(np.int8)], axis=1)
    elif p.arch == "bwa":
        # split array: n_l LSB bits | C_A | n_m MSB bits   [Paper Sec. III, Fig. 2]
        n_l = n // 2
        n_m = n - n_l
        w = np.concatenate([2 ** np.arange(n_l), 2 ** np.arange(n_m)])
        S = ((codes[:, None] >> np.arange(n)) & 1).astype(np.int8)
    else:
        raise ValueError(p.arch)
    return w, S


def draw_mismatch(p: DACParams, rng: np.random.Generator, w: np.ndarray):
    """Each element of w units is built from w independent unit caps:
    relative error sigma_u / sqrt(w). Returns actual element values (units),
    dummy value and (for bwa) attenuation-cap value."""
    if p.enable_mismatch:
        elem = w * (1 + rng.normal(0, p.sigma_u / np.sqrt(w)))
        dummy = 1.0 * (1 + rng.normal(0, p.sigma_u))
        c_a = None
        if p.arch == "bwa":
            n_l = p.n_fine // 2
            c_a_nom = 2 ** n_l / (2 ** n_l - 1)        # classic split-array value
            c_a = c_a_nom * (1 + rng.normal(0, p.sigma_u))
    else:
        elem = w.astype(float)
        dummy = 1.0
        c_a = (2 ** (p.n_fine // 2) / (2 ** (p.n_fine // 2) - 1)) if p.arch == "bwa" else None
    return elem, dummy, c_a


# ----------------------------------------------------------------------------
# Fine DAC transfer (one coarse region): returns normalised delta = (V - Vbase)/(VU - VL)
# ----------------------------------------------------------------------------
def fine_gain_curve(p: DACParams, elem, dummy, c_a, S):
    """delta[code] in units of (VU - VL), including mismatch and parasitic.
    [Inference] charge conservation on the floating top plate."""
    alpha = p.alpha if p.enable_parasitic else 0.0
    if p.arch in ("binary", "segmented"):
        c_tot = elem.sum() + dummy
        c_p = alpha / (1 - alpha) * c_tot
        return (S @ elem) / (c_tot + c_p)
    # ---- bwa: 2-node charge conservation -------------------------------------
    n_l = p.n_fine // 2
    eL, eM = elem[:n_l], elem[n_l:]
    SL, SM = S[:, :n_l], S[:, n_l:]
    c_b_eff = eM.sum() + (c_a * (eL.sum() + dummy)) / (c_a + eL.sum() + dummy)
    c_pB = alpha / (1 - alpha) * c_b_eff
    a11 = eL.sum() + dummy + c_a           # node A (LSB top plate), no parasitic assumed
    a22 = eM.sum() + c_a + c_pB            # node B (output top plate)
    r1 = SL @ eL
    r2 = SM @ eM
    det = a11 * a22 - c_a ** 2
    dB = (a11 * r2 + c_a * r1) / det
    return dB


# ----------------------------------------------------------------------------
# Full DAC transfer
# ----------------------------------------------------------------------------
class BiasDAC:
    def __init__(self, p: DACParams):
        self.p = p
        self.w, self.S = build_array(p)
        rng = np.random.default_rng(p.seed)
        self.elem, self.dummy, self.c_a = draw_mismatch(p, rng, self.w)
        self.delta = fine_gain_curve(p, self.elem, self.dummy, self.c_a, self.S)  # per fine code

    # references ---------------------------------------------------------------
    def ref_level(self, k):
        """Reference tap k of the ladder 0, span, 2*span, ... [Paper Fig. 3(b)]"""
        return k * self.p.region_span

    def fine_output(self, k_lo, k_hi, d):
        """Output for reference pair (VL = tap k_lo, VU = tap k_hi) and fine code d."""
        p = self.p
        vl, vu = self.ref_level(k_lo), self.ref_level(k_hi)
        alpha = p.alpha if p.enable_parasitic else 0.0
        v_base = vl if p.reset_to == "vl" else (1 - alpha) * vl   # [Inference] reset pins region start
        v = v_base + (vu - vl) * self.delta[d]
        if p.enable_gain_error:
            v = v * p.gain
        if p.enable_offset:
            v = v + p.offset
        return v

    def transfer(self):
        """Nominal code map: code D -> (region k = D >> n_fine, fine d)."""
        p = self.p
        D = np.arange(p.n_codes_total)
        if p.enable_coarse_tuning:
            k = D >> p.n_fine
            d = D & (p.n_codes_fine - 1)
            return self.fine_output(k, k + 1, d)
        return self.fine_output(0, 1, D)

    # calibration / remapping ----------------------------------------------------
    def intermediate_sequence(self):
        """[Paper Sec. IV-C, Fig. 9(b)] after region k, keep VL = tap k but use
        VU = tap k+2 (double span, double step) until the output reaches the start
        of region k+1, then switch to (k+1, k+2). Returns (settings, voltages)."""
        p = self.p
        settings, volts = [], []
        for k in range(p.n_regions):
            for d in range(p.n_codes_fine):
                settings.append((k, k + 1, d))
                volts.append(self.fine_output(k, k + 1, d))
            if k + 2 <= p.n_regions:
                v_end = volts[-1]
                v_next_start = self.fine_output(k + 1, k + 2, 0)
                for d in range(p.n_codes_fine):
                    v = self.fine_output(k, k + 2, d)
                    if v <= v_end:
                        continue
                    if v >= v_next_start:
                        break
                    settings.append((k, k + 2, d))
                    volts.append(v)
        return settings, np.array(volts)


# ----------------------------------------------------------------------------
# Metrics
# ----------------------------------------------------------------------------
def dnl_inl(v, lsb):
    dnl = np.diff(v) / lsb - 1
    line = np.linspace(v[0], v[-1], len(v))
    inl = (v - line) / lsb
    return dnl, inl


def decompose(v, v_ideal):
    """V_actual = a*V_ideal + b + eps(D), least-squares (a, b)."""
    A = np.vstack([v_ideal, np.ones_like(v_ideal)]).T
    (a, b), *_ = np.linalg.lstsq(A, v, rcond=None)
    eps = v - (a * v_ideal + b)
    return a, b, eps


def coverage(v_achievable, v_full, lsb):
    """Largest gap between adjacent achievable voltages (in LSB) and the fraction
    of the 0..v_full range that is farther than LSB/2 from any achievable value."""
    vs = np.sort(v_achievable)
    gaps = np.diff(vs) / lsb
    targets = np.arange(0, v_full, lsb)
    idx = np.searchsorted(vs, targets)
    idx = np.clip(idx, 1, len(vs) - 1)
    err = np.minimum(np.abs(vs[idx] - targets), np.abs(vs[idx - 1] - targets))
    return gaps.max(), (err > lsb / 2).mean()


def eq1_sigma_dnl(n, sigma0_over_c0):
    """[Paper Eq. (1)] sigma_DNL,BWA ~ 2^(3N/4) * sigma0/C0 (LSB)."""
    return 2 ** (0.75 * n) * sigma0_over_c0


# ----------------------------------------------------------------------------
# S&H channel: charge sharing + leakage + refresh
# ----------------------------------------------------------------------------
@dataclass
class SHParams:
    c_storage: float = 1e-12     # [Assume] storage cap per channel
    c_dac: float = 5.12e-12      # [Assume] 1024 units x 5 fF (plain 10-bit)
    i_leak: float = 1e-12        # [Assume] paper only says "pA" leakage design target [Paper Sec. III-A]
    f_r: float = 3.9e3           # [Paper Sec. IV-C] channel refresh rate
    n_ch: int = 8                # [Paper] 8 channels share one DAC
    t_end: float = 3e-3
    v_target: float = 0.5
    v_init: float = 0.0


def simulate_sh(sh: SHParams, dt=None):
    """Time-domain V_storage for one channel. Every T_R = 1/f_r the DAC (already
    settled at v_target on c_dac) is connected: charge sharing without buffer
    [Paper Sec. III]. Between refreshes: linear droop I_leak/C_storage."""
    t_r = 1 / sh.f_r
    if dt is None:
        dt = min(t_r / 20, sh.t_end / 20000)
    t = np.arange(0, sh.t_end, dt)
    v = np.empty_like(t)
    vs = sh.v_init
    next_refresh = 0.0
    share = sh.c_dac / (sh.c_dac + sh.c_storage)
    for i, ti in enumerate(t):
        if ti >= next_refresh:
            vs = vs + (sh.v_target - vs) * share
            next_refresh += t_r
        v[i] = vs
        vs -= sh.i_leak / sh.c_storage * dt
    droop_per_period = sh.i_leak / sh.c_storage * t_r
    return t, v, droop_per_period


# ----------------------------------------------------------------------------
# Power model (first order, paper baseline)  [Paper Table II, f_R = 3.9 kHz]
# ----------------------------------------------------------------------------
PAPER_POWER_3p9k = {            # W
    "DAC core (Sw&MUX)": 77e-9,
    "DAC reference voltages": 3e-9,
    "DAC digital (memory & logic)": 21e-6,
    "Clock buffer": 4.3e-6,
}
COOLING_BUDGET_100MK = 400e-6   # [Paper Sec. II]


def power_scaled(f_r, dyn_fraction_digital=0.5, core_scale=1.0, elem_scale=1.0):
    """[Assume] core ∝ f_R * C_total (core_scale) ; digital = static + dynamic∝f_R,
    with the dynamic fraction at 3.9 kHz given by dyn_fraction_digital; the
    element-count dependent part (drivers/latches) scaled by elem_scale;
    clock buffer ∝ f_R. Returns dict in W."""
    r = f_r / 3.9e3
    core = PAPER_POWER_3p9k["DAC core (Sw&MUX)"] * r * core_scale * elem_scale
    ref = PAPER_POWER_3p9k["DAC reference voltages"]
    dig = PAPER_POWER_3p9k["DAC digital (memory & logic)"]
    dig = dig * (1 - dyn_fraction_digital) + dig * dyn_fraction_digital * r
    clk = PAPER_POWER_3p9k["Clock buffer"] * r
    return {"core": core, "ref": ref, "digital": dig, "clock": clk,
            "total": core + ref + dig + clk}


# ----------------------------------------------------------------------------
# Plots
# ----------------------------------------------------------------------------
def plot_dnl_vs_code(seed=3):
    os.makedirs(FIG_DIR, exist_ok=True)
    fig, ax = plt.subplots(2, 2, figsize=(13, 8))
    cases = [("binary", 0, "plain binary 10 b"),
             ("bwa", 0, "BWA 5+5 b (paper topology)"),
             ("segmented", 4, "segmented 4T+6B")]
    for (arch, m, lab), a in zip(cases, ax.flat):
        p = DACParams(arch=arch, m_therm=m, enable_mismatch=True, seed=seed,
                      enable_coarse_tuning=False)
        dac = BiasDAC(p)
        v = dac.transfer()
        dnl, _ = dnl_inl(v, (dac.ref_level(1) - dac.ref_level(0)) / p.n_codes_fine)
        a.plot(dnl, lw=0.6)
        a.set_title(f"{lab}: sigma_u = {p.sigma_u}, max|DNL| = {np.abs(dnl).max():.2f} LSB")
        a.set_xlabel("fine code"); a.set_ylabel("DNL [LSB]"); a.grid(True, alpha=.3)
    # full 13-bit with coarse tuning + parasitic (paper-like)
    p = DACParams(arch="bwa", enable_mismatch=True, enable_parasitic=True, seed=seed)
    dac = BiasDAC(p)
    v = dac.transfer()
    dnl, _ = dnl_inl(v, p.lsb)
    a = ax.flat[3]
    a.plot(dnl, lw=0.6)
    a.set_ylim(-3, 3)
    a.set_title(f"BWA, 8 coarse regions, alpha={p.alpha}: boundary DNL = "
                f"{dnl[p.n_codes_fine-1]:.0f} LSB (clipped)", fontsize=10)
    a.set_xlabel("DAC input word (13 b)"); a.set_ylabel("DNL [LSB]"); a.grid(True, alpha=.3)
    fig.suptitle("DNL vs code, one Monte Carlo instance (unit-cap sigma_u = 0.003, paper-inferred)")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "v2_dnl_vs_code.png"), dpi=130)
    plt.close(fig)


def mc_dnl_stats(n_mc=500, sigma_u=0.003):
    rows = []
    for arch, m in [("binary", 0), ("segmented", 3), ("segmented", 4), ("bwa", 0)]:
        std_all, worst = [], []
        for s in range(n_mc):
            p = DACParams(arch=arch, m_therm=m, enable_mismatch=True, sigma_u=sigma_u,
                          seed=s, enable_coarse_tuning=False)
            dac = BiasDAC(p)
            v = dac.transfer()
            dnl, _ = dnl_inl(v, 1.0 / p.n_codes_fine)
            std_all.append(dnl.std())
            worst.append(np.abs(dnl).max())
        name = arch if arch != "segmented" else f"seg {m}T+{10-m}B"
        rows.append((name, np.mean(std_all), np.mean(worst), np.percentile(worst, 99)))
    return rows


def plot_sh_refresh():
    os.makedirs(FIG_DIR, exist_ok=True)
    fig, ax = plt.subplots(1, 3, figsize=(16, 4.6))
    for f_r, c in [(390e3, "tab:blue"), (3.9e3, "tab:orange")]:
        sh = SHParams(f_r=f_r, t_end=2.5e-3)
        t, v, droop = simulate_sh(sh)
        ax[0].plot(t * 1e3, v, c, lw=0.8, label=f"f_R = {f_r/1e3:.1f} kHz, droop/period = {droop*1e6:.1f} uV")
        # zoom on steady state
        m = t > 2.0e-3
        ax[1].plot(t[m] * 1e3, (v[m] - sh.v_target) * 1e6, c, lw=0.8, label=f"f_R = {f_r/1e3:.1f} kHz")
    ax[0].set_xlabel("time [ms]"); ax[0].set_ylabel("V_storage [V]")
    ax[0].set_title("S&H charge-up (no buffer) and leakage\n[Assume] C_storage=1 pF, C_dac=5.12 pF, I_leak=1 pA")
    ax[0].legend(fontsize=8); ax[0].grid(True, alpha=.3)
    ax[1].axhline(-122 / 2, color="gray", ls=":", label="-LSB/2 (61 uV)")
    ax[1].set_xlabel("time [ms]"); ax[1].set_ylabel("V_storage - V_target [uV]")
    ax[1].set_title("steady-state ripple (zoom, 2.0-2.5 ms)")
    ax[1].legend(fontsize=8); ax[1].grid(True, alpha=.3)
    # tradeoff: droop vs f_R for several I_leak/C, and power vs f_R
    f = np.logspace(3, 6, 200)
    for ic, lab in [(1e-12 / 1e-12, "1 pA / 1 pF"), (1e-13 / 1e-12, "100 fA / 1 pF"),
                    (1e-12 / 10e-12, "1 pA / 10 pF"), (1e-14 / 1e-12, "10 fA / 1 pF")]:
        ax[2].loglog(f, ic / f * 1e6, label=f"droop, I/C = {lab}")
    ax[2].axhline(122, color="k", ls="--", lw=0.8, label="1 LSB = 122 uV")
    ax[2].axhline(20, color="k", ls=":", lw=0.8, label="'lower tens of uV' [Paper]")
    ax[2].set_xlabel("channel refresh rate f_R [Hz]"); ax[2].set_ylabel("droop per period [uV]")
    ax2 = ax[2].twinx()
    for frac, ls in [(0.1, "-"), (0.5, "--"), (0.9, ":")]:
        ax2.loglog(f, [power_scaled(x, frac)["total"] * 1e6 for x in f], color="tab:red", ls=ls,
                   lw=0.9, label=f"P_total, digital dyn. fraction {frac}")
    ax2.axhline(400, color="tab:red", lw=0.6, alpha=.5)
    ax2.set_ylabel("estimated total power [uW] (paper baseline 25.4 uW @ 3.9 kHz)", color="tab:red")
    ax[2].axvline(3.9e3, color="gray", lw=0.6); ax[2].axvline(390e3, color="gray", lw=0.6)
    ax[2].set_title("power-droop tradeoff vs f_R")
    ax[2].legend(fontsize=7, loc="lower left"); ax2.legend(fontsize=7, loc="upper right")
    ax[2].grid(True, which="both", alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "v2_sh_refresh_leakage.png"), dpi=130)
    plt.close(fig)


def plot_coarse_jump_and_compensation():
    os.makedirs(FIG_DIR, exist_ok=True)
    p = DACParams(arch="binary", enable_parasitic=True, alpha=0.064)
    dac = BiasDAC(p)
    v = dac.transfer()
    D = np.arange(p.n_codes_total)
    lsb = p.lsb
    # --- (a) jump ------------------------------------------------------------
    fig, ax = plt.subplots(1, 3, figsize=(18, 5))
    m = (D >= 4000) & (D <= 4200)
    ax[0].plot(D[m], v[m], ".", ms=2)
    ax[0].axvspan(4000, 4095, color="tab:orange", alpha=.15); ax[0].axvspan(4096, 4200, color="tab:green", alpha=.15)
    ax[0].set_title(f"(a) coarse-region jump, alpha = {p.alpha}\n"
                    f"jump = {(v[4096]-v[4095])/lsb:.0f} LSB = {(v[4096]-v[4095])*1e3:.1f} mV", fontsize=10)
    ax[0].set_xlabel("DAC input word"); ax[0].set_ylabel("V_out [V]"); ax[0].grid(True, alpha=.3)
    # gnd-reset variant for comparison
    p2 = DACParams(arch="binary", enable_parasitic=True, alpha=0.064, reset_to="gnd")
    v2 = BiasDAC(p2).transfer()
    ax[0].plot(D[m], v2[m], ".", ms=1.5, color="gray", label="same C_p, top plate reset to GND (global gain only)")
    ax[0].legend(fontsize=7)
    # --- (b) intermediate steps --------------------------------------------------
    settings, vs = dac.intermediate_sequence()
    seq = np.arange(len(vs))
    n_int = sum(1 for s in settings if s[1] - s[0] == 2)
    m2 = (seq >= 4000) & (seq <= 4300 + n_int // 7)
    col = ["tab:blue" if s[1] - s[0] == 1 else "tab:red" for s in settings]
    ax[1].scatter(seq[m2], vs[m2], c=np.array(col)[m2], s=4)
    ax[1].set_title(f"(b) intermediate 250-mV span (red), as Fig. 9(b):\n"
                    f"{n_int//7} extra codes per boundary, step = 2 LSB, total words = {len(vs)}", fontsize=10)
    ax[1].set_xlabel("sequence index"); ax[1].set_ylabel("V_out [V]"); ax[1].grid(True, alpha=.3)
    # --- (c) coverage comparison: none / global 2-pt / per-region 2-pt / intermediate
    gap0, miss0 = coverage(v, p.v_full, lsb)
    gap_i, miss_i = coverage(vs, p.v_full, lsb)
    # global 2-point: relabel codes, achievable set unchanged -> same coverage
    a, b, eps = decompose(v, D * lsb)
    # per-region 2-point: same achievable set
    txt = (f"achievable-voltage coverage of 0..1 V (LSB = {lsb*1e6:.0f} uV)\n\n"
           f"no compensation        : max gap {gap0:5.1f} LSB, {miss0*100:4.1f}% of targets unreachable (>LSB/2)\n"
           f"global 2-pt gain/offset: max gap {gap0:5.1f} LSB, {miss0*100:4.1f}% (relabels codes only; a={a:.3f}, b={b*1e3:.2f} mV)\n"
           f"per-region 2-pt        : max gap {gap0:5.1f} LSB, {miss0*100:4.1f}% (corrects slope, cannot create voltages)\n"
           f"intermediate 250-mV    : max gap {gap_i:5.1f} LSB, {miss_i*100:4.1f}%\n\n"
           f"[Inference] the jump is a missing output range, not a code-labelling error:\n"
           f"only a method that adds achievable voltages (wider span, overlap) can fix it.")
    ax[2].axis("off"); ax[2].text(0.0, 0.5, txt, family="monospace", fontsize=8.5, va="center")
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "v2_coarse_jump_compensation.png"), dpi=130)
    plt.close(fig)
    # --- separate full-range residual plot: global calibration leaves the jumps ----
    fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
    ax[0].plot(D, eps / lsb, lw=0.6)
    ax[0].set_title(f"residual eps(D) after GLOBAL 2-pt fit (a={a:.4f}, b={b*1e3:.2f} mV)")
    ax[0].set_xlabel("DAC input word"); ax[0].set_ylabel("eps [LSB]"); ax[0].grid(True, alpha=.3)
    # coverage error: distance from every 13-bit target voltage to the nearest achievable output
    targets = np.arange(0, p.v_full, lsb)
    for vv, lab, c in [(v, "no compensation / global or per-region 2-pt (same achievable set)", "tab:blue"),
                       (vs, "with intermediate 250-mV steps", "tab:red")]:
        s = np.sort(vv)
        idx = np.clip(np.searchsorted(s, targets), 1, len(s) - 1)
        err = np.minimum(np.abs(s[idx] - targets), np.abs(s[idx - 1] - targets)) / lsb
        ax[1].plot(targets, err, lw=0.7, color=c, label=lab)
    ax[1].axhline(0.5, color="gray", ls=":", label="LSB/2")
    ax[1].set_title("distance from target voltage to nearest achievable output\n"
                    "(calibration relabels codes; only added voltages close the gaps)", fontsize=10)
    ax[1].set_xlabel("target voltage [V]"); ax[1].set_ylabel("|error| [LSB]"); ax[1].set_yscale("symlog", linthresh=1)
    ax[1].legend(fontsize=7); ax[1].grid(True, alpha=.3)
    fig.tight_layout()
    fig.savefig(os.path.join(FIG_DIR, "v2_jump_global_vs_region_cal.png"), dpi=130)
    plt.close(fig)
    return dict(jump_lsb=(v[4096] - v[4095]) / lsb, n_int_per_boundary=n_int // 7,
                n_words=len(vs), gap0=gap0, miss0=miss0, gap_i=gap_i, miss_i=miss_i, a=a, b=b)


def plot_alpha_sweep():
    """Sensitivity: jump size and required intermediate codes vs alpha (alpha not given in paper)."""
    os.makedirs(FIG_DIR, exist_ok=True)
    alphas = np.linspace(0.0, 0.15, 16)
    jump, n_int, total = [], [], []
    for al in alphas:
        p = DACParams(arch="binary", enable_parasitic=al > 0, alpha=max(al, 1e-9))
        dac = BiasDAC(p)
        v = dac.transfer()
        jump.append((v[4096] - v[4095]) / p.lsb)
        s, vs = dac.intermediate_sequence()
        n = sum(1 for x in s if x[1] - x[0] == 2)
        n_int.append(n / 7); total.append(len(vs))
    fig, ax = plt.subplots(1, 2, figsize=(11, 4))
    ax[0].plot(alphas, jump, "o-"); ax[0].set_xlabel("alpha = C_p/(C_tot+C_p)"); ax[0].set_ylabel("boundary jump [LSB]")
    ax[0].axvline(0.064, color="gray", ls=":", label="Fig. 9(a) reading"); ax[0].legend(); ax[0].grid(True, alpha=.3)
    ax[1].plot(alphas, n_int, "o-", label="intermediate codes per boundary"); ax[1].plot(alphas, np.array(total) - 8192, "s-", label="total extra words")
    ax[1].set_xlabel("alpha"); ax[1].legend(); ax[1].grid(True, alpha=.3)
    fig.suptitle("sensitivity to the (unknown) parasitic ratio alpha")
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "v2_alpha_sweep.png"), dpi=130); plt.close(fig)


def plot_mismatch_sweep():
    os.makedirs(FIG_DIR, exist_ok=True)
    sig = [0.001, 0.002, 0.003, 0.005, 0.01, 0.02]
    fig, ax = plt.subplots(figsize=(7, 4.5))
    for arch, m, lab in [("binary", 0, "plain binary"), ("segmented", 4, "seg 4T+6B"), ("bwa", 0, "BWA 5+5")]:
        worst = []
        for s in sig:
            w = []
            for seed in range(150):
                p = DACParams(arch=arch, m_therm=m, enable_mismatch=True, sigma_u=s, seed=seed,
                              enable_coarse_tuning=False)
                v = BiasDAC(p).transfer()
                dnl, _ = dnl_inl(v, 1 / p.n_codes_fine)
                w.append(np.abs(dnl).max())
            worst.append(np.mean(w))
        ax.loglog(sig, worst, "o-", label=f"{lab}: mean max|DNL| (MC)")
    ax.loglog(sig, [eq1_sigma_dnl(10, s) for s in sig], "k--", label="Eq. (1) [Paper]: 2^(3N/4)*sigma0/C0")
    ax.axhline(0.495, color="gray", ls=":", label="paper measured sigma_D = 0.495 LSB")
    ax.axvline(0.003, color="gray", ls=":")
    ax.set_xlabel("unit-cap mismatch sigma_u"); ax.set_ylabel("DNL [LSB]"); ax.legend(fontsize=8); ax.grid(True, which="both", alpha=.3)
    ax.set_title("capacitor mismatch -> DNL, 10-bit fine DAC (MC vs paper Eq. (1))")
    fig.tight_layout(); fig.savefig(os.path.join(FIG_DIR, "v2_mismatch_sweep.png"), dpi=130); plt.close(fig)


# ----------------------------------------------------------------------------
def main():
    os.makedirs(FIG_DIR, exist_ok=True)
    # sanity: ideal transfer is exactly linear for every architecture
    for arch, m in [("binary", 0), ("segmented", 4), ("bwa", 0)]:
        p = DACParams(arch=arch, m_therm=m)
        v = BiasDAC(p).transfer()
        dnl, inl = dnl_inl(v, p.lsb)
        print(f"ideal {arch:9s}: max|DNL| = {np.abs(dnl).max():.2e}, max|INL| = {np.abs(inl).max():.2e}, "
              f"Vmax = {v[-1]:.6f} V")

    print("\nMonte Carlo DNL statistics, 10-bit fine DAC, sigma_u = 0.003 (500 runs):")
    print("  arch         | std(DNL over codes) | mean max|DNL| | 99% max|DNL|")
    for name, s, w, w99 in mc_dnl_stats():
        print(f"  {name:12s} | {s:19.3f} | {w:13.3f} | {w99:12.3f}")
    print(f"  Eq. (1) analytic [Paper]: sigma_DNL,BWA = {eq1_sigma_dnl(10, 0.003):.3f} LSB ;"
          f" paper measured sigma_D = 0.495 LSB")

    plot_dnl_vs_code()
    plot_sh_refresh()
    r = plot_coarse_jump_and_compensation()
    print("\nCoarse-region jump (alpha = 0.064 [Paper-read]):")
    for k, val in r.items():
        print(f"  {k}: {val}")
    plot_alpha_sweep()
    plot_mismatch_sweep()

    print("\nPower scaling (paper Table II baseline @ 3.9 kHz):")
    for f_r in [3.9e3, 39e3, 390e3]:
        for frac in [0.1, 0.5, 0.9]:
            pw = power_scaled(f_r, frac)
            print(f"  f_R = {f_r/1e3:6.1f} kHz, digital dyn. fraction {frac}: total = {pw['total']*1e6:7.1f} uW "
                  f"(core {pw['core']*1e9:7.1f} nW, digital {pw['digital']*1e6:6.1f} uW, clock {pw['clock']*1e6:6.1f} uW)")
    print(f"\nplots written to {FIG_DIR}")


if __name__ == "__main__":
    main()
