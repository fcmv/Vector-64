# Vector-64 documentation

Start with the task you want to complete. These pages describe the current
checkout; released binaries should be paired with documentation from their tag.
The NNUE architecture is fixed to the published v1.0.0 Windows `-nnue.exe`;
the current STK-HalfKA implementation retains that contract.

## Use or integrate the engine

| Task | Start here |
|---|---|
| Choose a download, install in a GUI, or run a first search | [Getting started](getting-started.md) |
| Build on Linux, macOS, MSVC, or MSYS2 | [Building](building.md) |
| Set options, supply positions, manage clocks and searches | [UCI reference](uci.md) |
| Query legal moves and structured position state | [Validator protocol](validator.md) |
| Connect rules/AI workers to a host application | [Integration guide](engine-integration-response.md) |
| Use crazyhouse or host-managed bughouse reserves | [Variants](variants.md) |
| View inference, run analysis, or build the browser engine | [Vector Scope](visualizer.md) |
| Diagnose a failed build, load, or integration | [Troubleshooting](troubleshooting.md) |

## Understand and contribute

- [Architecture](architecture.md): module boundaries and runtime flows.
- [Engineering guide](implementation/engineering.md): actual code paths,
  invariants, ownership, and tests.
- [Engine contract](spec/engine-contract.md): representations, rules, state,
  evaluation conventions, and failure behavior.
- [STK-HalfKA contract](vector64-spec.md): current feature/model/binary layout.
- [NNUE training](nnue-training.md): a tiny CPU run through export and parity.
- [Testing](testing.md): commands and what each check establishes.
- [Glossary](glossary.md): chess-engine terminology used in these pages.
- [Architecture decisions](adr/index.md): constraints and measured decisions.

## Project references

- [Contributing](contributing.md), [support](support.md), and
  [limitations](limitations.md).
- [Compatibility](stability.md), [benchmark methodology](benchmark.md), and
  [release procedure](releasing.md).
- [Roadmap](roadmap.md): priorities, acceptance conditions and feature candidates.
- [Third-party notices](third-party-notices.md) and
  [shipped model](model-card.md).

Commands assume the repository root. MSVC Release executables are under
`build/bin/Release/`; single-configuration builds use `build/bin/`.
