# Compatibility boundaries

This page identifies the interfaces callers can depend on and the boundaries
that still need care. It does not retroactively invent a semantic-versioning
policy for older releases. Use a release's matching tagged docs; the development
checkout can contain commands not present in the latest published binary.

## Public surfaces

- Standard UCI setup, position, search and lifecycle commands, plus the options
  advertised by the binary's `uci` response.
- The documented validator commands, JSON fields, UCI drop notation, bracketed
  reserve FEN, and promoted `~` markers in variant builds.
- The STK-HalfKA network header/layout and supported 1024/128 widths.
- Documented data manifest tags, label perspective, training entry points, and
  export/check commands in the current checkout.

The fixed NNUE architecture is the one in the published v1.0.0 Windows
`-nnue.exe`, as identified in the [network contract](docs/vector64-spec.md).
The current implementation retains that architecture. This documentation update
makes no architecture migration or future feature commitment. The old
`VECTOR64_NNUE` HalfKP format is incompatible; it is not silently converted.

The custom protocol has no version negotiation. Dataset/network versions exist,
but not every checkpoint or human diagnostic has a stable schema. Integrators
should pin a build and run conformance checks when updating it. Reject unknown
required formats rather than guessing how to reinterpret data.

## Implementation details

Internal C++ symbols/layout, TT replacement heuristics, search ordering, scores,
PVs, exact best moves and node counts are not general compatibility guarantees.
The regression signatures constrain a particular source/net configuration;
intentional search changes can legitimately change them. Human `info string`
wording and JSON key order are not a parsing contract.

Do not parse successful UCI silence as acknowledgement of an unknown option.
Use the handshake and structured fields. The advertised option range is the
client-facing boundary even where a parser accepts a broader numeric input.

## Threading, state and numerical identity

Integer scalar/SIMD parity is defined for the same network and position on tested
supported kernels. Floating training outputs may differ after quantization.
Reproducible single-thread search additionally requires matching options, history,
reset state and a fixed budget. Timed and SMP searches can differ.

Network files use little-endian fields. Existing supported x86/ARM release
profiles are little-endian; host-native loader reads do not establish big-endian
portability. Known load and adjudication defects are listed in
[LIMITATIONS.md](LIMITATIONS.md).

## Changes and migrations

A change affecting a documented command, field, rule profile or file format
should describe its compatibility impact and migration in the same PR. Preserve
existing documentation URLs when replacing old pages, or leave a forwarding page.
Do not announce unimplemented deprecations or future support windows here.
