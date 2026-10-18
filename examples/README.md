# Runnable examples

Run these commands from the repository root with a built engine.

```bash
python examples/uci_client.py --engine build/bin/ChessEngine --depth 6
```

The client waits for handshake/readiness/search completion and bounds its reads.
It sets one thread and an 8 MB hash. It is a small single-client example, not a
multi-user engine pool or a parser for every UCI output field.

`training_positions.txt` contains eight labelled standard-chess FENs. Labels are
**synthetic demonstration values in White-relative centipawns**, not strong-engine
annotations or an evaluation corpus. They are sufficient to exercise data,
optimization, export and parity. Follow [the CPU walkthrough](../docs/nnue-training.md#tiny-cpu-walkthrough).

MSVC paths include `bin/Release/*.exe`; MSYS2 paths use `bin/*.exe`. These examples
use the current checkout CLI and do not assert that every command exists in v1.0.0.
