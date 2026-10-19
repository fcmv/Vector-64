# Release procedure

This records the current release mechanism and the checks a maintainer needs
before distributing a new version. No release or repository setting is changed
by building these docs.

## Existing mechanism

`.github/workflows/release.yml` builds on version tag pushes; manual dispatch
runs the build, test and packaging stages without publishing, even when dispatched
on a tag. Published tags must use `vMAJOR.MINOR.PATCH` with an optional prerelease
suffix, point into `main` history, and have successful `CI` and `Documentation`
push runs for that exact commit. The latest matching run must be complete and
successful; a pull-request run, manual check or older successful rerun cannot
substitute for a newer failure.

The matrix covers Linux x86-64-v2/v3, ARMv8-A and ARMv8.2 dot-product, macOS ARM64,
and Windows AVX2. Every platform must build all six executables. Each build runs
the full CTest suite, both search fingerprints, UCI startup/search for the four
search binaries, executable interface examples and the visualizer HTTP/evaluation
smoke test before staging. Missing binaries and skipped interface tests fail.

Build jobs have read-only repository access; only the publication job receives
release write permission. Concurrent runs for the same ref are serialized.
Actions are pinned to full commit hashes, and checkouts do not retain credentials.
Manual dispatch never runs the publication job.

Publication first creates or resumes a draft for the exact source commit. It
uploads only missing files, then checks every server-reported SHA256 digest
against the locally verified manifest before making the draft public. It checks
the remote tag again after upload. Existing public releases are refused; changed
or unexpected draft files are refused rather than overwritten. A failed upload
leaves a draft for inspection. Rerun only the failed publication job to reuse the
same verified artifact; a full rebuild may produce different bytes and require
manual review of the earlier draft. Publish corrections under a new version.

Generated notes use `.github/release.yml` categories and the capability text in
`.github/release-notes.md`. Review the generated notes before preparing the tag;
label categories do not replace the release-specific limitations and compatibility
information in the changelog.

## Before tagging

1. Select the exact reviewed commit and confirm its required CI results, including
   both search signatures and applicable inference, variant, UI and training checks.
2. Review [compatibility](STABILITY.md), current [limitations](LIMITATIONS.md), and
   the user-visible changes. Update tagged documentation to match the binaries.
3. Validate the embedded network and record its hash/model card. Build the
   committed UI with the documented Node toolchain when UI sources changed.
4. Smoke-test the actual platform assets: UCI handshake/search, embedded net,
   validator requests, variant fallback, and visualizer startup as applicable.
5. Review the [component terms](THIRD_PARTY_NOTICES.md). Include applicable license
   texts, notices, and source/build information with the distribution. Bare
   binaries alone do not communicate those terms.
6. Prepare release notes with CPU/runtime requirements, capability selection,
   breaking changes, known defects and source/net identity. Generate checksums
   for the final assets; do not claim signing/attestations unless actually produced.

## Tag and inspect

Only a maintainer with approval for publication should create/push a release tag.
A tag triggers an external release workflow. Check every matrix job and inspect
the resulting downloadable assets rather than relying on a successful upload.

Verify a fresh download on the advertised platform, confirm the corresponding
source tag and docs are accessible, and preserve the build/test evidence. The
current process does not define a backport window or a future version roadmap.

## Release history and distribution record

Update [CHANGELOG.md](CHANGELOG.md) before tagging and add a release-specific
guide under `docs/releases/`. Keep the development/release differences in
[versions](docs/versions.md) current. Do not retrofit new commands into an older
release guide. Changes to weights need the model card, binary hash and parity/
strength evidence updated together; the current architecture remains fixed.

Direct executable filenames remain unchanged. Each release also includes:

- `release-notices.zip`: root and Fathom license texts, native dependency texts,
  the model card, and licenses/inventory from every production package installed
  from the UI lockfile. The missing colord npm license is supplied from its exact
  upstream version; an unknown missing license fails packaging.
- `release-source.tar.gz`: corresponding tracked source at the exact commit,
  including the network, UI sources and committed bundle.
- `<platform>.build.json` and `release-builds.json`: compiler identity, configured
  CMake options/flags, source revision, file hashes, fingerprints, network hash,
  and UI bundle/lockfile hashes.
- `SHA256SUMS`: SHA256 for every downloadable file except the manifest itself.

The assembly stage requires all six platforms, verifies binary hashes against
their build records, rejects unexpected files, and checks the final manifest
before publication. Linux uses Ubuntu 24.04; Windows uses MSVC on Windows 2025;
macOS uses the macOS 15 toolchain. CPU compatibility does not establish OS/runtime
compatibility: inspect the toolchain and deployment settings in the build record.

Download `release-notices.zip` with any executable. Verify a fresh download with
`sha256sum --check SHA256SUMS` on Unix or compare `Get-FileHash -Algorithm SHA256`
with the manifest in PowerShell. The existing v1.0.0 Windows hash remains a
historical single-asset record. These records are not signatures or build
attestations, and the license collection does not fill gaps in model provenance.

## Publish documentation

The checked-in `Publish documentation` workflow is manual and restricted to
`main`. It first requires successful `CI` and `Documentation` runs for its
exact commit, builds the strict site with a `build.json` revision record,
uploads a Pages artifact and deploys through the `github-pages` environment.
It follows [GitHub's Pages workflow contract](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages).

After maintainer approval for repository configuration/publication:

1. Configure repository Settings > Pages to use GitHub Actions. Check the
   `github-pages` environment's permitted branches and any approval rules.
2. Push the reviewed documentation change to `main` and wait for both required
   workflows to pass. A successful run on a different commit is insufficient.
3. Dispatch `Publish documentation` on `main`, then inspect build and deployment.
4. Open the reported URL, verify `build.json`, the v1.0.0 guide, internal links,
   screenshots and video playback on desktop/mobile. Keep the repository docs
   link until the site is verified live.

The release guide identifies v1.0.0; it is not an invented archive of a complete
older site. Future frozen full-site versions need their own build/retention
policy. No Pages setting or deployment is performed by a local MkDocs build.
