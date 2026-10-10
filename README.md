# Berlin Good

Minimoog-style mono synth + three effects for the **Akai MPC (Gen 1, HAKAI / MPC OS standalone)**, built to get
Tangerine Dream / Berlin School sounds from the MPC itself.

- **Voice**: RaffoSynth (4 oscillators, Moog ladder filter, contour envelopes, LFO, glide) — mono, low CPU.
- **Phaser** (Berlin School): 6 allpass stages, slow sweep (0.03–3 Hz), stereo quadrature LFO, feedback.
  Controls: RATE, DEPTH, FEEDBACK, MIX.
- **Dotted stereo delay**: ping-pong, locked to the MPC tempo (HOST) or to a manual BPM.
  DIVISION: 1/8 dotted, 1/4 dotted, 1/16 dotted, 1/4, 1/8. Controls: FEEDBACK, TONE, MIX, BPM, SYNC.
- **Shimmer reverb**: 4-line FDN hall with a +1 octave pitch-shifted feedback.
  Controls: DECAY (1.2–19 s), SHIMMER, DAMP, MIX.
- Pages: MAIN, OSCILLATORS, MODULATION, **FX** (new). 55 parameters, all on Q-Links and automatable.
- 18 patches: the 14 RaffoSynth ones (FX off) + 4 Berlin patches: *Phaedra Seq, Rubycon Pad, Stratosfear Lead, Tangram Bass*.
- Effects chain order: synth → phaser → delay → shimmer reverb → soft clip.

## Build (needs Docker, e.g. Docker Desktop on the iMac)

    ./build.sh

It clones the MPC plugin framework, copies this folder in, runs the offline test (`tools/test_port.sh`) and builds the
ARM `.so` + skin with `tools/build_port.sh` (glibc 2.31 toolchain, runs on the MPC).
Output: `framework/berlin-good/build/` (`berlingood.so`, `skin/KK - VST - [SYN] Berlin Good/`, `pluginlist-entry.xml`).
Then install like your other plugins (the framework's `release.py` / install.sh, or copy the folder to
`/sdcard/Synths/KK - VST - [SYN] Berlin Good/` and register `pluginlist-entry.xml`).

## Credits and licence

MIT. Synth engine: RaffoSynth by Nicolas Roulet and Julian Palladino (https://github.com/nicoroulet/RaffoSynth),
Move Anything port by charlesvestal, MPC port and skin by saustin2010 (https://github.com/saustin2010/mpc-vst-moog).
Berlin Good additions (effects `src/dsp/fx.h`, FX page, Berlin patches): 2026, KK (Angelo Raggi).
