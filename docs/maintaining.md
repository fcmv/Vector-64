# Maintaining the project

Use [contributing](contributing.md) for implementation checks,
[releasing](releasing.md) for publication and [roadmap](roadmap.md) for priority.
This is a working review/triage guide, not a claim that repository protections,
review ownership or response SLAs have already been configured.
See [governance](governance.md), [conduct](code-of-conduct.md) and
[community management](community-management.md) for responsibilities, triage
labels, contributor onboarding and reviewable protection settings.

## Triage and ownership

Ask for the binary/source/net identity and a minimal input before diagnosing a
rules or inference report. Classify confirmed current defects in limitations,
future capabilities in the roadmap and measured experiments in identified
reports. A public issue requesting a private contact must not contain exploit
details. Follow [security reporting](security.md).

Review rules against independent positions/counts where possible. Review search
and weights with separate consistency, speed and strength evidence. Confirm
native/WASM source-list and C++/TypeScript contracts for visualization changes.
The maintainer chooses reviewers and merges. CODEOWNERS records the current
review owner; independent approval is enforced only by active repository rules.

## Documentation and media upkeep

Update each interface's owning reference when its code changes. Keep new commands
out of an older release guide and put user-visible changes in the changelog.
Review examples against the binary named in the page. A green strict MkDocs build
checks local links/anchors, not every semantic assertion or external URL.

README images/videos are real captures with source/network identity in
[media notes](media.md). Re-record when the interface changes materially. Keep
readable captions and a static fallback; do not make a video the only way to
learn a command. Preserve raw benchmark evidence byte for byte and distinguish
screen-demo counters from controlled measurements.

## Facts still needed

The shipped network's exact data/checkpoint/training history and model-specific
distribution terms are not established by the existing artifact. Preserve that
uncertainty in the [model card](model-card.md). Recover records from the actual
run or produce an identified replacement; do not infer a history from a header.

For a replacement run, record data origin/rights/hash, splits/filters, source and
dependency revisions, seed, optimizer and selection settings, checkpoint/model
hashes, integer parity and controlled match evidence. Keep architecture changes
out of this work: the published Windows v1.0.0 NNUE contract remains fixed.

Private reporting, reviewed-merge requirements, tag protection and Pages setup
are repository settings, separate from writing their procedures. Verify their
actual state before claiming they are enabled. A published docs/release workflow
must be inspected after it runs; a local build is not a successful deployment.
