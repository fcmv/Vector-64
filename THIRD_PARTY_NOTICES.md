# Components and notices

This inventory records the terms declared in the repository and dependency
metadata. It does not relicense components or resolve every combined-distribution
question. The root [LICENSE](LICENSE) contains Apache-2.0; the UI package declares
GPL-3.0-or-later. A redistribution needs the applicable texts and attribution,
not merely a pointer to this inventory.

| Component | Source / identity | Declared terms / use |
|---|---|---|
| Engine project | Root source and `LICENSE` | Apache-2.0 at the repository root. |
| Vector Scope UI | `ui/package.json`, `ui/package-lock.json` | UI package declares GPL-3.0-or-later. |
| Chessground | `chessground` 9.2.1 in the lockfile | GPL-3.0-or-later; used by `ui/src/components/Board.tsx`. |
| chess.js | 1.4.0 in the lockfile | BSD-2-Clause. |
| React and React DOM | UI dependency lockfile | MIT. |
| PixiJS | UI dependency lockfile | MIT. |
| Fathom | Vendored commit `c9c6fef0dddc05d2e242c183acf5833149ab676d` | MIT; [vendoring record](src/syzygy/README.md) and [license](src/syzygy/LICENSE). |
| nlohmann/json | v3.11.3, SHA256-pinned native fetch in CMake | MIT; used by visualization. |
| cpp-httplib | v0.18.3, SHA256-pinned native fetch in CMake | MIT; native visualizer HTTP. |
| coi-serviceworker | v0.1.7 banner in `ui/public/coi-serviceworker.js` | MIT; Guido Zuidhof and contributors. |
| Embedded STK-HalfKA weights | `nets/stk-vector-64.nnue` | No separate model-specific license/provenance manifest is present; see [model card](nets/model-card.md). |

The UI is bundled into `ui/dist/index.html`, embedded in the native `-viz`
executable, and used by the browser/WASM distribution. Its dependency terms do
not disappear when bundled. Chessground publishes explicit
[licensing guidance](https://github.com/lichess-org/chessground#license).
The engine-only targets do not link the UI, cpp-httplib, or nlohmann/json.

For a release, preserve Fathom's vendored license and fetch/copy the applicable
license texts and notices for bundled dependencies. Review the native visualizer
and browser distribution under their actual component boundaries; changing a
package metadata field does not remove an upstream dependency's obligations.
Verify assets and training inputs separately if adding new ones.

Python training dependencies and the optional external Bullet checkout have
their own terms. Installing them is distinct from incorporating them in a
redistributed binary. This list is not a full transitive SBOM; use the exact
lockfile/build inputs when producing a distribution inventory.
