#include "syzygy.h"

#include "../cores/bitboard.h"

// Fathom's public header (extern "C" internally). Its own quoted includes
// (tbconfig.h) resolve via the third_party/fathom include directory added in
// CMake.
#include "tbprobe.h"

#include <cstdint>
#include <limits>
#include <memory>

namespace Search::Syzygy {
namespace {

// Fathom wants the en-passant target square index, or 0 for "none". Square 0
// (a1) is never a legal ep target, so the mapping is unambiguous.
unsigned ep_for_fathom(const Core::Position &pos) {
  const Core::Square ep = pos.ep_square();
  return ep == Core::SQ_NONE ? 0u : static_cast<unsigned>(ep);
}

// Fathom cannot probe positions with castling rights; any rights make it
// return FAILED. We only need "zero vs non-zero", so collapse to a flag.
unsigned castling_for_fathom(const Core::Position &pos) {
  return pos.castling_rights() != 0 ? 0xFu : 0u;
}

Wdl wdl_of(unsigned raw) {
  switch (raw) {
  case TB_WIN:
    return Wdl::WIN;
  case TB_LOSS:
    return Wdl::LOSS;
  default: // DRAW, CURSED_WIN, BLESSED_LOSS -> a draw under the 50-move rule
    return Wdl::DRAW;
  }
}

// Find the legal move matching Fathom's (from, to, promotion) triple, so
// castling and en passant carry the correct flags. Move::none() if no match.
Core::Move match_legal(const Core::MoveList &legal, unsigned from, unsigned to,
                       unsigned promo) {
  for (int i = 0; i < legal.size(); ++i) {
    const Core::Move m = legal[i];
    if (static_cast<unsigned>(m.from_sq()) != from ||
        static_cast<unsigned>(m.to_sq()) != to)
      continue;
    if (promo == TB_PROMOTES_NONE) {
      if (!m.is_promotion())
        return m;
      continue;
    }
    const Core::PieceType want = promo == TB_PROMOTES_QUEEN    ? Core::QUEEN
                                 : promo == TB_PROMOTES_ROOK   ? Core::ROOK
                                 : promo == TB_PROMOTES_BISHOP ? Core::BISHOP
                                                               : Core::KNIGHT;
    if (m.is_promotion() && m.promotion_type() == want)
      return m;
  }
  return Core::Move::none();
}

} // namespace

int init(const std::string &path) {
  tb_free();
  if (path.empty() || !tb_init(path.c_str()))
    return 0;
  return static_cast<int>(TB_LARGEST);
}

void shutdown() { tb_free(); }

int max_pieces() { return static_cast<int>(TB_LARGEST); }

bool active() { return TB_LARGEST > 0; }

Wdl probe_wdl(const Core::Position &pos) {
  const unsigned res = tb_probe_wdl(
      pos.pieces(Core::WHITE), pos.pieces(Core::BLACK), pos.pieces(Core::KING),
      pos.pieces(Core::QUEEN), pos.pieces(Core::ROOK), pos.pieces(Core::BISHOP),
      pos.pieces(Core::KNIGHT), pos.pieces(Core::PAWN),
      static_cast<unsigned>(pos.halfmove_clock()), castling_for_fathom(pos),
      ep_for_fathom(pos), pos.side_to_move() == Core::WHITE);
  return res == TB_RESULT_FAILED ? Wdl::FAIL : wdl_of(res);
}

int probe_root_moves(const Core::Position &pos,
                     const Core::MoveList &candidates, Core::MoveList &out) {
  // TbRootMoves is large (~100 KB); keep it off the stack.
  auto results = std::make_unique<TbRootMoves>();
  const uint64_t white = pos.pieces(Core::WHITE);
  const uint64_t black = pos.pieces(Core::BLACK);
  const uint64_t kings = pos.pieces(Core::KING);
  const uint64_t queens = pos.pieces(Core::QUEEN);
  const uint64_t rooks = pos.pieces(Core::ROOK);
  const uint64_t bishops = pos.pieces(Core::BISHOP);
  const uint64_t knights = pos.pieces(Core::KNIGHT);
  const uint64_t pawns = pos.pieces(Core::PAWN);
  const unsigned rule50 = static_cast<unsigned>(pos.halfmove_clock());
  const unsigned castling = castling_for_fathom(pos);
  const unsigned ep = ep_for_fathom(pos);
  const bool turn = pos.side_to_move() == Core::WHITE;

  // DTZ ranking accounts for the 50-move rule; fall back to WDL ranking when
  // the DTZ tables are incomplete.
  int ok =
      tb_probe_root_dtz(white, black, kings, queens, rooks, bishops, knights,
                        pawns, rule50, castling, ep, turn, pos.has_repeated(),
                        /*useRule50=*/true, results.get());
  if (!ok)
    ok = tb_probe_root_wdl(white, black, kings, queens, rooks, bishops, knights,
                           pawns, rule50, castling, ep, turn,
                           /*useRule50=*/true, results.get());
  if (!ok || results->size == 0)
    return 0;

  int32_t bestRank = std::numeric_limits<int32_t>::min();
  Core::MoveList ranked;
  for (unsigned i = 0; i < results->size; ++i) {
    const TbMove tm = results->moves[i].move;
    const Core::Move m = match_legal(candidates, TB_MOVE_FROM(tm),
                                     TB_MOVE_TO(tm), TB_MOVE_PROMOTES(tm));
    if (!m.is_ok() || results->moves[i].tbRank < bestRank)
      continue;
    if (results->moves[i].tbRank > bestRank) {
      bestRank = results->moves[i].tbRank;
      ranked.clear();
    }
    ranked.push_back(m);
  }
  for (Core::Move m : ranked)
    out.push_back(m);
  return ranked.size();
}

} // namespace Search::Syzygy
