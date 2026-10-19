# Documentation versions

The main documentation describes the development checkout. A command appearing
here is not automatically present in the latest downloadable release.

| Version | Source identity | Documentation |
|---|---|---|
| Development | The commit built by the docs workflow; current source is `main` | This site's main reference, walkthroughs and examples. |
| v1.0.0 | `b301d4fea0faf08fa2cf774438b532b027503fd7` | [Verified release guide](releases/v1.0.0.md), with commands limited to that release. |

The v1.0.0 page is a release-specific guide maintained alongside development
docs. It is not an archived copy of every page on this site. Historical source
and its original documents remain available at the
[tag](https://github.com/fcmv/Vector-64/tree/v1.0.0).

| Surface | v1.0.0 downloads | Development checkout |
|---|---|---|
| UCI search and capability-suffixed binaries | Available | Available |
| Published Windows NNUE topology and shipped weights | Fixed baseline | Same architecture and shipped network identity |
| `--perft` and `--perft-one` | Available | Available |
| `--perft-divide` | Unavailable | Available |
| Shared current training CLI and tagged data contracts | Do not assume current examples apply | Documented and tested here |
| Canary-protected benchmark matrix scripts | Not part of that tagged tree | Available |

Use [CHANGELOG](changelog.md) for behavior changes and
[compatibility](stability.md) for public boundaries. Include the binary hash,
tag/commit and options in a report; a filename alone does not identify a build.

## Documentation publication

The normal documentation workflow checks the site and examples without
publishing. The separate `Publish documentation` workflow is manually dispatched
and deploys its selected `main` commit through GitHub Pages. It requires Pages
to be configured with **GitHub Actions** as its source and a permitted
`github-pages` environment. See the [publication procedure](releasing.md#publish-documentation).

Until a successful deployment is verified, repository-relative links are the
documentation entry point. Preparing a workflow does not establish a live site.
