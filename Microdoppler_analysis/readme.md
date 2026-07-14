
# Micro-Doppler Analysis using HackRF One

This project demonstrates how a simple Continuous Wave (CW) radar can be built using two HackRF One Software Defined Radios (SDRs) to visualize human motion through micro-Doppler signatures.

Unlike an FMCW radar, this project focuses on measuring the velocity of moving objects rather than their distance. Motion is observed by measuring the Doppler frequency shift produced by reflections from moving targets.

---

## Project Overview

The setup consists of two HackRF One SDRs.

- One HackRF continuously transmits a single 2.4 GHz CW signal.
- The second HackRF receives reflections from the moving target.
- Both SDRs share a 10 MHz reference clock for frequency synchronization.
- GNU Radio is used for transmission and reception.
- Python processes the recorded IQ samples to generate signed micro-Doppler spectrograms.

---

## System Workflow

```
HackRF TX (2.4 GHz CW Tone)
            │
            ▼
     Moving Target
            │
            ▼
HackRF RX (IQ Samples)
            │
            ▼
GNU Radio Receiver
            │
            ▼
Save IQ (.cf32)
            │
            ▼
Python Processing
      │
      ├── Carrier Drift Removal
      ├── MTI / Clutter Suppression
      ├── Short-Time Fourier Transform
      └── Signed Micro-Doppler Spectrogram
```

---

## Signal Processing

The recorded IQ samples are processed offline in Python.

The processing pipeline consists of:

1. Loading the recorded complex IQ samples.
2. Removing carrier frequency drift caused by oscillator offsets.
3. Suppressing stationary clutter around zero Doppler.
4. Computing a Short-Time Fourier Transform (STFT).
5. Separating approaching and receding motion using Doppler sign.
6. Generating a signed micro-Doppler spectrogram.

---

## Repository Contents

```
Microdoppler_analysis/

├── tx_tone_2p4ghz.grc
│   GNU Radio transmitter

├── rx_microdoppler_2p4.grc
│   GNU Radio receiver

├── microdoppler_hand.py
│   Python script used to generate signed micro-Doppler spectrograms

├── pics/
│   Spectrogram images

└── results.md
    Explanation of generated results
```

---

## Tools Used

- HackRF One (2x)
- GNU Radio 3.10
- Python
- NumPy
- SciPy
- Matplotlib
- Raspberry Pi

---

## Future Work

Some possible improvements include:

- Phase-coherent receiver using USRP B210
- Angle of Arrival (AoA)
- Beamforming
- FMCW ranging
- Range-Doppler processing
- Gesture classification using machine learning
