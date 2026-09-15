#!/usr/bin/env python3
"""Shared 68000-safe LibreKick Exec runtime primitives.

These helpers emit small machine-independent code slices that retained ROM and
WCS profiles can consume without importing a milestone-specific ROM builder.
"""
from __future__ import annotations

import struct

SYSBASE_ADDR = 4
# Current internal ExecBase layout used by the M2 runtime. Keep the offset here
# so WCS and ordinary ROM profiles consume the same task lookup primitive.
THIS_TASK_OFF = 0x114


def get_sysbase_code() -> bytes:
    """Return the ExecBase pointer stored at absolute address 4 in D0.

    68000 encoding: MOVE.L $00000004,D0 ; RTS
    """
    return bytes.fromhex("2039000000044e75")


def get_current_task_code() -> bytes:
    """Return ExecBase->ThisTask in D0 without requiring A6.

    This is a private shared runtime primitive, not yet a public FindTask()
    vector. It deliberately derives ExecBase from address 4 so the same bytes
    work in retained ROM and A1000 WCS profiles.
    """
    # MOVEA.L $00000004,A0 ; MOVE.L $0114(A0),D0 ; RTS
    return bytes.fromhex("207900000004202801144e75")


def set_current_task_code() -> bytes:
    """Store D0 in ExecBase->ThisTask without requiring A6.

    This is a private shared scheduler/runtime primitive. It intentionally
    mirrors get_current_task_code() and is not yet a public Exec vector.
    """
    # MOVEA.L $00000004,A0 ; MOVE.L D0,$0114(A0) ; RTS
    return bytes.fromhex("207900000004214001144e75")


def jsr_absolute(addr: int) -> bytes:
    """Emit JSR absolute-long for a 68000 target address."""
    if not 0 <= addr <= 0xFFFFFFFF:
        raise ValueError("absolute address outside 32-bit range")
    return bytes.fromhex("4eb9") + struct.pack(">I", addr)
