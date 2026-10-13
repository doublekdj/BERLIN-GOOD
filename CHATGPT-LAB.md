# Berlin Mood — ChatGPT Lab

This branch is an isolated development track for experiments led by ChatGPT.

## Baseline
- Started from `main` at the time the lab branch was created.
- The original `main` branch is not modified by work on this branch.
- The existing Claude-updated project files are preserved as they appeared in the selected baseline.

## Rules
1. Keep changes on `chatgpt-lab-clean`; do not merge or cherry-pick into `main` until explicitly reviewed.
2. Preserve original presets and parameter IDs unless a change is justified and documented.
3. Record each code change and its intended audible/UI effect.
4. Do not call a build successful until the MPC cross-build and host test actually pass.
5. Compare the two implementations using the same presets, MIDI wheel movements, notes, and test conditions.

## Planned work
- Audit the current DSP routing for modulation wheel, filter cutoff and pitch modulation.
- Inspect skin assets/layout before changing knob filmstrips or panel graphics.
- Review envelope sustain/release selectively; avoid bulk preset changes.
- Run build and host tests, then prepare an A/B test checklist for MPC Live.

## Status
Lab branch created. No DSP or preset changes have been made on this clean lab branch yet.
