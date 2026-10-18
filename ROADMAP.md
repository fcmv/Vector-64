# Roadmap

This roadmap orders work on Vector-64's current engine, training tools and
Vector Scope. It records priorities and candidate directions, without assigning
release dates or treating an experiment as an accepted improvement.

The fixed NNUE architecture is the one in the published v1.0.0 Windows
`STK-Vector-64-windows-x86-64-avx2-nnue.exe`. Its embedded network matches the
repository's shipped model byte for byte. The [network contract](docs/vector64-spec.md)
records its features, layer sizes, integer arithmetic, file format and release
identity. Training better weights, improving inference implementation and tuning
search can proceed within that contract. A replacement feature set or topology
requires a separate decision.

Current behavior belongs in the [documentation](docs/index.md), confirmed defects
in [LIMITATIONS.md](LIMITATIONS.md), and measured results in identified experiment
reports. An unchecked item here is future work, not a claim that it ships today.

## Now: correctness and dependable interfaces

These items address known failures before expanding the supported surface.

- [ ] **Correct material adjudication.** Repair the false insufficient-material
  result for the documented mate-in-one counterexample. Cover opponent blockers,
  bishop square colors and reserves with independent rule cases. State the exact
  supported material/dead-position semantics and distinguish claimable draws
  from automatic game termination. Completion requires regression cases without
  false draw declarations and a documented host adjudication boundary.
- [ ] **Make network replacement transactional.** Read and validate into
  temporary state, then replace the active network only after success. Cover
  missing files, invalid headers, truncated payloads and repeated reloads for
  both supported widths. After a failed replacement, the previous network's
  identity, loaded state and evaluations must remain intact.
- [ ] **Repair tablebase search boundaries.** Disable standard-chess probes in
  drop variants, preserve UCI `searchmoves` restrictions during root ranking,
  and supply the appropriate repetition state to DTZ ranking. Verify WDL/DTZ,
  halfmove-clock behavior and missing-file fallback with identified table files.
- [ ] **Harden external position and protocol input.** Add malformed FEN/move,
  reserve and command cases, bounded-buffer checks and fuzz coverage. Preserve
  resident state after rejected input and keep structured inline failures
  distinct from process failure. Review custom JSON capability/version handling
  before adding incompatible fields or command semantics.
- [ ] **Stress search lifecycle and shared state.** Exercise repeated searches,
  stop/quit, option changes, persistent ordering and TT/evaluation interaction
  under varied time controls and thread counts. Record what concurrency checks
  establish; passing ordinary sanitizers alone does not prove race freedom.

## Next: reproducible OSS releases

- [ ] **Package complete releases.** Ship platform binaries with applicable
  licenses/notices, a short usage guide, SHA256 checksums, source commit,
  network identity and build-toolchain details. Resolve the recorded component
  and model distribution questions without inventing missing provenance.
- [ ] **Verify the downloadable artifacts.** Gate release commits on required
  checks and smoke-test UCI search, embedded NNUE, validator queries, variant
  fallback and visualization on the actual supported platform assets. Document
  CPU and runtime requirements and the supported configuration matrix.
- [ ] **Protect the maintenance path.** Configure reviewed merges and required
  CI checks, choose release-tag protection and review ownership, and establish
  an actionable private security-reporting route. Repository-setting changes
  require maintainer approval when implemented.
- [ ] **Publish versioned documentation and release history.** Publish the docs
  site, distinguish release-tag documentation from development documentation,
  and maintain a changelog for user-visible behavior and compatibility changes.
  A fresh-clone reader must be able to follow the documented examples.
- [ ] **Pin and maintain build inputs.** Validate a fixed Emscripten version,
  define tested Python versions, cover UI dependency updates and record native
  dependency revisions. Exercise engine-only and variants-disabled builds.
- [ ] **Record release provenance.** Add verifiable build attestations when the
  packaging and verification process is established. Provenance supplements
  artifact tests and component notices.

## Next: reproducible training within the released architecture

- [ ] **Add held-out checkpoint selection to the shared trainer.** Split by
  game/source where possible, use deterministic evaluation samples, record the
  selection criterion and export the selected checkpoint. Compare training loss,
  held-out prediction quality, quantization effects and match strength separately.
- [ ] **Make every run identifiable.** Record data hashes and source rights,
  filtering, label perspective, seed, dependency/toolchain versions, settings,
  checkpoints and resulting network hashes. Preserve compatible resume behavior
  and fail clearly when inputs or settings change.
- [ ] **Make Bullet runs isolated and reproducible.** Pin a compatible external
  revision and example registration procedure. Replace existence-only reuse and
  shared checkpoint deletion with per-run storage and identity checks. Reject
  empty/non-finite oracle output and align wrapper batch/superbatch settings
  with the actual Rust trainer.
- [ ] **Produce an identified full training and evaluation report.** Use an
  explicit current baseline instead of assuming historical `runs/v2` assets.
  Retain held-out results, exact integer parity, mirror checks, model metadata
  and controlled match artifacts. Dataset size is a recorded experimental
  choice, not a promised strength improvement.

The old proposal for reserve NNUE features and different feature-count formats
is parked because it changes the fixed architecture. Drop variants continue
to use classical evaluation under the current scope.

## Then: measured search and variant strength

- [ ] **Build a durable experiment workflow.** Extend the existing match tools
  with an experiment queue, immutable run metadata and readable reports. Validate
  referee behavior against independent rule cases. Preserve hypotheses, budgets,
  openings, W/D/L, LLR and accepted/rejected/inconclusive outcomes.
- [ ] **Model reserves in exchange evaluation.** Develop and test reserve-aware
  SEE or a measured alternative. Respect crazyhouse local reserve ownership,
  promoted-piece reversion and bughouse partner transfers. Keep ordinary chess
  behavior isolated from variant-specific evaluation changes.
- [ ] **Retune variant pruning with evidence.** Evaluate reverse/quiet futility,
  move-count pruning, LMR and quiescence delta margins one change at a time.
  Test narrower null-move reserve conditions rather than assuming that disabling
  null move improves drop play.
- [ ] **Improve classical variant evaluation.** Measure mobility, pawn structure
  and defended king-ring/drop-threat terms against identified baselines. Account
  for evaluation cost as well as relative playing strength.
- [ ] **Expand tactical and endgame regression coverage.** Curate licensed,
  identified position suites with expected behavior and fixed budgets. Use
  tactical solve rates and performance measurements alongside controlled matches.

Checking-drop quiescence already exists experimentally and defaults to off after
the reported negative tests. Incremental NNUE, integer export parity, drop
history and reserve material are also already implemented. New experiments must
start from that state; historical completed work is not a new milestone.
See [historical variant experiments](docs/experiments/variant-search.md).

## Later: feature candidates

These candidates need individual scope and acceptance criteria before work starts.

| Candidate | Intended result / boundary |
|---|---|
| Annotated PGN export and batch analysis | Build on existing PGN input/history with saved evaluations, variations and game reports. |
| Exportable network-comparison reports | Extend existing comparison/ablation views with repeatable position sets and saved evaluation/activation differences. |
| Reliable browser execution | Add real browser startup and integer-parity checks, version/cache diagnostics and a single-thread fallback when isolation is unavailable. |
| Typed integration client | Extend the example client with capability checks, bounded requests, structured errors and worker lifecycle management. |
| Chess960 | Specify FEN, castling and UCI semantics, then establish independent legal-tree and state-transition coverage. |
| Additional two-player variants | Consider atomic, horde, king of the hill, three-check and racing kings separately, each with explicit rules, evaluation and tests. |
| Partner-aware bughouse | Define partner-board/clocks input, transfer ordering and incoming-material estimates before sitting/time policy or broader coordination. |
| Broader Windows CPU support | Evaluate a portable build using the existing scalar inference path, with parity, performance and minimum-runtime verification. |

PGN input, history navigation, evaluation graphs, network comparison, single-line
validator requests, `children` and JSON search summaries already exist. Candidate
work extends those capabilities rather than promising their first implementation.

## Research and deferred scope

- Four-player chess and chaturaji were discussed in older notes. They remain
  exploratory work, with separate player-count, search and possibly geometry
  requirements. Their presence in a historical worktree does not establish
  implementation or a delivery commitment.
- Joint search of both bughouse boards is research beyond the initial partner
  protocol and supply model.
- Changes to NNUE features/topology, including reserve feature blocks, remain
  deferred under the released-architecture constraint.
- Distributed volunteer testing can be reconsidered after a small, reliable
  local experiment queue demonstrates a need for it.

## Updating this roadmap

An implementation PR should identify its roadmap item, resulting behavior,
compatibility impact and decisive verification. Mark an item complete only when
its implementation and acceptance evidence are available. Link the relevant
issue, PR or experiment when one exists; do not invent tracking links or dates.

Use [CONTRIBUTING.md](CONTRIBUTING.md), [testing](docs/testing.md) and
[benchmark methodology](BENCHMARK.md) for evidence requirements. Search speed,
integer consistency and playing strength are distinct results. Update current
references and known limitations when their underlying behavior changes.
