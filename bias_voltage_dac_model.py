"""
Behavioral Model of a Bias Voltage DAC
==========================================
Course: AMS Fall 2026
Purpose: Allow students to simulate an N-bit voltage-output DAC, observe
         its ideal transfer characteristic, and see the effect of common
         non-idealities: offset error, gain error, and per-code INL/DNL
         (integral/differential nonlinearity).

Instructions for students:
    1. Modify the parameters in the "USER-ADJUSTABLE PARAMETERS" section.
    2. Run the script (python bias_voltage_dac_model.py).
    3. Observe how the ideal staircase transfer curve is distorted by each
       non-ideality, and how INL/DNL are computed and plotted.

Requirements: numpy, matplotlib
"""

import numpy as np
import matplotlib.pyplot as plt

# ----------------------------------------------------------------------
# USER-ADJUSTABLE PARAMETERS
# ----------------------------------------------------------------------
N_BITS           = 4         # DAC resolution [bits] (e.g., 4-bit -> 16 codes)
VREF             = 1.6       # Reference voltage [V]

OFFSET_ERROR_V   = 0.01     # Constant output offset error [V]
GAIN_ERROR_PCT   = 2.0       # Gain error, as a percentage of full scale [%]

INL_STD_LSB      = 0.15    # Standard deviation of random INL, in units
                              # of LSB (integral nonlinearity: deviation of
                              # each code's output from the ideal line)
RANDOM_SEED      = 42        # Seed for reproducible random non-idealities

np.random.seed(RANDOM_SEED)

# ----------------------------------------------------------------------
# IDEAL DAC TRANSFER FUNCTION
# ----------------------------------------------------------------------
def ideal_dac_output(codes, n_bits=N_BITS, vref=VREF):
    """
    Computes the ideal DAC output voltage for each input digital code:
        Vout = Code * Vref / 2^N
    """
    full_scale_codes = 2 ** n_bits
    lsb = vref / full_scale_codes
    return codes * lsb, lsb


# ----------------------------------------------------------------------
# NON-IDEAL DAC TRANSFER FUNCTION (offset, gain error, INL)
# ----------------------------------------------------------------------
def non_ideal_dac_output(codes, n_bits=N_BITS, vref=VREF,
                          offset=OFFSET_ERROR_V, gain_error_pct=GAIN_ERROR_PCT,
                          inl_std_lsb=INL_STD_LSB):
    """
    Computes the DAC output including:
        - A constant offset error added to every code
        - A gain error that scales the ideal slope
        - Random per-code INL deviations (drawn once and held fixed,
          representing a specific physical DAC's static nonlinearity)
    """
    ideal_output, lsb = ideal_dac_output(codes, n_bits, vref)

    gain_factor = 1 + gain_error_pct / 100.0
    inl_deviation = np.random.normal(0, inl_std_lsb * lsb, size=codes.shape)

    non_ideal_output = offset + gain_factor * ideal_output + inl_deviation
    return non_ideal_output, lsb


# ----------------------------------------------------------------------
# INL / DNL CALCULATION
# ----------------------------------------------------------------------
def compute_inl_dnl(actual_output, lsb):
    """
    Computes INL and DNL (in units of LSB) from a DAC's actual output
    codes, referenced to a best-fit ideal line through the first and last
    codes.
    """
    n_codes = len(actual_output)
    ideal_line = np.linspace(actual_output[0], actual_output[-1], n_codes)

    inl = (actual_output - ideal_line) / lsb
    dnl = np.diff(actual_output) / lsb - 1  # ideal step is exactly 1 LSB

    return inl, dnl


# ----------------------------------------------------------------------
# PLOTTING
# ----------------------------------------------------------------------
def plot_dac_characteristics():
    codes = np.arange(2 ** N_BITS)

    ideal_output, lsb = ideal_dac_output(codes)
    non_ideal_output, _ = non_ideal_dac_output(codes)
    inl, dnl = compute_inl_dnl(non_ideal_output, lsb)

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Transfer curve
    axes[0].step(codes, ideal_output, where='mid', label="Ideal")
    axes[0].step(codes, non_ideal_output, where='mid', label="Non-ideal")
    axes[0].set_xlabel("Digital input code")
    axes[0].set_ylabel("Output voltage [V]")
    axes[0].set_title(f"{N_BITS}-bit DAC Transfer Characteristic")
    axes[0].legend()
    axes[0].grid(True)

    # INL
    axes[1].plot(codes, inl, marker='o', markersize=3)
    axes[1].axhline(0, color='gray', linestyle=':')
    axes[1].set_xlabel("Digital input code")
    axes[1].set_ylabel("INL [LSB]")
    axes[1].set_title("Integral Nonlinearity (INL)")
    axes[1].grid(True)

    # DNL
    axes[2].plot(codes[1:], dnl, marker='o', markersize=3, color='tab:orange')
    axes[2].axhline(0, color='gray', linestyle=':')
    axes[2].set_xlabel("Digital input code")
    axes[2].set_ylabel("DNL [LSB]")
    axes[2].set_title("Differential Nonlinearity (DNL)")
    axes[2].grid(True)

    plt.tight_layout()


if __name__ == "__main__":
    plot_dac_characteristics()
    plt.show()
