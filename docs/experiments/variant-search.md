# Historical variant search experiments

These measurements were reported in `docs/variants.md` at source commit
`7e89a6581ff62049b7eade744213843f27d2f442`. They explain the history behind
current defaults; they were not rerun for this documentation update. Some
comparisons identify only a branch or previous tip, without complete binary,
network and raw-result identity. Preserve that gap rather than reconstructing
a run from the point estimate.

[Variants](../variants.md) describes current behavior and CMake settings.
[Benchmark methodology](../benchmark.md) describes the evidence needed for a
new claim. No number here establishes an absolute engine rating or a roadmap.

## Evaluation and search corrections

The original notes report two defects corrected before these tuning defaults:

- A loaded standard net was still reached by the search fallback in a drop
  variant, despite the non-search `eval` route disabling it. Rebuilding both
  accumulators at each affected node also imposed a large cost. A reported
  crazyhouse start-position run, one thread and three seconds, moved from
  0.61M to 3.32M NPS and depth 13 to 16 after correction. Hardware and full
  executable identity were not retained in this note.
- Reserve material was omitted from evaluation. Enabling it reported
  `+54 =0 -3` over 57 games, H1 accepted at LLR +3.65. The reported +502 Elo
  estimate is highly uncertain at that sample/score; retain the observations
  rather than interpreting the point estimate as a precise rating gain.

The notes also report matching fixed-node variant searches between the
non-embedded and embedded binaries after the NNUE fallback correction.
Current checks and limitations remain the authority for today's checkout.

## Reported tuning comparisons

The original setup was crazyhouse, 25,000 nodes, SPRT H0 Elo <= 0 versus
H1 Elo >= 5, using `tools/sprt_variant.ps1`.

| Change | Reported Elo estimate | Games | Reported verdict |
|---|---|---|---|
| Reserve material on versus off | +502 | 57 | H1 accepted |
| Drop history on versus off | +51.3 +/- 18.2 | 1,406 | H1 accepted |
| Null move off versus on | -16.1 +/- 10.9 | 3,850 | H0 accepted |
| Checking-drop quiescence depth 2 versus 0 | -21.4 +/- 12.5 | 2,960 | H0 accepted |

These comparisons explain why dedicated drop history and null-move pruning
remain enabled, while the checking-drop quiescence depth defaults to zero.
Drops use their source field for a piece type, so a separate history table
avoids aliasing ordinary `[from][to]` move history.

The quiescence experiment was rerun after fixing reserve evaluation. Its
reported -21.4 +/- 12.5 result was close to an earlier -20.8 +/- 12.4 result;
the notes attributed the cost to extra search work. That attribution is a
historical interpretation, not independently established by this archive.

## Reported evaluation terms

| Change | Reported Elo estimate | Games | Reported verdict |
|---|---|---|---|
| Crazyhouse piece values | +30.6 +/- 13.6 | 2,512 | H1 accepted |
| King danger, scale 6 | +9.5 +/- 8.7 | 6,000 | Game cap, positive estimate |
| King danger, scale 14 | +10.3 +/- 8.7 | 6,000 | Game cap, positive estimate |
| Both terms versus neither | +25.2 +/- 12.3 | 3,061 | H1 accepted |

Neither king-danger comparison alone reached its reported SPRT bound. Scale 6
was retained with the jointly tested piece-value settings. A game-cap result
is inconclusive under that stopping rule even if its point estimate is positive.

## Bughouse without partner feed

The notes report a -66 Elo result when crazyhouse board-value corrections were
applied unconditionally to a bughouse match. A standalone bughouse game starting
with empty hands acquires no local reserves: captured pieces leave for an absent
partner board, so it cannot exercise realistic drop play.

The evaluation correction was gated on crazyhouse capture semantics or either
side having a reserve. The archive reports unchanged fixed-node score/PV/counts
for the empty-hand bughouse path afterward. This describes the reported setup;
it does not prove partner-fed bughouse strength.

A symmetric reserve-position example was reported to move from +337 for White
to +20 after the evaluation corrections, replacing a sequence of early queen,
bishop and rook drops with development. The exact FEN and raw search trace were
not preserved in these notes, so that example cannot be reproduced from this
page alone.

## Combined historical result

The old branch-versus-previous-tip comparison reported crazyhouse `+49 =0 -1`
over 50 games, H1 accepted at LLR +8.74, with a +676 Elo point estimate. The
small, lopsided sample and incomplete identity prevent treating that estimate
as a precise or transferable improvement for the current engine.

The material-adjudication defect now documented in
[limitations](../limitations.md#material-adjudication) is a further reason to
review referee behavior before relying on retained self-play results.
