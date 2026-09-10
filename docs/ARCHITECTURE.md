# Architecture

LibreKick is structured as a compatibility-oriented ROM, not as a monolithic reimplementation.

## Layers

1. **ROM entry/bootstrap** — reset vectors, early CPU/chipset setup and deterministic handoff.
2. **Kernel/core** — Exec-compatible primitives required by higher layers.
3. **Libraries** — versioned library interfaces such as graphics/intuition/dos compatibility surfaces.
4. **Devices/resources** — timer, trackdisk, input and other ROM-resident services.
5. **Expansion/boot** — AutoConfig, boot-device discovery and filesystem handoff.
6. **Compatibility tests** — black-box tests for V40-visible behavior.

## Source layout

- `src/boot/` reset/bootstrap code
- `src/core/` kernel/core implementation
- `src/libraries/` library implementations
- `src/devices/` devices/resources
- `src/expansion/` expansion and boot support
- `tests/` host-side and later runtime compatibility tests
- `tools/` build/check utilities

## Implementation strategy

M0 establishes the contract and build shape. M1 should produce the first genuinely bootable ROM and validate it in FS-UAE. Open-source AROS/m68k components may be reused only after their licensing and integration boundaries are documented.

The baseline remains 68000-clean. CPU-specific optimizations belong in explicit profiles and must not silently raise the minimum CPU requirement.
