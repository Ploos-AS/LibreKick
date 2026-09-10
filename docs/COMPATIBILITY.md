# Compatibility Contract

LibreKick's first compatibility baseline is Kickstart/AmigaOS 3.1, commonly identified as V40.

## What compatible means

Compatibility is defined by observable behavior required by existing software, including:

- Exec-style library calling conventions and version checks.
- Required library and device names.
- Publicly documented structures, constants and error codes.
- Expected initialization and shutdown behavior.
- 68k ABI compatibility for supported CPU profiles.
- Boot/runtime behavior needed by Workbench-era software.

Binary compatibility is a goal where it can be achieved from legitimate public specifications and independent testing.

## What compatible does not mean

LibreKick does not aim to reproduce copyrighted ROM bytes, internal implementation details, private source code, trademarks, artwork, or proprietary assets.

A passing compatibility test demonstrates matching externally visible behavior only.

## Baseline CPU

68000 is the baseline CPU target. Features requiring 68020+ must be isolated behind explicit target profiles.

## Initial validation matrix

M0-M1 validation should grow toward:

| Target | CPU | Emulator/hardware | Goal |
|---|---|---|---|
| A500 | 68000 | FS-UAE | cold boot |
| A500+ | 68000 | FS-UAE | cold boot |
| A600 | 68000 | FS-UAE | cold boot |
| A1200 | 68020 | FS-UAE | cold boot |
| A3000 | 68030 | FS-UAE | cold boot |
| A4000 | 68040 | FS-UAE | cold boot |

Real-hardware qualification follows once ROM initialization is sufficiently complete.
