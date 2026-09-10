#!/usr/bin/env python3
"""Create the deterministic M0 ROM-shaped image.

This is deliberately not bootable firmware. M1 replaces the marker payload
with real 68k reset/bootstrap code.
"""
from pathlib import Path
import sys

ROM_SIZE = 512 * 1024
MARKER = b"LIBREKICK-M0\0"

if len(sys.argv) != 2:
    raise SystemExit("usage: make_m0_rom.py OUTPUT")

image = bytearray([0xFF]) * ROM_SIZE
image[:len(MARKER)] = MARKER
Path(sys.argv[1]).write_bytes(image)
