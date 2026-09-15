#!/usr/bin/env python3
"""Shared 68000-safe LibreKick Exec runtime primitives.

These helpers emit small machine-independent code slices that retained ROM and
WCS profiles can consume without importing a milestone-specific ROM builder.
"""
from __future__ import annotations

import struct

SYSBASE_ADDR = 4


def get_sysbase_code() -> bytes:
    """Return the ExecBase pointer stored at absolute address 4 in D0.

    68000 encoding: MOVE.L $00000004,D0 ; RTS
    """
    return bytes.fromhex("2039000000044e75")


def jsr_absolute(addr: int) -> bytes:
    """Emit JSR absolute-long for a 68000 target address."""
    if not 0 <= addr <= 0xFFFFFFFF:
        raise ValueError("absolute address outside 32-bit range")
    return bytes.fromhex("4eb9") + struct.pack(">I", addr)
