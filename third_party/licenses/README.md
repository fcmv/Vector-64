# Distribution license texts

These are unmodified upstream license texts used by release packaging. They
supplement the vendored Fathom license and the texts collected from the exact
production dependencies installed by `ui/package-lock.json`.

| File | Upstream identity |
|---|---|
| `nlohmann-json.txt` | [nlohmann/json v3.11.3 LICENSE.MIT](https://github.com/nlohmann/json/blob/v3.11.3/LICENSE.MIT) |
| `cpp-httplib.txt` | [cpp-httplib v0.18.3 LICENSE](https://github.com/yhirose/cpp-httplib/blob/v0.18.3/LICENSE) |
| `colord.txt` | [Pixi colord v2.9.6 LICENSE.md](https://github.com/pixijs/colord/blob/v2.9.6/LICENSE.md); the npm tarball omits this file. |
| `coi-serviceworker.txt` | [coi-serviceworker LICENSE at 7b1d2a0](https://github.com/gzuidhof/coi-serviceworker/blob/7b1d2a092d0d2dd2b7270b6f12f13605de26f214/LICENSE); the worker source matches this revision. |

When updating these dependencies, review and update their license texts as well.
This collection preserves declared terms; it does not change the component
boundaries or resolve the model provenance gaps in the [model card](../../nets/model-card.md).
