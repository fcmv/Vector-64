# Project governance

Vector-64 is maintained by [@soumik15630m](https://github.com/soumik15630m) in
the [fcmv repository](https://github.com/fcmv/Vector-64). The maintainer is
responsible for scope, review, releases and moderation. There is no elected
committee, foundation or voting process. This document describes how decisions
are made as more people contribute.

## Participation and decisions

Anyone may report a defect, propose a change, review a pull request, improve
documentation or reproduce a result. Follow [contribution guidance](CONTRIBUTING.md)
and the [code of conduct](CODE_OF_CONDUCT.md). Use issues for public technical
discussion; Discussions is not currently enabled.

Small fixes can go directly to a pull request with a reproduction and relevant
checks. Discuss large changes in an issue before committing substantial work.
State the user problem, proposed behavior, compatibility effects, evidence and
maintenance cost. The maintainer records an accepted or declined decision and
its reason in the issue or pull request. Architecture decisions belong in
[the decision log](docs/adr/index.md) when they change a lasting boundary.

The current NNUE architecture remains fixed. Search and training improvements
need the evidence described in [contributing](CONTRIBUTING.md); a higher NPS or
one short match does not establish playing strength. Reactions and comment
volume are useful signals of interest, but they do not replace correctness,
review or evidence. Disagreement about a proposal is not a conduct violation.

## Roles and delegation

| Role | Responsibility |
|---|---|
| Contributor | Proposes and explains a change; supplies reproducible evidence. |
| Reviewer | Checks behavior, tests and compatibility; identifies unresolved concerns. |
| Triager | Reproduces and classifies reports, links duplicates, and helps scope work. |
| Maintainer | Accepts scope and merges, delegates access, and authorizes releases and settings. |

These are responsibilities, not claims that teams or permissions already exist.
The current review owner is recorded in [CODEOWNERS](.github/CODEOWNERS). Review
ownership requests a reviewer; it becomes an enforced approval rule only when
repository protection is configured.

Maintainer access should follow sustained, constructive contributions and
demonstrated knowledge of the affected area. Record proposed appointments and
scope publicly, obtain the person's agreement, then grant only the access they
need. Start triage and review delegation before granting release or admin access.
Remove access when responsibilities end and review credentials during handover.

## Review, releases and continuity

Review the latest revision. Authors should not treat their own work as independent
approval. A change to search, model identity, data rights, public formats or release
workflows needs explicit maintainer review. Do not merge merely because checks
are green when a substantive review concern is unresolved.

Use [the release procedure](RELEASING.md) for publication. Published version tags
and assets identify immutable releases; fixes receive a new version. A failed
upload stays a draft. Do not replace a public executable under an existing name.

There is currently one recorded maintainer, so independent review, moderation
appeals and release continuity have limited redundancy. Add a second qualified
maintainer and a private reporting contact before advertising those capabilities.
The project does not promise response times or automatic succession. Record a
handover of release access, repository administration, reporting contacts and
unresolved security reports when responsibility changes.

Keep this document, CODEOWNERS and actual repository access aligned. Changes to
governance are reviewed in public, except sensitive personal or security details.
