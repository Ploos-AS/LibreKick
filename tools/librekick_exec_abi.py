#!/usr/bin/env python3
"""Shared LibreKick Exec ABI constants used by retained machine runtimes.

Keep machine-specific bootstrap/layout code separate, but source public Exec
base/library layout constants from this module so A1000 WCS and ordinary ROM
profiles converge on one compatibility contract.
"""

EXEC_BASE = 0x00003400
LIB_VERSION_OFF = 20
LIB_REVISION_OFF = 22
LIB_IDSTRING_OFF = 24
EXEC_VERSION = 40
