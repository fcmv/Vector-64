# Reviewable community configuration

These files are proposals for GitHub repository settings. GitHub does not
automatically apply them, and this change does not grant access or enable rules.
Both ruleset templates deliberately use `enforcement: disabled`.

| File | Intended use |
|---|---|
| `main-ruleset.json` | One current code-owner approval, resolved reviews, linear history, and required GitHub Actions checks on `main`; no force push, deletion or bypass actors. |
| `release-tags-ruleset.json` | Prevent updates/deletions of `v*` tags after creation, with no bypass actors. |
| `labels.json` | A small area/status vocabulary and contributor-help labels, applied by maintainers. Existing unrelated labels are retained. |

The required contexts are `CI complete` and `documentation`. Integration ID
15368 is GitHub Actions, verified against this repository's check runs. Run the
new workflow on `main` successfully before requiring its new completion check.

There is currently one listed code owner. **Do not activate the main ruleset
until another qualified owner/reviewer has agreed to serve.** A sole owner cannot
independently approve their own changes. The templates contain no emergency
bypass; decide and record that policy explicitly before activation rather than
discovering a lockout during a release.

After explicit maintainer approval, compare the live settings with these
templates, import disabled rulesets through GitHub's rules UI/API, review their
scope, and activate only the approved rules. Update an existing matching ruleset
instead of creating duplicates. Confirm rule insights and test an ordinary pull
request before treating the protection as operational. Tag protection does not
restrict who can create the first tag; choose tag-creation permissions separately.

For labels, compare by exact name and create/update the listed entries only.
Do not delete labels from existing reports, rewrite user content, bulk message
contributors or automatically close old issues as part of setup.

The remaining settings and rollout order are documented in
[community management](../../docs/community-management.md). Templates are based on
[GitHub's repository rules API](https://docs.github.com/en/rest/repos/rules).
