#!/usr/bin/env bash
# Build Berlin Good for the MPC (needs git, Docker running). Run from this folder.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
FW="$HERE/framework"
[ -d "$FW/.git" ] || git clone -b steve-features https://github.com/saustin2010/mpc-vst-plugins.git "$FW"
rm -rf "$FW/berlin-good"
mkdir "$FW/berlin-good"
tar -C "$HERE" --exclude=framework --exclude=build --exclude=build.sh -cf - . | tar -C "$FW/berlin-good" -xf -
cd "$FW"
tools/test_port.sh berlin-good/vst.json      # must end with PASSED
tools/build_port.sh berlin-good/vst.json
echo "Done: $FW/berlin-good/build/"
