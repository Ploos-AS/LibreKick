#!/usr/bin/env python3
"""Shared 68000-safe LibreKick Exec runtime primitives.

These helpers emit small machine-independent code slices that retained ROM and
WCS profiles can consume without importing a milestone-specific ROM builder.
"""
from __future__ import annotations

import struct

SYSBASE_ADDR = 4
THIS_TASK_OFF = 0x114
TC_SPREG_OFF = 0x36


def get_sysbase_code() -> bytes:
    """Return the ExecBase pointer stored at absolute address 4 in D0."""
    return bytes.fromhex("2039000000044e75")


def get_current_task_code() -> bytes:
    """Return ExecBase->ThisTask in D0 without requiring A6."""
    return bytes.fromhex("207900000004202801144e75")


def set_current_task_code() -> bytes:
    """Store D0 in ExecBase->ThisTask without requiring A6."""
    return bytes.fromhex("207900000004214001144e75")


def swap_current_task_code() -> bytes:
    """Replace ExecBase->ThisTask with D0 and return the previous pointer in D0."""
    return bytes.fromhex("207900000004222801142140011420014e75")


def handoff_task_stack_code() -> bytes:
    """Privately hand off execution to D0's prepared task stack.

    Saves the post-JSR A7 in old ThisTask->tc_SPReg, installs D0 as ThisTask,
    loads A7 from new ThisTask->tc_SPReg, returns the old task pointer in D0,
    then RTS transfers through the return PC prepared on the new stack.
    D1/A0/A1 are scratch. This is not a public Exec Switch/Dispatch vector and
    does not save or restore the complete CPU register/SR context.
    """
    # MOVEA.L $00000004,A0 ; MOVEA.L $0114(A0),A1 ; MOVE.L A7,$0036(A1)
    # MOVE.L A1,D1 ; MOVEA.L D0,A1 ; MOVE.L D0,$0114(A0)
    # MOVEA.L $0036(A1),A7 ; MOVE.L D1,D0 ; RTS
    return bytes.fromhex("20790000000422680114234f003622092240214001142e69003620014e75")


def jsr_absolute(addr: int) -> bytes:
    """Emit JSR absolute-long for a 68000 target address."""
    if not 0 <= addr <= 0xFFFFFFFF:
        raise ValueError("absolute address outside 32-bit range")
    return bytes.fromhex("4eb9") + struct.pack(">I", addr)
