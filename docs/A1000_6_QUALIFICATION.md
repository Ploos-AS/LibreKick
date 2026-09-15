# LibreKick A1000.6 qualification

A1000.6 qualifies the first shared 68000-safe LibreKick Exec runtime primitive inside the retained stock-style A1000 DF0 → WCS boot path.

## Qualified scope

The A1000.3 64 KiB clean-room bootstrap loads the A1000.6 256 KiB WCS payload from the retained LibreKick-private kickdisk and transfers execution to `$00fc0008`.

The A1000.6 WCS runtime installs the shared Exec ABI state, publishes ExecBase at absolute address 4, records version 40.6 and its WCS-resident id string, then calls the shared `GetSysBase` primitive. The primitive executes `MOVE.L $00000004,D0 ; RTS`; the WCS runtime verifies the returned D0 value against `$00003400` before entering the green PASS state.

This is a shared internal runtime primitive. A1000.6 does **not** claim a public `exec.library` negative vector, a complete Exec scheduler, or full Exec compatibility.

## Qualified build

- HEAD: `f5935c663319fba87ab2f2b37de182aca07ea893`
- runtime workflow: `A1000 bootstrap runtime qualification`
- runtime run: `34968853559` (#58)
- runtime job: `104379852123`
- result: **PASS / success**
- runner: Ubuntu 24.04.5 LTS (`ubuntu-24.04`)
- FS-UAE: 3.1.66-2build2

Static qualification also passed in `A1000 kickdisk static qualification`, run `34968853573` (#52), on the same HEAD.

## Static/build evidence

- A1000.3 bootstrap ROM: 65,536 bytes
- A1000.6 WCS payload: 262,144 bytes
- A1000.6 kickdisk: 901,120 bytes
- WCS base: `$00fc0000`
- WCS entry: `$00fc0008`
- ExecBase: `$00003400`
- shared Exec version/revision: 40.6
- shared primitive: `GetSysBase`
- primitive WCS address: `$00fc0200`
- primitive bytes: `2039000000044e75`
- payload SHA-256: `3daa26e87c1a3ede7270b45a7147925f89d59c81ce8313a10894707f9f836fb3`
- container: LibreKick-private bootstrap container v2

The static checker validates the container manifest and payload hash, WCS vectors, runtime bytes, markers/id string, shared ABI constants, and the exact 68000-safe `GetSysBase` machine code.

## Runtime evidence

The complete A1000.3 DF0 loader → A1000.6 WCS runtime path reached the green terminal state after the configured 20-second gate:

```text
image=960x540
green_ratio=0.9010
blue_ratio=0.0000
red_ratio=0.0000
dominant_rgb=0,240,0
dominant_ratio=0.9010
FS-UAE runtime gate PASS: green diagnostic screen
```

This means the WCS runtime executed far enough to install and verify the shared Exec ABI state, call the shared `GetSysBase` primitive, verify its returned ExecBase, and enter the PASS state.

## Retained runtime artifact

- artifact: `librekick-a1000-bootstrap-runtime-qualification`
- artifact ID: `10395899342`
- artifact size: 5,344 bytes
- ZIP SHA-256: `537507b5b5dfd664a9ff868ecebe660e69c878ef137fbee342d29c41d348834c`

The artifact retains the diagnostic screenshot, FS-UAE log/version/configuration, runtime result metadata, A1000.3 bootstrap ROM, A1000.6 WCS payload, and A1000.6 kickdisk.

## Scope boundary

A1000.6 is **emulator-qualified** for the shared internal `GetSysBase` runtime primitive on the stock-style A1000 WCS path. It is not hardware-qualified and does not claim stock Commodore Kickstart-disk compatibility or full `exec.library` compatibility.

## Verdict

**A1000.6 PASS.**

The next convergence step should make an ordinary retained 512 KiB ROM profile consume the same shared Exec runtime primitive. That will prove that `tools/librekick_exec_runtime.py` is genuinely shared across both WCS and ROM machine families before adding further Exec primitives.
