# Experimental Results

The following spectrograms were generated using the CW radar.

Each image is a signed micro-Doppler spectrogram generated from the recorded IQ samples.

---

## Understanding the Spectrogram

- Horizontal axis → Time
- Vertical axis → Doppler Frequency (Hz)
- Positive Doppler → Motion towards the radar
- Negative Doppler → Motion away from the radar
- Colour → Signal strength

The dark blue band around 0 Hz represents stationary clutter and direct transmitter leakage that has been intentionally suppressed during processing.

---

# Fast Hand Motion

![Fast Hand](pics/fasthandzoomedin.png)

The first experiment was performed by waving the hand quickly in front of the radar.

Observations:

- Strong reflections appear once the hand enters the radar beam.
- Positive and negative Doppler components alternate as the hand moves towards and away from the radar.
- Peak Doppler shifts reach approximately ±50–60 Hz.
- The larger Doppler spread indicates higher hand velocity.

---

# Slow Hand Motion

![Slow Hand](pics/slowhandzoomedin.png)

The second experiment was performed using slower hand movements.

Observations:

- Doppler signatures remain much closer to the zero-Doppler line.
- Individual forward and backward hand swings become clearly visible.
- Peak Doppler shifts reduce to approximately ±20–30 Hz.
- The smaller Doppler spread corresponds to lower hand velocity.

---

## Conclusion

The generated spectrograms demonstrate that a simple Continuous Wave radar can distinguish between different motion speeds using Doppler frequency alone.

Although the radar does not measure target range, it successfully captures the velocity and temporal characteristics of moving objects through their micro-Doppler signatures.
