#!/usr/bin/env bash
# Re-measures every patch and rewrites src/dsp/presets_trim.h so all patches play at the same level.
# Needs g++. Run from the project root after changing patches: tools/calibrate.sh
set -euo pipefail
cd "$(dirname "$0")/.."
python3 tools/gen_presets.py
for i in 1 2 3 4; do
  g++ -O1 -std=gnu++14 -Isrc/dsp -x c++ tools/calibrate.cpp -x c src/dsp/moog_engine.c -o /tmp/bm_cal 2>/dev/null || \
  { g++ -O1 -std=gnu++14 -Isrc/dsp -c -x c++ tools/calibrate.cpp -o /tmp/bm_cal1.o && gcc -O1 -Isrc/dsp -c src/dsp/moog_engine.c -o /tmp/bm_cal2.o && g++ /tmp/bm_cal1.o /tmp/bm_cal2.o -o /tmp/bm_cal; }
  /tmp/bm_cal 0.17 > /tmp/bm_trim.h
  cp /tmp/bm_trim.h src/dsp/presets_trim.h
done
echo "calibrated"
