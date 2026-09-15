# LibreKick M2.43 qualification

M2.43 qualifies the retained **A1000 DF0 → WCS bootstrap path** in automated FS-UAE CI.

## Qualified scope

The A1000.3 64 KiB clean-room bootstrap releases the reset OVL mapping before using low Chip RAM, reads the LibreKick-private A1000.2 kickdisk through the DF0 standard-MFM/Paula disk-DMA path, validates its manifest, loads the 256 KiB payload at `$00fc0000`, and hands execution to `$00fc0008` in A1000 WCS.

The automated runtime overlay bypasses `/RDY` and track-zero sensing because those mechanical signals are not authoritative in the emulator gate. The canonical hardware bootstrap retains both checks for later real-A1000 qualification. The disk DMA, MFM decode, manifest validation, payload loading and WCS handoff remain part of the automated path.

## Qualified build

- HEAD: `320f50fe58238cf7c272e66409c002d4cb085a39`
- workflow: `A1000 bootstrap runtime qualification`
- run: `34911362884` (#33)
- job: `104199341850`
- result: **PASS / success**
- runner: Ubuntu 24.04
- FS-UAE: 3.1.66

Static/runtime build evidence:

- A1000.3 bootstrap ROM: 65,536 bytes
- bootstrap reset SP: `$0003fffc`
- bootstrap reset PC: `$00f80008`
- A1000.2 WCS payload: 262,144 bytes
- A1000.2 kickdisk: 901,120 bytes
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- payload SHA-256: `a79d025a4999003c253a8a85c2130039f0e551aa59ecca0dc24a2b50ebd24196`

## Runtime evidence

The complete bootstrap path reached the synthetic WCS payload's green terminal state after 20 seconds:

```text
image=960x540
green_ratio=0.9010
blue_ratio=0.0000
red_ratio=0.0000
dominant_rgb=0,240,0
dominant_ratio=0.9010
FS-UAE runtime gate PASS: green diagnostic screen
```

The previous cyan-stage stall was traced to the A1000 reset ROM overlay remaining enabled while the bootstrap attempted its first low Chip RAM state write. The qualified bootstrap explicitly configures CIA-A port A and clears OVL before accessing low memory.

## Artifact

- artifact: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10374209434`
- artifact size: 5010 bytes
- ZIP SHA-256: `ed831959575a1b0dedb0c176a204c04a3164cb4382894e2d8b746b558a1387c6`

The artifact retains the diagnostic screenshot, FS-UAE log/version/configuration, result metadata, bootstrap ROM, WCS payload and kickdisk image.

## Scope boundary

M2.43 proves the automated emulator bootstrap transport and WCS handoff. It does **not** claim real A1000 hardware qualification, stock Commodore Kickstart-disk compatibility, or a complete useful WCS-resident LibreKick runtime.

## Verdict

**M2.43 PASS.**

The A1000 bootstrap transport is now qualified. The next A1000 slice is to replace the synthetic green-screen WCS payload with the first useful native LibreKick WCS-resident runtime while retaining this qualified DF0 → WCS bootstrap path.
