#!/usr/bin/env bash
set -euo pipefail

FSUAE_BIN="${FSUAE_BIN:-fs-uae}"
CONFIG="${1:-configs/fs-uae/a500-m1.fs-uae}"
ROM="build/librekick-m1.rom"
LOGDIR="build/m1-runtime"
LOG="$LOGDIR/fs-uae.log"

if ! command -v "$FSUAE_BIN" >/dev/null 2>&1; then
  echo "M1.1 BLOCKED: fs-uae not found (set FSUAE_BIN or install FS-UAE)" >&2
  exit 2
fi

make clean
make check

# make clean removes build/, so create the runtime artifact directory only
# after the clean/build gate has completed.
mkdir -p "$LOGDIR"

sha256sum "$ROM" | tee "$LOGDIR/rom.sha256"
"$FSUAE_BIN" --version | tee "$LOGDIR/fs-uae-version.txt"

cat <<'EOF'
M1.1 runtime qualification is interactive by design.
Expected evidence after launch:
  - LibreKick ROM is accepted and mapped as a 512 KiB Kickstart image
  - visible COLOR00 debug marker is reached
  - no reset loop / illegal instruction failure
  - CPU remains in the intentional bootstrap idle loop
  - when a debugger is available, chip RAM $00001000 contains 4c4b3031 ('LK01')
Close FS-UAE after observing the runtime evidence.
EOF

set +e
"$FSUAE_BIN" "$CONFIG" 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
set -e

printf '%s\n' "$rc" > "$LOGDIR/fs-uae.exit-code"

if [ "$rc" -ne 0 ]; then
  echo "M1.1 FAIL/BLOCKED: FS-UAE exited with status $rc" >&2
  exit "$rc"
fi

echo "M1.1 emulator run completed. Runtime PASS still requires the observations in docs/M1_QUALIFICATION.md."
