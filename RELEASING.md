# Release procedure

This records the current release mechanism and the checks a maintainer needs
before distributing a new version. No release or repository setting is changed
by building these docs.

## Existing mechanism

`.github/workflows/release.yml` builds on `v*` tag pushes; manual dispatch builds
without its tag-only publication step. The matrix covers Linux x86-64-v2/v3,
ARM64 and dot-product, macOS ARM64, and Windows AVX2. It stages up to six binaries
per platform and publishes them through a GitHub Release. The current workflow
runs a classical perft sanity check before staging; it does not itself establish
that the full CI or every staged capability passed.

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

The current tag workflow still publishes bare binaries. A complete future
distribution should carry the actual applicable license texts/notices, source
commit, compiler/toolchain/build flags and network hash, with SHA256 for every
final downloadable file. Generate checksums after packaging and verify them
against a fresh download. The existing single Windows NNUE hash is not a full
cross-platform checksum manifest. `THIRD_PARTY_NOTICES.md` is an inventory, not
a substitute for missing dependency license texts or model provenance.

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
