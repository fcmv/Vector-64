# Building

All commands run from the repository root. Use a separate build directory when
changing compiler, generator, or architecture. A configured CMake tree cannot
be reused across incompatible generators.

## Requirements

- CMake 3.15 or newer, as declared by `CMakeLists.txt`.
- A C++20 compiler and its native build tool. CI exercises GCC, Clang, Apple
  Clang, and MSVC; inspect the workflow for runner versions in a given run.
- Internet access on first configure when `ENGINE_VIZ=ON` (the default), for
  hash-pinned nlohmann/json and cpp-httplib headers.

The C++ engine build needs neither Python nor Node. The default net and the
single-file UI bundle are committed and embedded during the build.

## Linux and macOS

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DENGINE_NATIVE=OFF
cmake --build build -j
ctest --test-dir build --output-on-failure
./build/bin/ChessEngine-nnue
```

Use `-DCMAKE_CXX_COMPILER=clang++` in a new tree to choose Clang. Portable builds
disable native tuning; for a binary used only on the build machine, the default
`ENGINE_NATIVE=ON` enables `-march=native` on applicable non-MSVC builds.

## Windows with MSVC

Run from a Visual Studio developer shell with the Desktop C++ workload and
CMake available:

```powershell
cmake -S . -B build-msvc
cmake --build build-msvc --config Release
ctest --test-dir build-msvc -C Release --output-on-failure
.\build-msvc\bin\Release\ChessEngine-nnue.exe
```

MSVC uses a multi-configuration output directory, so `Release` belongs in both
the executable path and the CTest configuration. The current CMake flags always
include `/arch:AVX2`; `ENGINE_NATIVE=OFF` does not change this.

## Windows with MSYS2 UCRT64

Install the UCRT64 GCC and build tools, and Git Bash or an MSYS2 shell. In
PowerShell, with a typical MSYS2 installation:

```powershell
cmake -S . -B build-ucrt -G "MinGW Makefiles" -DCMAKE_MAKE_PROGRAM=C:/msys64/ucrt64/bin/mingw32-make.exe -DCMAKE_CXX_COMPILER=C:/msys64/ucrt64/bin/g++.exe -DCMAKE_BUILD_TYPE=Release -DENGINE_NATIVE=OFF
cmake --build build-ucrt -j 4
ctest --test-dir build-ucrt --output-on-failure
.\build-ucrt\bin\ChessEngine-nnue.exe
```

Adjust the installation path to your machine. The MinGW build links its runtime
statically; this avoids loading incompatible runtime DLLs from another toolchain
on `PATH`. Use Git Bash/MSYS2 Bash for the repository's shell scripts rather
than assuming Windows' `bash.exe` is the intended shell.

## Build options

| Option | Default | Effect |
|---|---|---|
| `ENGINE_NATIVE` | `ON` | `-march=native` on applicable non-MSVC native builds. Disable for redistribution. |
| `ENGINE_LTO` | `ON` | Interprocedural/link-time optimization. Disable when a toolchain or diagnostic build needs it. |
| `ENGINE_VIZ` | `ON` | Visualizer targets, dependencies, and `viz.*` tests. |
| `ENGINE_VARIANTS` | `ON` | Separate variant core, variant/validator binaries, and variant tests. |
| `EMBED_NNUE` | `nets/stk-vector-64.nnue` | Network embedded in `-nnue`, `-all`, and the visualizer. |
| `STK_UI_BUNDLE` | `ui/dist/index.html` | HTML bundle embedded in the visualizer. |
| `OPT_KING_DANGER` | `OFF` | Perft-oriented king-danger precomputation. |
| `ENGINE_PGO` | `off` | GCC-style profile generation/use: `off`, `generate`, or `use`. |

Variant evaluation experiment knobs are described in [variants](variants.md).
An NNUE target is omitted when its network is missing or the embedding toolchain
is unsupported; `-all` also requires variant support. An omitted target does not
mean that capability was built.

## Engine-only and offline builds

```bash
cmake -S . -B build-engine -DCMAKE_BUILD_TYPE=Release -DENGINE_NATIVE=OFF -DENGINE_VIZ=OFF
cmake --build build-engine -j
ctest --test-dir build-engine --output-on-failure
```

This skips visualization dependency downloads and registers no `viz.*` tests.
Add `-DENGINE_VARIANTS=OFF` if only standard-chess targets are wanted.

## Optional development environments

| Work | Additional requirements |
|---|---|
| Run the example UCI client | Python 3.10+; standard library only. |
| Python tooling/tests | Python 3.10+ and `requirements-dev.txt`; training tests also need NumPy/PyTorch. |
| Train/export NNUE | [CPU/CUDA setup](nnue-training.md). |
| Edit the UI | Node 24 (the CI bundle toolchain), `npm ci` in `ui/`. |
| Build WebAssembly | Emscripten SDK, Bash, and source build tools; see [visualizer](visualizer.md). |
| Build documentation | Python 3.11 and `requirements-docs.txt`; `python -m mkdocs build --strict`. |

Debug configuration enables assertions, but current CMake also applies
optimization flags globally. Use the [sanitizer recipe](testing.md) for memory
and undefined-behavior checks; Debug does not imply an unoptimized binary.
