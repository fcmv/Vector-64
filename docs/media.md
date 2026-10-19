# Demo videos and capture notes

## It's thinking ...

A silent, 100-second recording of Vector Scope, with `fcmv/vector-64` branding.
It keeps the recorded play, board zooms and neuron inspection in their original
order and at normal speed. Four seconds are trimmed from the initial pause.
The title fades in at the screen center, with an animated ellipsis, and fades
away as play resumes. Its position stays fixed as the dots change. When the
enlarged board closes at source time 46.5 seconds, the architecture appears at
the screen center for seven seconds. A fully opaque black backing, regular-weight
44-64 px type and matched fades keep the architecture legible over the network.
The opening title has no backing. The final text retains its fading dark backing.
The final four seconds reference
[the roadmap](roadmap.md). There are no separate explanatory scenes.

[Download the 1920x1080 MP4](assets/it-thinks-1080p.mp4).

<video controls playsinline preload="metadata" width="100%" poster="../assets/it-thinks-1080p.png">
  <source src="../assets/it-thinks-1080p.mp4" type="video/mp4">
  Use the download link above if inline playback is unavailable.
</video>

## Uncaptioned recording

[Download the 104-second source clip](assets/vector-scope-live-1080p.mp4).
This is a normalized copy of the user-provided recording, before the title,
branding overlay and closing text. Both MP4 files are 1920x1080 in 16:9, with
60 fps constant output. The original capture averages about 48.8 fps with
variable timestamps. Repeated frames provide regular output timing; no motion
interpolation creates intermediate board or neural states.

<video controls playsinline preload="metadata" width="100%" poster="../assets/vector-scope-overview.jpg">
  <source src="../assets/vector-scope-live-1080p.mp4" type="video/mp4">
  Use the full-resolution link above if inline playback is unavailable.
</video>

The short GIF is a 960x540 preview. The [illustrated tour](visualizer-tour.md)
provides a text alternative and distinguishes board/root state from a sampled
PV-leaf frame.

## Capture identity and interpretation

The recording was supplied by the maintainer on 2026-10-19. Its metadata identifies
Microsoft Game DVR and a Vector Scope window. It shows one search thread, a
1000-node requested budget, a 350 ms move delay and the H=1024 STK-HalfKA layout.
Other runtime settings and the executable/network hashes are not established by
the recording alone. The raw file hash and selected interval are recorded in
[the edit manifest](assets/it-thinks-1080p.json).

Play starts about 8.7 seconds into the original recording. The board remains
unchanged during the later inspection, while hovering changes the highlighted
connections and detail cards. These are recorded UI states, not invented frames.
UI NPS counters and moves are demonstration state, not controlled throughput or
strength results. Neither MP4 has narration, music or an audio track.

The architecture text follows the [network contract](vector64-spec.md):
22,528 features per perspective, two 1024-wide accumulators, pairwise activation,
a 1024 -> 16 -> 32 -> 1 dense path, eight output buckets and integrated PSQT.
The roadmap reference describes future work, not implemented features or dates.
The project repository is [fcmv/Vector-64](https://github.com/fcmv/Vector-64).

Earlier inspector and tools screenshots came from the native viewer rebuilt
from checkout `7545c5b307bf51dedeefaf4d45d69ebfebdf9daf`, with pending documentation,
theme and media edits. That capture used the shipped network with SHA256
`7b877e6bdefde3b41ef958e3270b3312806382a1e97d5e24f0c0c6217cd87ace`.
Their source and theme differences are identified in
[capture.json](assets/capture.json), alongside the current asset hashes.

The weights remain fixed during play. Positions, activations, selected buckets
and evaluations can change. The view samples a separate integer forward pass;
it is not every visited search node, a training animation, calibrated win odds
or a complete explanation of why search chose a move.

## Reproduce the edit

The renderer needs FFmpeg/ffprobe and local TrueType fonts. Windows uses Segoe UI
and Segoe UI Semilight by default; Linux falls back to DejaVu Sans. Supply
`--font` and `--title-font` for consistent typography. Font files are not shipped
in this repository.

```bash
python tools/docs/render_showcase.py
```

The default input is the committed uncaptioned clip. The renderer selects seconds
4 through 104, applies the overlays, and writes the edited MP4, poster and JSON
hash/timing manifest into `docs/assets/`. Use `--output` for a separate cut.
The input must be 1920x1080, at least 30 fps and cover the selected interval.

For another recording, supply `--input`, `--start`, `--seconds` and
`--playback-start`. The playback timestamp is relative to the input file and
controls when the title fades. Use `--architecture-start` with a source timestamp
and `--architecture-seconds` to align the centered architecture with the network
coming into focus. The roadmap overlay occupies the final four seconds.
Optional `--raw-output` saves an uncaptioned normalized copy from the beginning
of the input through the end of the selected interval.

Keep source masters and recorder logs locally. Verify dimensions, duration,
frame timing, readable overlays and source identity before replacing README
assets. Update the capture notes and hashes with each replacement.
