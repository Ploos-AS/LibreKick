# Roadmap

## Project-wide machine-variant policy

LibreKick is not a single generic ROM image. The project will build, qualify, version and retain explicit ROM variants for the supported Amiga models, comparable to the per-machine strategy used by LibreTOS and LibreROM.

**Shared source does not imply a universal ROM.** Common source code, schemas, build tooling and CI infrastructure are shared wherever practical, but every supported machine profile has its own deterministic ROM build and qualification path. A universal image may be explored as an optional convenience in the future, but it must never replace the model-specific ROMs.

Each supported machine profile gets a stable identifier, deterministic build target, emulator configuration, qualification status and retained release artifact. Common code is shared wherever possible, while machine-specific bootstrap, chipset, expansion, storage and ROM-layout differences remain explicit.

Every LibreKick release that claims support for a machine must publish that machine's qualified ROM image as a separate release artifact. Previously supported model-specific ROM variants remain buildable, reproducible and available when support for newer machines is added.

The project-wide pipeline is therefore:

**shared source → machine profile → machine-specific build → machine-specific qualification → separate retained release ROM**

Initial machine families:

- A1000
- A500
- A500+
- A600
- A2000 / A1500
- A2500/20 and A2500/30
- A3000 / A3000T
- A1200
- A4000 / A4000T
- CDTV
- CD32

See `docs/MACHINE_PROFILES.md` for the profile and artifact policy.

## M0 — Foundation

- Project scope and compatibility contract.
- Clean-room policy.
- Architecture and source layout.
- MIT licensing.
- Deterministic 512 KiB ROM-image build/check skeleton.
- Define machine-profile naming and retained per-model artifact policy.

## M1 — First bootable ROM

- 68k reset/bootstrap path.
- Valid ROM layout/checksum handling.
- Early serial/debug output.
- FS-UAE qualification on a 68000-class profile.
- AROS ROM/runtime material used only as legally compatible reference/integration input.
- Establish the first retained A500 LibreKick variant as the baseline, without treating it as the only target.

## M2 — Core runtime

- Exec-compatible minimum core.
- Memory, tasks, interrupts, libraries and resources needed for controlled test programs.
- A500/A500+/A600 runtime matrix.
- Split common runtime from machine-profile glue so all later milestones can be built per model.

## M3 — Devices and expansion

- timer.device, trackdisk.device and input foundations.
- AutoConfig/expansion path.
- Boot-device and filesystem handoff.
- Add retained A1000, A2000/A1500, A2500 and CDTV profiles where the required hardware paths are implemented.

## M4 — V40 compatibility surface

- Systematic library/device API and ABI compatibility work.
- Compatibility test suite derived from public documentation and black-box behavior.
- A1200/A3000/A4000 profiles.
- Add retained A3000/A3000T, A1200 and A4000/A4000T ROM variants rather than replacing the 68000-family variants.

## M5 — Workbench-era application compatibility

- Boot a compatible disk environment.
- Run representative AmigaOS 3.1 applications.
- Regression qualification across CPU/system profiles.
- Add and retain the CD32 profile when its chipset/boot requirements are supported.
- Run cross-model regression so development of later machines cannot silently break earlier LibreKick variants.

## M6 — Hardware qualification and extended ROM profiles

- Real Amiga ROM testing.
- 512 KiB baseline plus optional larger ROM profiles.
- 68020/030/040/060-specific optional optimizations without breaking the 68000 baseline.
- Hardware qualification is recorded per machine profile and per released ROM artifact.
- Released model-specific ROM images remain reproducible and available after newer models or optimizations are added.
