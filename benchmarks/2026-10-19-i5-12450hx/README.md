# i5-12450HX benchmark evidence

This directory preserves the user's completed run from 2026-10-19, 11:39-11:42
Asia/Calcutta, at engine source commit
`85369956e82b82f1bba57b15d67a654f7ec14012`.

- `results.json` is the original completed collector state. It includes machine
  information, settings, binary/input hashes, canary calibration, process logs,
  rejected attempts and all 15 accepted measured samples.
- `summary.md` is the original generated report, including warmups and rejected
  attempts in its decision table. Timing medians use accepted measured samples.
- The numbered `.txt` files are the original process transcripts, including
  calibration, warmups, canary brackets and rejected attempts.
- `provenance.json` records the wrapper path-resolution bug and aggregate perft
  footer values extracted from accepted raw transcripts. No timing was rerun
  or adjusted when preparing this snapshot.

The original output was written under `C:\Windows\System32\artifacts` because
the wrapper confused PowerShell's location with the native process directory.
The raw `environment.build_directory` string is consequently wrong. Actual
executable paths and hashes identify `D:\Soumik\Cpp\Chess\build-benchmark`,
and the recorded compiler flags came from that build. The original JSON is
preserved rather than silently editing its metadata.

The H=1024 network SHA256 is
`7b877e6bdefde3b41ef958e3270b3312806382a1e97d5e24f0c0c6217cd87ace`.
This snapshot is a throughput measurement on one machine. It does not establish
an Elo rating or performance across other hardware/build profiles.
