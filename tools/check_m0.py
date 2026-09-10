#!/usr/bin/env python3
from pathlib import Path
import sys

ROM_SIZE = 512 * 1024
MARKER = b"LIBREKICK-M0\0"

if len(sys.argv) != 2:
    raise SystemExit("usage: check_m0.py ROM")

p = Path(sys.argv[1])
data = p.read_bytes()
assert len(data) == ROM_SIZE, f"wrong ROM size: {len(data)}"
assert data.startswith(MARKER), "missing LibreKick M0 marker"
assert set(data[len(MARKER):]) <= {0xFF}, "unexpected nondeterministic payload"
print(f"M0 check PASS: {p} ({len(data)} bytes)")
