# i5-12450HX fixed-depth matrix evidence

This directory preserves the user's completed collection on 2026-10-19,
13:04-13:29 Asia/Calcutta. The engine source is
`85369956e82b82f1bba57b15d67a654f7ec14012`.

The focused matrix contains 28 search profiles and one single/multi perft
profile, with five accepted measured repetitions each: 145 measured samples.
Each profile also has one accepted discarded warmup. Search axes are depths
8, 10, 12, 13, 14 and 16; threads 1, 2, 4, 8 and 12; hash sizes 8, 64 and
256 MB; and MultiPV 1, 3 and 5. Each sweep changes one setting from the
depth-13, one-thread, 8 MB, MultiPV-1 anchor. It is not the full product.

The canary retains the earlier run's 6,396,476 NPS baseline and +/-5% tolerance.
Two calibration attempts failed that reference before the third passed.
Four pre-canary and six post-canary sample attempts were rejected; their logs
remain alongside the accepted measurements.

- `results.json` and `summary.md` are the original completed collector outputs.
- The 558 numbered `.txt` files are original process stdout, including
  signature checks, calibration, warmups, rejected attempts and canaries.
- `sha256.json` records the hashes of those 560 original files.
- `provenance.json` records the source directory, verification performed and
  aggregate perft footers extracted from the accepted raw transcripts.

Every accepted search/perft payload and its canaries were matched to raw stdout.
Binary, network and collector hashes were checked against the local files when
preparing this snapshot. The completed acceptance state and saved node counts
were validated without launching any engine workloads. Originals are preserved
without modification; transient lock and duplicate checkpoint files are omitted.

The machine is an Intel Core i5-12450HX, 8 physical cores and 12 logical
processors, running Windows 11 Pro 10.0.26300. This uses the local GCC native
Release build with LTO and the unchanged embedded H=1024 network. It is not
a timing measurement of the downloaded Windows release executable. Temperature,
affinity and power-mode telemetry were not recorded. No Elo is established.
