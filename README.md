# Motion detection using two HackRF Ones (CW Doppler radar)

I made a motion detector using two HackRF One SDRs and GNU Radio. One HackRF
transmits a continuous tone in the 2.4 GHz ISM band and the other receives it.
When something moves near the antennas (like waving a hand), the received
signal changes and a trigger fires.


## Hardware

- 2 × HackRF One (one transmit, one receive)
- 2 antennas
- Raspberry Pi (or any Linux machine) with GNU Radio 3.10 and gr-osmosdr
- powered USB hub — two HackRFs on normal ports kept disconnecting for me

## How it works

- The TX flowgraph (`capture/tx_tone_2p4ghz.grc`) transmits a tone at a
  100 kHz offset from the 2.4 GHz center frequency. The offset is there
  because the HackRF has a DC spike right at the center frequency, so you
  don't want your signal sitting on top of it.
- The RX flowgraph (`capture/rx_doppler_2p4.grc`) shifts that tone back to
  0 Hz with a frequency-translating FIR filter and throws away everything
  else (2 Msps decimated down to 50 ksps, 10 kHz low-pass).
- Then it takes the magnitude in dB and runs it through two smoothing
  filters — a fast one (~4 ms) and a very slow one (~2 s). The slow one is
  basically "what the empty room looks like". When something moves, the
  fast one reacts and (fast − slow) jumps.
- That difference becomes the **Motion strength** signal (500 samples/sec).
  When it crosses the threshold, the **Trigger** goes to 1. It turns off a
  bit below the threshold (at 0.8×) so it doesn't flicker on and off right
  at the edge.

The RX window shows three plots: the tone FFT ("Tone health"), Motion
strength, and the Trigger.

## How to run

Run TX and RX as two separate programs — putting both HackRFs in one
GNU Radio process causes problems on shutdown.

```bash
# terminal 1 — transmitter
grcc capture/tx_tone_2p4ghz.grc -o . && python tx_tone_2p4ghz.py

# terminal 2 — receiver / detector
grcc capture/rx_doppler_2p4.grc -o . && python rx_doppler.py
```

Or open both files in GNU Radio Companion and run TX first, then RX.

Notes:

- The flowgraphs pick devices as `hackrf=0` (TX) and `hackrf=1` (RX). The
  index depends on the order the boards enumerate, so if TX/RX seem swapped
  check `hackrf_info`.
- If nothing triggers, look at the **Tone health** plot first. No clear spike
  means the receiver isn't seeing the tone at all — fix that before touching
  the threshold. If the spike is there, play with the **RX IF gain** and
  **Trigger threshold** sliders.


## Next steps

- [x] motion detection at 2.4 GHz (this)
- [ ] record complex IQ and make micro-Doppler spectrograms in Python
- [ ] detect a fan's blades from its Doppler pattern
- [ ] FMCW for range measurement
- [ ] passive radar experiments
- [ ] detect a still person from their breathing
