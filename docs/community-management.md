# Community management

Use [governance](governance.md) for decision authority and [the code of conduct](code-of-conduct.md)
for behavior and moderation. This page is the operational guide for handling
more reports and contributors without making every interaction depend on one
maintainer's memory.

## Routing and triage

The issue chooser provides defects, feature proposals, documentation corrections,
performance reports and questions/contact requests. Discussions is currently
disabled, so usage questions still go to issues. Security reports use
[the private-reporting guidance](security.md); a public report must not request
exploit details or personal information.

Triage starts by finding related reports, checking the reported source/binary
identity and asking for the smallest missing piece of evidence. Ask a specific
question instead of requiring a contributor to rerun every test. For a duplicate,
link the existing report and preserve any new reproduction or evidence before
closing it. Documented limitations can still be valid defects.

Use one primary area label from `.github/community/labels.json` where possible.
`status:confirmed` means a defect is established; `status:accepted` means a
proposal's scope and acceptance criteria are agreed. `status:needs-info` should
name the missing information, and `status:blocked` should name its dependency.
Remove obsolete status labels as a report progresses. Lack of a status or
priority label does not mean a report has been rejected.

Maintainers assign `priority:high` for serious impact or a release blocker.
Correctness failures, crashes, lost data and regressions take precedence over
feature requests. Record impact and reproduction when deciding priority. Keep
security details private rather than encoding them in public labels.

## Helping contributors and reviewers

Mark `good first issue` only when the task has a bounded goal, a starting point,
clear verification and someone available to answer questions. Use `help wanted`
for accepted work that needs assistance. Avoid reserving broad features indefinitely;
coordinate an active attempt in the issue and make it clear when work is available.

Draft pull requests can be used to agree on an approach early. Reviewers should
distinguish required changes from suggestions and explain the relevant invariant.
Ask for evidence proportionate to the change. Do not request a full playing-strength
campaign for a documentation correction, or accept a search improvement solely
because it compiles. Follow [contribution checks](contributing.md).

Before merging, identify the responsible reviewer, verify the latest revision's
checks and settle substantive review threads. For outside contributions, the
first run may require maintainer approval. Inspect workflow/dependency changes
before approving that run; never expose repository secrets to untrusted builds.

Use GitHub Projects or milestones when the issue queue needs a shared view of
accepted work. Link each item to its public acceptance criteria. A milestone is
planning, not a promised release date. Periodically review blocked work and
maintenance capacity. Do not close reports merely because time has elapsed;
request a named missing input or record an explicit decision with a reason.

## Repository settings and rollout

Read-only API inspection on 2026-10-19 found no repository rulesets or classic
protection on `main`. Discussions, private vulnerability reporting, Dependabot
security updates, secret scanning and push protection were disabled. Those are
settings observations at that date, not properties of the source tree. No setting
was changed by this documentation or its configuration templates.

After explicit maintainer approval, use this rollout order:

1. Establish private vulnerability reporting and a confidential conduct contact.
   Publish only an agreed public contact; do not reuse a contributor's Git email
   address without permission. Test the reporting route with a harmless report.
2. Review security-update and secret-scanning/push-protection options supported
   by the repository's account. Enable the chosen controls and confirm how
   maintainers receive and triage their alerts.
3. Merge the workflow/community files and obtain successful `CI complete` and
   `documentation` checks. Confirm CODEOWNERS is recognized and add another
   qualified owner before requiring independent approval of owner-authored work.
4. Review/import the disabled [ruleset and label templates](https://github.com/fcmv/Vector-64/blob/main/.github/community/README.md).
   Decide bypass and tag-creation policies, then activate the agreed protections.
   Do not activate a rule that leaves the project unable to review its own work.
5. Decide whether Discussions would help separate Q&A and proposals from bugs.
   If enabled, create the agreed categories and then update the issue chooser
   and support page. Do not link to categories that do not yet exist.
6. As reviewers join, delegate triage and area ownership before release/admin
   access. Record membership changes and review active access during handover.

The workflows support merge-group checks if a merge queue is adopted later;
this does not enable a queue. Branch/tag rules and protected release/Pages
environments remain repository configuration. Verify them after setup instead
of treating a checked-in file as enforcement.

## Releases and operational review

Use [the release procedure](releasing.md). Uploads stay in a draft until the full
file set and server-reported SHA256 digests match. A retry can resume identical
draft assets; changed or unexpected assets require maintainer inspection.
Published assets and tags must not be replaced to repair a failed release.

Review support load, unresolved serious defects, time awaiting review and flaky
checks when choosing maintenance work. Use these signals to improve capacity;
they are not contributor rankings. Do not publish response-time commitments
or a backport window until maintainers can sustain them.
