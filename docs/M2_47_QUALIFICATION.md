# M2.47 emulator qualification

Status: **PASS — emulator-qualified**

M2.47 converges the private CPU context-frame work into the retained 512 KiB LibreKick ROM line. The context frame preserves and restores SR, D2-D7, and A2-A6 while handing execution through the current task stack. This milestone remains deliberately narrower than a public Exec scheduler: it does not claim public `Switch`, `Dispatch`, `Schedule`, `Reschedule`, or general scheduler-driven task switching.

## Qualified source

- Commit: `230f3c13a2e3e28279e088323093414929eccbc3`
- Generator: `tools/make_m2_47_rom.py`
- Checker: `tools/check_m2_47.py`
- ROM size: 524288 bytes
- ROM checksum: `0xffffffff`
- Context handoff: `$00f86b00`
- Context resume: `$00f86c00`
- Probe: `$00f86d00`

## Static qualification

GitHub Actions `M1 static qualification` passed on the qualified source:

- Run: `35201279338`
- Run number: `#492`
- Job: `105136356010` (`m1-static`)
- Result: **PASS**

The static checker built the M2.47 ROM and verified the retained ROM structure, private context-frame code and checksum.

## FS-UAE runtime qualification

GitHub Actions `FS-UAE runtime qualification` passed on the same source:

- Run: `35201279408`
- Run number: `#366`
- Job: `105136356345` (`fs-uae-runtime`)
- Runner: Ubuntu 24.04.5 LTS
- FS-UAE: 3.1.66
- Rendering: Mesa llvmpipe software OpenGL
- Result: **PASS**

Runtime evidence:

- Diagnostic image: 960x540
- Green ratio: `0.8848`
- Red ratio: `0.0000`
- Blue ratio: `0.0000`
- Dominant RGB: `0,240,0`
- Dominant ratio: `0.8832`
- Runtime gate: `PASS: green diagnostic screen`

The runtime build also reported:

- `M2.47 check PASS`
- `context=SR,D2-D7,A2-A6`
- `checksum=0xffffffff`
- `scope=private CPU context frame; public Exec scheduler not claimed`

## Retained evidence artifact

- Artifact: `fs-uae-runtime-qualification`
- Artifact ID: `10488461823`
- Size: 14938 bytes
- SHA-256: `50efcf3f5c81fac3a624c8f55de1c58be55dff17321e29c7fba975bfbb748428`
- Retention expiry reported by GitHub: 2026-12-16

The artifact contains the runtime result, diagnostic screenshot, FS-UAE log/version, ROM metadata, configuration and OpenGL evidence.

## Retained model profiles

The A500, A500 Plus and A600 retained profiles are marked `emulator-qualified` at milestone `m2_47`. Each profile keeps an explicit model-specific artifact path and FS-UAE configuration rather than collapsing the project into one generic ROM identity.

## Qualification boundary

This qualification demonstrates deterministic ROM generation, static validation and successful FS-UAE execution of the M2.47 private CPU context-frame probe. It is emulator qualification, not a claim of complete Amiga Exec compatibility or physical-hardware qualification.
