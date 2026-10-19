# Support and reporting

Start with [getting started](docs/getting-started.md),
[troubleshooting](docs/troubleshooting.md), and [known limitations](LIMITATIONS.md).
For reproducible defects or usage questions, use the
[repository issues](https://github.com/fcmv/Vector-64/issues).
Contributions follow [CONTRIBUTING.md](CONTRIBUTING.md).
Use the issue chooser's relevant form: defect, feature, documentation, performance
or question. Discussions is not currently enabled. For an unrelated private
contact request, use the question form without incident details or attachments.
Community responsibilities and behavior follow [governance](GOVERNANCE.md) and
[the code of conduct](CODE_OF_CONDUCT.md).

## A useful engine report

Include the executable name and version/tag/commit, OS and CPU/ISA, compiler
flags if built locally, network SHA256, options, and the smallest FEN plus move
history that reproduces it. Paste the exact commands and actual/expected reply.

For rule problems, give the expected legal move, status, or reference perft count.
For a search problem, give budget, threads/hash, reset state, and whether it
persists with `Threads=1`. For a strength claim, include the match settings and
SPRT verdict rather than only an Elo point estimate.

For UI/browser failures, include native versus WASM transport, browser version,
origin, isolation/SharedArrayBuffer status, and console error. Do not attach
private datasets, credentials, or sensitive local paths unnecessarily.

Suspected security issues should follow [SECURITY.md](SECURITY.md). Ordinary
illegal-move or score bugs can be reported as functional defects. There is no
promised response time or paid support commitment in this repository.
