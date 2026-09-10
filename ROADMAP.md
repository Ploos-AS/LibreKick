# Roadmap

## M0 — Foundation

- Project scope and compatibility contract.
- Clean-room policy.
- Architecture and source layout.
- MIT licensing.
- Deterministic 512 KiB ROM-image build/check skeleton.

## M1 — First bootable ROM

- 68k reset/bootstrap path.
- Valid ROM layout/checksum handling.
- Early serial/debug output.
- FS-UAE qualification on a 68000-class profile.
- AROS ROM/runtime material used only as legally compatible reference/integration input.

## M2 — Core runtime

- Exec-compatible minimum core.
- Memory, tasks, interrupts, libraries and resources needed for controlled test programs.
- A500/A500+/A600 runtime matrix.

## M3 — Devices and expansion

- timer.device, trackdisk.device and input foundations.
- AutoConfig/expansion path.
- Boot-device and filesystem handoff.

## M4 — V40 compatibility surface

- Systematic library/device API and ABI compatibility work.
- Compatibility test suite derived from public documentation and black-box behavior.
- A1200/A3000/A4000 profiles.

## M5 — Workbench-era application compatibility

- Boot a compatible disk environment.
- Run representative AmigaOS 3.1 applications.
- Regression qualification across CPU/system profiles.

## M6 — Hardware qualification and extended ROM profiles

- Real Amiga ROM testing.
- 512 KiB baseline plus optional larger ROM profiles.
- 68020/030/040/060-specific optional optimizations without breaking the 68000 baseline.
