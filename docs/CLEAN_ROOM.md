# Clean-room Development Policy

LibreKick must be developed without copying proprietary Kickstart/AmigaOS ROM code or source code.

Allowed inputs include:

- Publicly available official programming documentation and autodocs where redistribution/use is lawful.
- Public API/ABI descriptions and headers that are legally reusable.
- AROS and other suitably licensed open-source implementations, subject to license compatibility review.
- Independently written compatibility tests based on documented or externally observable behavior.
- Measurements of externally visible runtime behavior made on legitimately owned systems/ROMs.

Do not commit or transcribe:

- Decompiled or disassembled proprietary Kickstart implementation code.
- Proprietary ROM byte sequences.
- Leaked or otherwise unauthorized source code.
- Proprietary artwork, fonts, sounds or Workbench assets.

When behavior is ambiguous, document the test case and expected external result. Implement the behavior independently.

Every imported third-party component must record its origin and license before integration.
