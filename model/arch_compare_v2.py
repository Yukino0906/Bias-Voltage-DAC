"""
Architecture comparison: Binary vs Thermometer vs Segmented capacitive DAC
=========================================================================
Phase 2 support script (does NOT modify the v1 model in bias_voltage_dac_model.py).

Purpose
-------
Compare, under the SAME unit-element mismatch, how the digital coding of a
charge-redistribution DAC affects DNL / INL / monotonicity / switching activity.

Model
-----
* Every weight is built from unit capacitors C_u with independent random
  error:  C_u,i = C_u * (1 + N(0, sigma_u)).
  -> a weight of 2^k units has relative error sigma_u / sqrt(2^k) (area-law
     matching, Pelgrom-like). This is the fair comparison: binary and
     thermometer use the same total unit-capacitor area.
* Output of a charge-redistribution DAC (no attenuation capacitor, ideal
  switches, no parasitics):
      Vout(D) = Vref * C_on(D) / C_total
  The division by C_total means gain error from mismatch is absorbed; what
  remains is code-dependent nonlinearity epsilon(D).
* DNL_k = (V_k - V_{k-1}) / LSB - 1,  INL from endpoint-fit line.

Coding schemes
--------------
  binary      : N binary-weighted elements, weights 2^0 .. 2^(N-1)
  thermometer : 2^N - 1 unit elements, unary control
  segmented   : M thermometer-coded MSB elements (each 2^(N-M) units)
                + (N-M) binary-coded LSB elements

Run:  python model/arch_compare_v2.py
"""
import numpy as np

N_BITS   = 10        # fine DAC resolution (paper: ~10 bit inside cap array)
SIGMA_U  = 0.003     # unit-capacitor relative mismatch (paper: sigma0 = 0.003 C0)
N_MC     = 2000      # Monte Carlo runs
SEED     = 1


def element_weights(scheme, n_bits, m_therm=0):
    """Return nominal element weights (in units) and the control matrix
    S[code, element] in {0,1}."""
    codes = np.arange(2 ** n_bits)
    if scheme == "binary":
        w = 2 ** np.arange(n_bits)
        S = ((codes[:, None] >> np.arange(n_bits)) & 1).astype(np.int8)
    elif scheme == "thermometer":
        n_el = 2 ** n_bits - 1
        w = np.ones(n_el, dtype=int)
        S = (np.arange(n_el)[None, :] < codes[:, None]).astype(np.int8)
    elif scheme == "segmented":
        n_lsb = n_bits - m_therm
        n_t = 2 ** m_therm - 1
        w_t = np.full(n_t, 2 ** n_lsb)
        w_b = 2 ** np.arange(n_lsb)
        w = np.concatenate([w_t, w_b])
        msb = codes >> n_lsb
        lsb = codes & (2 ** n_lsb - 1)
        S_t = (np.arange(n_t)[None, :] < msb[:, None]).astype(np.int8)
        S_b = ((lsb[:, None] >> np.arange(n_lsb)) & 1).astype(np.int8)
        S = np.concatenate([S_t, S_b], axis=1)
    else:
        raise ValueError(scheme)
    return w, S


def decoder_gate_estimate(scheme, n_bits, m_therm=0):
    """Very rough digital-complexity proxy: number of 2-input gate
    equivalents for the code -> switch-control mapping (excludes memory,
    timing, level shifters). binary: ~0 (direct). thermometer of m bits:
    ~ (2^m - 1) outputs, each ~ m-1 gate-equivalents (worst-case)."""
    if scheme == "binary":
        return 0
    m = n_bits if scheme == "thermometer" else m_therm
    return (2 ** m - 1) * max(m - 1, 1)


def simulate(scheme, n_bits, m_therm=0, sigma_u=SIGMA_U, n_mc=N_MC, seed=SEED):
    rng = np.random.default_rng(seed)
    w, S = element_weights(scheme, n_bits, m_therm)
    n_codes = 2 ** n_bits
    lsb_nom = 1.0 / n_codes            # Vref = 1
    dnl_max = np.empty(n_mc)
    inl_max = np.empty(n_mc)
    dnl_all = np.empty((n_mc, n_codes - 1))
    nonmono = 0
    for i in range(n_mc):
        # each element of weight w_j is a sum of w_j unit caps -> relative
        # error sigma_u/sqrt(w_j)
        c = w * (1 + rng.normal(0, sigma_u / np.sqrt(w)))
        c_total = c.sum() + 1.0 * 0   # (no dummy / attenuation cap here)
        vout = (S @ c) / (c_total + 0)  # Vref normalised
        # normalise so that full-scale + 1 LSB = Vref (C_total includes all elements)
        vout = vout * (n_codes - 1) / n_codes / vout[-1] if vout[-1] > 0 else vout
        step = np.diff(vout)
        dnl = step / lsb_nom - 1
        ideal_line = np.linspace(vout[0], vout[-1], n_codes)
        inl = (vout - ideal_line) / lsb_nom
        dnl_all[i] = dnl
        dnl_max[i] = np.abs(dnl).max()
        inl_max[i] = np.abs(inl).max()
        if (step < 0).any():
            nonmono += 1
    # switching activity: number of elements toggled per +1 code step
    toggles = np.abs(np.diff(S.astype(int), axis=0)).sum(axis=1)
    # charge moved per step, in units (sum of |delta weight|)
    charge_moved = (np.abs(np.diff(S.astype(int), axis=0)) * w[None, :]).sum(axis=1)
    return dict(
        scheme=scheme, m=m_therm,
        n_elements=len(w),
        n_switches=len(w),               # one switch (pair) per element
        decoder_gates=decoder_gate_estimate(scheme, n_bits, m_therm),
        dnl_sigma=dnl_all.std(),
        dnl_max_mean=dnl_max.mean(),
        dnl_max_99=np.percentile(dnl_max, 99),
        inl_max_mean=inl_max.mean(),
        inl_max_99=np.percentile(inl_max, 99),
        p_nonmono=nonmono / n_mc,
        toggles_mean=toggles.mean(), toggles_max=toggles.max(),
        charge_mean=charge_moved.mean(), charge_max=charge_moved.max(),
    )


def main():
    cases = [
        ("binary", 0),
        ("segmented", 2),
        ("segmented", 3),
        ("segmented", 4),
        ("segmented", 5),
        ("thermometer", 0),
    ]
    print(f"N = {N_BITS} bit, sigma_u = {SIGMA_U} (unit cap), {N_MC} Monte Carlo runs\n")
    hdr = ("scheme        | elem | dec.gates | DNL sigma | max|DNL| mean/99% | "
           "max|INL| mean/99% | P(non-mono) | toggles mean/max | charge mean/max")
    print(hdr); print("-" * len(hdr))
    for scheme, m in cases:
        r = simulate(scheme, N_BITS, m)
        name = f"{scheme}" if scheme != "segmented" else f"seg {m}T+{N_BITS-m}B"
        print(f"{name:13s} | {r['n_elements']:4d} | {r['decoder_gates']:9d} | "
              f"{r['dnl_sigma']:9.3f} | {r['dnl_max_mean']:6.3f} / {r['dnl_max_99']:5.3f}   | "
              f"{r['inl_max_mean']:6.3f} / {r['inl_max_99']:5.3f}   | "
              f"{r['p_nonmono']:11.4f} | {r['toggles_mean']:5.2f} / {r['toggles_max']:3d}     | "
              f"{r['charge_mean']:6.1f} / {r['charge_max']:5.0f}")

    # sensitivity: sigma_u sweep for binary vs 4T+6B
    print("\nsigma_u sweep (max|DNL| mean, P(non-mono)):")
    for s in [0.003, 0.01, 0.02, 0.03]:
        rb = simulate("binary", N_BITS, 0, sigma_u=s, n_mc=500)
        rs = simulate("segmented", N_BITS, 4, sigma_u=s, n_mc=500)
        rt = simulate("thermometer", N_BITS, 0, sigma_u=s, n_mc=200)
        print(f"  sigma_u={s:5.3f}: binary {rb['dnl_max_mean']:.3f} / {rb['p_nonmono']:.3f} | "
              f"4T+6B {rs['dnl_max_mean']:.3f} / {rs['p_nonmono']:.3f} | "
              f"thermo {rt['dnl_max_mean']:.3f} / {rt['p_nonmono']:.3f}")


if __name__ == "__main__":
    main()
