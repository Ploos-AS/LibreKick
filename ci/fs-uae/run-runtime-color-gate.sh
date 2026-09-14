#!/usr/bin/env bash
set -euo pipefail

OUT=${LIBREKICK_RUNTIME_OUT:-build/fs-uae/runtime}
WAIT_SECONDS=${LIBREKICK_RUNTIME_WAIT_SECONDS:-2}

if [[ -n "${LIBREKICK_RUNTIME_ROM:-}" ]]; then
  rom="$LIBREKICK_RUNTIME_ROM"
else
  rom=$(awk '$1 == "ROM" && $2 == ":=" {print $3; exit}' Makefile)
fi
if [[ -z "${rom:-}" ]]; then
  echo "Could not determine current ROM" >&2
  exit 2
fi

if [[ -n "${LIBREKICK_RUNTIME_CONFIG:-}" ]]; then
  config="$LIBREKICK_RUNTIME_CONFIG"
else
  stem=$(basename "$rom" .rom)
  milestone=${stem#librekick-}
  config="configs/fs-uae/a500-${milestone}.fs-uae"
fi

if [[ ! -f "$config" ]]; then
  echo "Missing FS-UAE config: $config" >&2
  exit 2
fi

if [[ -n "${LIBREKICK_RUNTIME_BUILD_CMD:-}" ]]; then
  bash -lc "$LIBREKICK_RUNTIME_BUILD_CMD"
else
  make clean check
fi
mkdir -p "$OUT"
printf '%s\n' "$rom" > "$OUT/rom.txt"
printf '%s\n' "$config" > "$OUT/config.txt"
printf '%s\n' "$WAIT_SECONDS" > "$OUT/wait-seconds.txt"
fs-uae --version > "$OUT/fs-uae-version.txt" 2>&1 || true

pid=""
cleanup() {
  [[ -n "${pid:-}" ]] || return 0
  if kill -0 "$pid" 2>/dev/null; then
    kill -TERM "$pid" 2>/dev/null || true
    for _ in $(seq 1 20); do
      kill -0 "$pid" 2>/dev/null || break
      sleep 0.1
    done
  fi
  if kill -0 "$pid" 2>/dev/null; then kill -KILL "$pid" 2>/dev/null || true; fi
  wait "$pid" 2>/dev/null || true
}
trap cleanup EXIT INT TERM

# GitHub-hosted runners do not provide an ALSA/OpenAL playback device.  Audio is
# irrelevant to the color-based runtime gate, so disable it explicitly.  This
# avoids FS-UAE stalling during audio backend initialization before SDL creates
# the emulator window.
fs-uae "$config" --uae-sound-output=none > "$OUT/fs-uae.log" 2>&1 &
pid=$!

wid=""
for _ in $(seq 1 100); do
  wid=$(xdotool search --name 'FS-UAE' 2>/dev/null | head -n1 || true)
  if [[ -z "$wid" ]]; then wid=$(xdotool search --pid "$pid" 2>/dev/null | head -n1 || true); fi
  [[ -n "$wid" ]] && break
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "FS-UAE exited before creating a window" >&2
    cat "$OUT/fs-uae.log" >&2 || true
    exit 1
  fi
  sleep 0.1
done

if [[ -z "$wid" ]]; then
  echo "Timed out waiting for FS-UAE window" >&2
  cat "$OUT/fs-uae.log" >&2 || true
  printf 'result=FAIL\nreason=window-timeout\n' > "$OUT/result.txt"
  exit 1
fi

sleep "$WAIT_SECONDS"
import -window "$wid" "$OUT/diagnostic.png"

python3 - "$OUT/diagnostic.png" "$OUT/result.txt" <<'PY'
from collections import Counter
from pathlib import Path
from PIL import Image
import sys

image_path = Path(sys.argv[1])
result_path = Path(sys.argv[2])
im = Image.open(image_path).convert("RGB")
w, h = im.size
x0, y0 = max(0, w // 10), max(0, h // 10)
x1, y1 = min(w, w - w // 10), min(h, h - h // 10)
pixels = list(im.crop((x0, y0, x1, y1)).getdata())
count = max(1, len(pixels))

green = sum(1 for r, g, b in pixels if g >= 180 and r <= 80 and b <= 80)
blue = sum(1 for r, g, b in pixels if b >= 160 and r <= 100 and g <= 120)
red = sum(1 for r, g, b in pixels if r >= 160 and g <= 120 and b <= 120)

def q(rgb):
    return tuple((v // 16) * 16 for v in rgb)
quant = Counter(q(px) for px in pixels)
dominant_rgb, dominant_count = quant.most_common(1)[0]
dominant_ratio = dominant_count / count

green_ratio = green / count
blue_ratio = blue / count
red_ratio = red / count
summary = (
    f"image={w}x{h}\n"
    f"green_ratio={green_ratio:.4f}\n"
    f"blue_ratio={blue_ratio:.4f}\n"
    f"red_ratio={red_ratio:.4f}\n"
    f"dominant_rgb={dominant_rgb[0]},{dominant_rgb[1]},{dominant_rgb[2]}\n"
    f"dominant_ratio={dominant_ratio:.4f}\n"
)
result_path.write_text(summary)
print(summary, end="")

if green_ratio < 0.55:
    with result_path.open("a") as f: f.write("result=FAIL\n")
    raise SystemExit("FS-UAE runtime gate FAIL: diagnostic screen is not green")

print("FS-UAE runtime gate PASS: green diagnostic screen")
with result_path.open("a") as f: f.write("result=PASS\n")
PY

cleanup
pid=""
trap - EXIT INT TERM
