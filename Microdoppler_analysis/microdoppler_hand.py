#!/usr/bin/env python3
"""Signed micro-Doppler spectrogram for a WAVING HAND (two-HackRF 2.4 GHz rig).

A hand's Doppler is small (~15-60 Hz) and sits right on top of the direct-path
carrier, so the fan script (scaled to +/-300 Hz, tuned for fast blade tips)
squashes it into a thin line at zero. This script is tuned for a hand:

  1. estimate the direct-path carrier (the steady tone from the two boards'
     slightly-offset oscillators) and de-rotate it to 0 Hz;
  2. high-pass to remove that carrier / DC while KEEPING the hand motion;
  3. signed STFT (complex FFT) -> two-sided Doppler:
        +f = hand approaching, -f = hand receding;
  4. display zoomed to +/-fmax (default 80 Hz) in dB, with a thin zero notch,
     so the alternating approach/recede swings of a wave fill the frame.

Usage:
    python3 microdoppler_hand.py microdoppler_fan_2p4ghz.cf32
    python3 microdoppler_hand.py capture.cf32 --fs 1000 --fmax 80 --window 0.4
    python3 microdoppler_hand.py --demo
"""
import argparse
import os
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def moving_average(x, L):
    if L < 2:
        return np.zeros_like(x)
    k = np.ones(L, dtype=np.float64) / L
    # complex-safe running mean via convolution, same length
    re = np.convolve(x.real, k, mode="same")
    im = np.convolve(x.imag, k, mode="same")
    return (re + 1j * im).astype(np.complex64)


def estimate_carrier(z, fs, search_hz=120.0):
    """Strongest steady tone within +/-search_hz = direct-path carrier + LO offset."""
    N = len(z)
    F = np.fft.fftshift(np.fft.fft(z - z.mean()))
    f = np.fft.fftshift(np.fft.fftfreq(N, 1.0 / fs))
    band = np.abs(f) <= search_hz
    idx = np.where(band)[0]
    pk = idx[np.argmax(np.abs(F[idx]))]
    return float(f[pk])


def signed_spectrogram(z, fs, window_s, overlap, zeropad):
    nperseg = max(64, int(round(window_s * fs)))
    noverlap = int(nperseg * overlap)
    step = max(1, nperseg - noverlap)
    nfft = nperseg * zeropad
    win = np.hanning(nperseg).astype(np.float64)
    starts = range(0, len(z) - nperseg + 1, step)
    cols = []
    for s in starts:
        seg = z[s:s + nperseg] * win
        F = np.fft.fftshift(np.fft.fft(seg, nfft))
        cols.append(np.abs(F))
    S = np.array(cols).T                       # [freq, time]
    freqs = np.fft.fftshift(np.fft.fftfreq(nfft, 1.0 / fs))
    times = (np.arange(len(cols)) * step + nperseg / 2) / fs
    return S, freqs, times, nperseg


def process(z, fs, fmax, window_s, overlap, zeropad, hpf, notch_hz, clip_db,
            title, out):
    # 1. de-rotate the direct-path carrier to DC
    fc = estimate_carrier(z, fs)
    n = np.arange(len(z))
    z = z * np.exp(-1j * 2 * np.pi * fc * n / fs).astype(np.complex64)

    # 2. high-pass: remove DC / residual carrier, keep the hand
    L = max(2, int(round(fs / max(hpf, 1e-3))))
    z = z - moving_average(z, L)

    # 3. signed STFT
    S, freqs, times, nperseg = signed_spectrogram(z, fs, window_s, overlap, zeropad)

    # 4. display: zero-Doppler notch scaled to the main-lobe width, dB, zoom
    mainlobe = 2.6 * fs / nperseg
    notch = max(notch_hz, mainlobe)
    S[np.abs(freqs) < notch, :] = 0.0
    fmask = np.abs(freqs) <= fmax
    Sd = S[fmask, :]
    fd = freqs[fmask]

    ref = np.percentile(Sd[Sd > 0], 99.5) if np.any(Sd > 0) else 1.0
    SdB = 20 * np.log10(Sd / ref + 1e-9)
    vmax = 0.0
    vmin = -abs(clip_db)

    # simple detection: strongest |Doppler| per column, and its swing
    col_peak_f = fd[np.argmax(Sd, axis=0)]
    active = Sd.max(axis=0) > 0.35 * ref            # columns with real motion
    swing = (col_peak_f[active].max() - col_peak_f[active].min()) if active.any() else 0.0
    fpk = np.abs(col_peak_f[active]).max() if active.any() else 0.0

    plt.figure(figsize=(11, 5))
    plt.imshow(SdB, origin="lower", aspect="auto",
               extent=[float(times[0]), float(times[-1]), float(fd[0]), float(fd[-1])],
               cmap="jet", vmin=vmin, vmax=vmax, interpolation="bilinear")
    plt.axhline(0, color="w", lw=0.5, alpha=0.3)
    plt.xlabel("Time (s)")
    plt.ylabel("Doppler (Hz)   [+ approaching / - receding]")
    plt.title("%s\npeak |Doppler| %.0f Hz, swing %.0f Hz  (carrier removed at %.1f Hz)"
              % (title, fpk, swing, fc))
    plt.colorbar(label="dB (rel. peak)")
    plt.tight_layout()
    plt.savefig(out, dpi=150)
    plt.close()
    print("  carrier removed at : %.1f Hz" % fc)
    print("  peak |Doppler|     : %.1f Hz  =  %.2f m/s" % (fpk, fpk * 3e8 / (2 * 2.427e9)))
    print("  approach/recede swing: %.0f Hz" % swing)
    print("  wrote", out)
    return fpk


def synth_hand(fs, seconds, seed=1):
    """Weak hand wave (Doppler swinging +/-~45 Hz at ~1.5 Hz) + strong steady
    direct-path carrier at a ~15 Hz LO offset + noise."""
    rng = np.random.default_rng(seed)
    N = int(fs * seconds)
    t = np.arange(N) / fs
    # hand: velocity oscillates -> Doppler swings; phase = integral of 2*pi*fd
    fd_max = 45.0
    f_wave = 1.5
    fd = fd_max * np.sin(2 * np.pi * f_wave * t)
    # only "wave" during 8..23 s, still otherwise
    envelope = ((t > 8) & (t < 23)).astype(float)
    phase = 2 * np.pi * np.cumsum(fd * envelope) / fs
    hand = 2.5e-5 * envelope * np.exp(1j * phase)
    carrier = 1.0e-3 * np.exp(1j * 2 * np.pi * 15.0 * t)      # strong steady direct path
    noise = (rng.standard_normal(N) + 1j * rng.standard_normal(N)) * (3e-5 / np.sqrt(2))
    return (carrier + hand + noise).astype(np.complex64)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file", nargs="?", default=None, help="complex64 .cf32 capture")
    p.add_argument("--fs", type=float, default=1000.0, help="capture sample rate (Hz)")
    p.add_argument("--fmax", type=float, default=80.0, help="Doppler display zoom (Hz)")
    p.add_argument("--window", type=float, default=0.4, help="STFT window (s)")
    p.add_argument("--overlap", type=float, default=0.9, help="STFT overlap fraction")
    p.add_argument("--zeropad", type=int, default=2, help="FFT zero-pad factor")
    p.add_argument("--hpf", type=float, default=7.0, help="high-pass corner (Hz), removes carrier/DC")
    p.add_argument("--notch", type=float, default=3.0, help="zero-Doppler display notch (Hz)")
    p.add_argument("--clip-db", type=float, default=25.0, help="dB display range below peak")
    p.add_argument("--demo", action="store_true")
    p.add_argument("--out", default=None)
    a = p.parse_args()

    if a.demo:
        z = synth_hand(a.fs, 28.0)
        title = "Signed micro-Doppler (hand) - SYNTHETIC DEMO"
        out = a.out or "microdoppler_hand_demo.png"
    elif a.file:
        z = np.fromfile(a.file, dtype=np.complex64)
        title = "Signed micro-Doppler spectrogram (hand)"
        stem = os.path.splitext(os.path.basename(a.file))[0]
        out = a.out or (stem + "_hand.png")
    else:
        print("give a .cf32 file  or  --demo")
        sys.exit(1)

    process(z, a.fs, a.fmax, a.window, a.overlap, a.zeropad, a.hpf, a.notch,
            a.clip_db, title, out)


if __name__ == "__main__":
    main()
