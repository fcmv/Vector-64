# Repository layout

The engine, visualization, training tools and documentation have separate owners
in the source tree. Moving a file does not change the released NNUE architecture.

```text
app/                    Native engine entry point
src/
  cores/                Positions, moves, attacks and hashing
  search/               Search, evaluation and the tablebase adapter
  nnue/                 Integer inference and embedded-network support
  datagen/              Native self-play data generation
  perft/                Shared perft and EPD diagnostic implementation
  uci/                  Protocol handling
  viz/                  Telemetry, native viewer and WASM bindings
third_party/fathom/     Vendored tablebase prober, revision record and license
cmake/                  Compiler options, targets, embedding and test registration
tests/                  C++, Python and executable-documentation checks
test_data/              Stable shared EPD workload
tools/
  bench/                Benchmark collectors, build and profiling helpers
  nnue/                 Shared training, export and feature contracts
  bullet/               External trainer integration
  experiments/          SPRT drivers and historical experiment reproductions
  docs/                 Documentation validation and media rendering
ui/                     React/TypeScript source and the embedded HTML bundle
docs/                   Reference documentation and small presentation assets
examples/               Integration and tiny training examples
nets/                   Shipped network and model card
benchmarks/             Immutable identified measurement records
out/build/              Ignored local build trees created by presets
artifacts/              Ignored local outputs and recording masters
```

## Build definitions

The root `CMakeLists.txt` establishes the project and includes the focused
modules in `cmake/`. Target names and `bin/` output locations remain stable.
`BUILD_TESTING=OFF` omits test executables and CTest registrations; perft commands
remain available because their implementation belongs to the engine source.
`ENGINE_VIZ=OFF` omits the visualization targets and their fetched dependencies.
The standard and variant cores retain their separate compilation boundaries.

Use the [build presets](building.md#build-presets) for new build trees. Existing
`cmake -S . -B build` commands still work. Do not relocate an existing CMake
cache to a new path; configure a new tree and retire the old one when no longer
needed. `CMakeUserPresets.json` is ignored for personal toolchain paths.

## Python packages and compatibility commands

`tools.nnue`, `tools.bench` and `tools.bullet` use package-relative imports.
For example:

```bash
python -m tools.nnue.make_net --help
python -m tools.bench.benchmark --help
python -m tools.bench.benchmark_matrix --help
```

Existing file commands such as `python tools/run_pipeline.py`,
`python tools/benchmark.py` and `python tools/nnue/make_net.py` remain supported.
Standalone launch guards register the local package and invoke the same module
without changing the working directory or modifying `sys.path`. Relative input
paths keep their original meaning. The root PowerShell and Bash compatibility
launchers forward to their implementations under `tools/bench/` or
`tools/experiments/`.

The canonical expected search counts stay in `tools/bench_signature.txt`.
Historical SPRT scripts identify their original revisions and may require local
assets that are not available in a fresh clone. They are not current baselines.
Benchmark collectors still reject changed run identities; complete an old
resumable run using its original source revision instead of relabelling it.

## Generated and large files

Keep the shipped network available to fresh-clone builds and preserve the
committed single-file UI bundle so native builds do not require Node. Local
training shards, checkpoints, recordings and build outputs belong in ignored
run/artifact directories. Published benchmark records retain their exact bytes.

For future long videos and recording masters, prefer versioned release assets
or durable media hosting. Keep a lightweight preview, a text alternative, source
identity and SHA256 manifest in the repository. Existing published recordings
remain in place so current links and capture manifests keep working. Moving an
asset out of the working tree does not remove its earlier Git history.
