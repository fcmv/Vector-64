# Glossary

| Term | Meaning in this project |
|---|---|
| UCI | Line-oriented protocol through which a GUI controls an engine process. |
| FEN | Board state, mover, castling, en passant, and clocks; not a complete move history. |
| EPD | Position-oriented test input; this repository uses it for reference perft counts. |
| Perft | Count of legal move-tree leaves to a specified depth, without ordinary search pruning. |
| Divide | Perft counts separated by legal root move. |
| Bitboard | A 64-bit square mask; a1 is bit 0. |
| Zobrist hash | Incrementally updated position identity used by TT/repetition logic. |
| TT | Transposition table storing search results/bounds, moves and static evaluation. |
| PV | Principal variation: the current best line reported by a search. |
| MultiPV | Search/report multiple root lines. |
| Quiescence | Tactical continuation after the nominal search frontier. |
| SEE | Static exchange evaluation used in ordering/pruning; current variant model is reserve-incomplete. |
| Lazy SMP | Parallel searches sharing TT/weights while retaining per-worker search state. |
| NNUE | Efficiently updated neural evaluation using sparse feature changes. |
| STK-HalfKA | This engine's 22,528-feature-per-perspective encoding and associated fixed integer network contract. |
| FT | Feature transformer from active sparse features to each perspective's accumulator. |
| Accumulator | Incrementally maintained sum of active feature weights plus bias. |
| PSQT | Piece-square evaluation; distinguish classical PSQT from the network's integrated side output. |
| Side to move / stm | The player who moves next; network/search scores are relative to that side. |
| Output bucket | One of eight dense heads selected by piece count. |
| Reserve / hand | Pieces available for drops in crazyhouse or host-managed bughouse. |
| Promoted marker | `~` on a variant FEN piece, needed for capture-to-pawn reversion. |
| SPRT / LLR | Sequential strength test and log-likelihood ratio; a game cap can leave it inconclusive. |
| WDL / DTZ | Tablebase win/draw/loss and distance-to-zeroing information. |
| Fingerprint | Deterministic bench count for a specified search/net configuration; not an Elo score. |
| Integer parity | Exact agreement of quantized inference paths, distinct from float prediction quality. |
| COOP/COEP | Browser isolation policies enabling SharedArrayBuffer for pthread WASM. |
