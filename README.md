# LibreKick

LibreKick is a free and open-source Kickstart-compatible ROM project for 68k Amiga systems and emulators.

The first compatibility target is the public API/ABI surface expected by software written for Kickstart/AmigaOS 3.1 (V40). LibreKick is not AmigaOS and does not contain Commodore/Amiga copyrighted ROM code.

## M0 goals

- Define the compatibility target and non-goals.
- Establish a clean-room development policy.
- Provide an initial 68k ROM build skeleton.
- Keep 68000 compatibility as the baseline unless a target profile explicitly says otherwise.
- Prepare automated static checks and later FS-UAE + AROS-based runtime qualification.
- Support both real hardware and emulators as long-term targets.

## Initial target systems

- Amiga 500 / 500+
- Amiga 600
- Amiga 1200
- Amiga 3000 / 4000
- FS-UAE and compatible emulators

The initial ROM size target is 512 KiB. Larger optional ROM profiles may be added later.

## Build

The M0 build is intentionally minimal. It verifies the repository/toolchain layout and produces a deterministic ROM image placeholder suitable for evolving into the first bootable LibreKick image.

```sh
make
make check
```

A cross-toolchain using `m68k-amigaos-gcc` is expected for native 68k code as implementation starts landing.

## Compatibility strategy

LibreKick targets observable documented interfaces: library/device names, versioning, calling conventions, structures where legally/documentarily available, error behavior, and runtime semantics. Compatibility tests should be written from public documentation and independently observed behavior, not copied ROM implementation details.

See:

- `docs/COMPATIBILITY.md`
- `docs/CLEAN_ROOM.md`
- `docs/ARCHITECTURE.md`
- `ROADMAP.md`

## License

MIT. Copyright (c) 2026 Ploos AS.
