# Berlin Mood

Minimoog-style mono synth + effects, arpeggiator and 274 programs for the **Akai MPC (Gen 1, HAKAI / MPC OS standalone)**, built to get
Tangerine Dream / Berlin School sounds from the MPC itself.

- **Voice**: RaffoSynth (4 oscillators, Moog ladder filter, contour envelopes, LFO, glide) — mono, low CPU.
- **Phaser** (Berlin School): 6 allpass stages, slow sweep (0.03–3 Hz), stereo quadrature LFO, feedback.
  Controls: RATE, DEPTH, FEEDBACK, MIX.
- **Dotted stereo delay**: ping-pong, locked to the MPC tempo (HOST) or to a manual BPM.
  DIVISION: 1/8 dotted, 1/4 dotted, 1/16 dotted, 1/4, 1/8. Controls: FEEDBACK, TONE, MIX, BPM, SYNC.
- **Shimmer reverb**: 4-line FDN hall with a +1 octave pitch-shifted feedback.
  Controls: DECAY (1.2–19 s), SHIMMER, DAMP, MIX.
- **Drive**: saturator / overdrive / distortion, with TONE and MIX. **Compressor** (threshold, ratio, attack, release,
  make-up) and a lookahead **limiter** (ceiling, release) on the output.
- **Reverb types**: PLATE, ROOM, HALL (the shimmer works on all three). Every effect has its own ON/OFF button.
- **Arpeggiator**: 16 patterns (CHORD = your notes, plus 15 fixed Berlin-style sequences), direction UP / DOWN / UP-DOWN /
  RANDOM, rate 1/4 .. 1/32, gate, 1-3 octaves, HOLD. Tempo from the MPC (or the manual BPM of the delay).
- **4 macros** on the MAIN page (one Q-Link column): OPEN (filter cutoff), SPACE (reverb), ECHO (delay), PHASE (phaser).
  They add to the patch values, so they never overwrite a patch.
- Pages: MAIN, OSCILLATORS, MODULATION, **FX MOD** (phaser, delay, reverb), **FX DYN** (drive, compressor, limiter), **ARP**.
  80 parameters, all on Q-Links and automatable.
- **274 programs**: the 14 RaffoSynth ones (effects off), 4 hand-made Berlin patches and a bank of 256 Berlin School
  patches (16 families x 16 variations, see PRESETS.txt). Some play their own sequence through the arpeggiator.
- Signal chain: synth -> drive -> phaser -> delay -> reverb -> compressor -> limiter -> soft clip.

## Build (needs Docker, e.g. Docker Desktop on the iMac)

    ./build.sh

It clones the MPC plugin framework, copies this folder in, runs the offline test (`tools/test_port.sh`) and builds the
ARM `.so` + skin with `tools/build_port.sh` (glibc 2.31 toolchain, runs on the MPC).
Output: `framework/berlin-good/build/` (`berlingood.so`, `skin/KK - VST - Berlin Mood/`, `pluginlist-entry.xml`).
Then install like your other plugins (the framework's `release.py` / install.sh, or copy the folder to
`/sdcard/Synths/KK - VST - Berlin Mood/` and register `pluginlist-entry.xml`).

## Credits and licence

MIT. Synth engine: RaffoSynth by Nicolas Roulet and Julian Palladino (https://github.com/nicoroulet/RaffoSynth),
Move Anything port by charlesvestal, MPC port and skin by saustin2010 (https://github.com/saustin2010/mpc-vst-moog).
Berlin Mood additions (effects `src/dsp/fx.h`, arpeggiator `src/dsp/arp.h`, pages, macros, patch bank): 2026, Angelo Raggi (KK).

The original copyright notices must stay in LICENSE and in the source files (MIT condition). "Minimoog" is a trademark
of its owner; Berlin Mood is not affiliated with or endorsed by it and only describes its sound as Minimoog-style.
