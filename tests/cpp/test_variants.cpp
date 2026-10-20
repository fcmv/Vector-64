// FEN reconstruction independently checks reserves and promoted-piece marks
// as well as board state.
//
// From startpos, captures can begin at ply three and drops at ply five.
// Crazyhouse must match chess through depth four and exceed it at depth five.
#include "cores/attacks.h"
#include "cores/material.h"
#include "cores/movegen.h"
#include "cores/position.h"
#include "cores/zobrist.h"
#include "perft/perft.h"
#include "search/search.h"
#include "uci/validator.h"
#include <memory>

#include <cstdio>
#include <random>
#include <string>
#include <vector>

using namespace Core;

namespace {

constexpr const char *DROP_STARTPOS =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[] w KQkq - 0 1";

// Bughouse reserves are fed by the partner board, which this engine cannot
// see, so captures here add nothing to either hand. A bughouse run therefore
// has to start from an injected reserve or it would never see a drop.
constexpr const char *BUGHOUSE_STOCKED =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR[QRBNPqrbnp] w KQkq - 0 1";

int failures = 0;

void fail(const char *what, const std::string &fen) {
  std::printf("FAIL: %s\n  %s\n", what, fen.c_str());
  ++failures;
}

bool check_against_rebuild(const Position &pos, Variant v) {
  Position rebuilt;
  rebuilt.set_variant(v);
  const std::string fen = pos.toFEN();
  if (!rebuilt.setFromFEN(fen)) {
    fail("toFEN/setFromFEN round trip failed", fen);
    return false;
  }
  if (rebuilt.hash() != pos.hash()) {
    fail("incremental hash drifted from rebuild", fen);
    return false;
  }
  if (rebuilt.material_wb() != pos.material_wb() ||
      rebuilt.psqt_wb() != pos.psqt_wb()) {
    fail("incremental material/psqt drifted", fen);
    return false;
  }
  if (rebuilt.hand_material_wb() != pos.hand_material_wb()) {
    fail("incremental reserve material drifted", fen);
    return false;
  }
  if (rebuilt.promoted_pieces() != pos.promoted_pieces()) {
    fail("promoted-piece mask drifted", fen);
    return false;
  }
  for (int c = WHITE; c <= BLACK; ++c) {
    int expectedHand = 0;
    for (int pt = PAWN; pt <= QUEEN; ++pt) {
      const Color col = static_cast<Color>(c);
      const PieceType type = static_cast<PieceType>(pt);
      if (rebuilt.in_hand(col, type) != pos.in_hand(col, type)) {
        fail("reserve count drifted", fen);
        return false;
      }
      expectedHand += rebuilt.in_hand(col, type);
    }
    if (pos.hand_size(static_cast<Color>(c)) != expectedHand ||
        rebuilt.hand_size(static_cast<Color>(c)) != expectedHand) {
      fail("total hand count disagrees with piece counts", fen);
      return false;
    }
  }
  return true;
}

bool list_contains(const MoveList &list, Move m) {
  for (int i = 0; i < list.size(); ++i) {
    if (list[i] == m)
      return true;
  }
  return false;
}

// A false pseudo-legal drop can decrement an empty reserve and corrupt state.
bool check_movegen(Position &pos, std::mt19937_64 &rng) {
  MoveList full;
  generate_legal_moves(pos, full);

  MoveList legalCaptures;
  generate_legal_captures(pos, legalCaptures);
  int expectedCaptures = 0;
  for (int i = 0; i < full.size(); ++i) {
    if (full[i].is_capture()) {
      ++expectedCaptures;
      if (!list_contains(legalCaptures, full[i])) {
        fail("capture generator missed a legal variant capture", pos.toFEN());
        return false;
      }
    }
  }
  if (legalCaptures.size() != expectedCaptures) {
    fail("capture generator included a drop or quiet move", pos.toFEN());
    return false;
  }

  MoveList captures;
  MoveList quiets;
  generate_pseudo_captures(pos, captures);
  generate_pseudo_quiets(pos, quiets);
  const NodeLegality nl = make_node_legality(pos);

  MoveList staged;
  for (int i = 0; i < captures.size(); ++i) {
    if (is_legal(nl, captures[i]))
      staged.push_back(captures[i]);
  }
  for (int i = 0; i < quiets.size(); ++i) {
    if (is_legal(nl, quiets[i]))
      staged.push_back(quiets[i]);
  }

  if (staged.size() != full.size()) {
    fail("staged generators disagree with generate_legal_moves", pos.toFEN());
    return false;
  }
  for (int i = 0; i < full.size(); ++i) {
    if (!list_contains(staged, full[i])) {
      fail("staged set is missing a legal move", pos.toFEN());
      return false;
    }
    if (!is_pseudo_legal(pos, full[i])) {
      fail("is_pseudo_legal rejects a legal move", pos.toFEN());
      return false;
    }
  }

  MoveList pseudoAll;
  generate_pseudo_legal_moves(pos, pseudoAll);
  for (int k = 0; k < 256; ++k) {
    const Move m(static_cast<uint16_t>(rng()));
    if (is_pseudo_legal(pos, m) && !list_contains(pseudoAll, m)) {
      fail("is_pseudo_legal accepts a move the generators never produce",
           pos.toFEN());
      return false;
    }
  }
  return true;
}

bool check_drop_shape(const Position &pos, Move m) {
  if (!m.is_drop())
    return true;
  if (m.is_capture() || m.is_promotion() || m.is_en_passant() ||
      m.is_castling() || m.is_double_push()) {
    fail("drop carries a conflicting move flag", pos.toFEN());
    return false;
  }
  const PieceType pt = m.dropped_piece();
  if (pt < PAWN || pt > QUEEN) {
    fail("drop names an undroppable piece type", pos.toFEN());
    return false;
  }
  if (pos.in_hand(pos.side_to_move(), pt) == 0) {
    fail("drop from an empty reserve", pos.toFEN());
    return false;
  }
  if (pos.occupancy() & square_bb(m.to_sq())) {
    fail("drop onto an occupied square", pos.toFEN());
    return false;
  }
  if (pt == PAWN && (square_bb(m.to_sq()) & (RANK_1_BB | RANK_8_BB))) {
    fail("pawn dropped onto a back rank", pos.toFEN());
    return false;
  }
  return true;
}

// Brute-force played drops provide an independent oracle for the checking-drop
// generator.
bool check_drop_check_generator(Position &pos) {
  if (!pos.has_drops() || !pos.has_any_in_hand(pos.side_to_move()))
    return true;

  MoveList all;
  generate_legal_moves(pos, all);
  MoveList expected;
  for (int i = 0; i < all.size(); ++i) {
    if (!all[i].is_drop())
      continue;
    UndoInfo u{};
    pos.make_move(all[i], u);
    const bool givesCheck = pos.in_check();
    pos.unmake_move(all[i], u);
    if (givesCheck)
      expected.push_back(all[i]);
  }

  MoveList generated;
  generate_drop_checks(pos, generated);
  const NodeLegality nl = make_node_legality(pos);
  MoveList got;
  for (int i = 0; i < generated.size(); ++i) {
    if (is_legal(nl, generated[i]))
      got.push_back(generated[i]);
  }

  if (got.size() != expected.size()) {
    fail("drop-check generator produced the wrong number of checking drops",
         pos.toFEN());
    return false;
  }
  for (int i = 0; i < expected.size(); ++i) {
    if (!list_contains(got, expected[i])) {
      fail("drop-check generator missed a checking drop", pos.toFEN());
      return false;
    }
  }
  return true;
}

int total_in_hand(const Position &pos) {
  int n = 0;
  for (int c = WHITE; c <= BLACK; ++c)
    for (int pt = PAWN; pt <= QUEEN; ++pt)
      n += pos.in_hand(static_cast<Color>(c), static_cast<PieceType>(pt));
  return n;
}

bool run_games(Variant v, const char *label, const char *startFen, int games,
               int maxPlies) {
  std::mt19937_64 rng(0xD40D5ULL + static_cast<uint64_t>(v));
  uint64_t dropsPlayed = 0;
  uint64_t promotedCaptures = 0;

  for (int game = 0; game < games; ++game) {
    Position pos;
    pos.set_variant(v);
    if (!pos.setFromFEN(startFen)) {
      fail("variant start position did not parse", startFen);
      return false;
    }

    for (int ply = 0; ply < maxPlies; ++ply) {
      MoveList moves;
      generate_legal_moves(pos, moves);
      if (moves.size() == 0)
        break;

      if (!check_movegen(pos, rng))
        return false;
      if (!check_drop_check_generator(pos))
        return false;

      const Move move =
          moves[static_cast<int>(rng() % static_cast<uint64_t>(moves.size()))];
      if (!check_drop_shape(pos, move))
        return false;
      if (move.is_drop())
        ++dropsPlayed;
      if (move.is_capture() &&
          (pos.promoted_pieces() & square_bb(move.to_sq())))
        ++promotedCaptures;

      const uint64_t hashBefore = pos.hash();
      const std::string fenBefore = pos.toFEN();
      const int matBefore = pos.material_wb();
      const int psqtBefore = pos.psqt_wb();
      const int handMatBefore = pos.hand_material_wb();
      const int handBefore = total_in_hand(pos);
      const int fullmoveBefore = pos.fullmove_number();
      const Color mover = pos.side_to_move();

      const uint64_t predicted = pos.key_after(move);

      UndoInfo undo{};
      pos.make_move(move, undo);

      if (pos.fullmove_number() != fullmoveBefore + (mover == BLACK)) {
        fail("variant fullmove clock advanced incorrectly", pos.toFEN());
        return false;
      }

      if (pos.opponent_in_check()) {
        std::printf("FAIL: move left the mover's king in check "
                    "(drop=%d pt=%d to=%d cap=%d)\n  before: %s\n  after:  "
                    "%s\n",
                    int(move.is_drop()), int(move.dropped_piece()),
                    int(move.to_sq()), int(move.is_capture()),
                    fenBefore.c_str(), pos.toFEN().c_str());
        ++failures;
        return false;
      }

      if (pos.hash() != predicted) {
        fail("key_after != post-move hash", pos.toFEN());
        return false;
      }
      if (!check_against_rebuild(pos, v))
        return false;

      if (!pos.captures_fill_hand() && move.is_capture() &&
          total_in_hand(pos) != handBefore) {
        fail("bughouse capture changed a reserve on this board", fenBefore);
        return false;
      }

      pos.unmake_move(move, undo);
      if (pos.hash() != hashBefore || pos.material_wb() != matBefore ||
          pos.psqt_wb() != psqtBefore ||
          pos.hand_material_wb() != handMatBefore || pos.toFEN() != fenBefore) {
        fail("unmake did not restore state exactly", fenBefore);
        return false;
      }

      pos.make_move(move, undo);
    }
  }

  // A run that never exercised a drop would pass every check above while
  // testing nothing that matters here.
  if (dropsPlayed == 0) {
    std::printf("FAIL: %s games never played a drop\n", label);
    ++failures;
    return false;
  }
  std::printf("PASS: %s -- %d games, %llu drops, %llu promoted-piece captures, "
              "state matches rebuild throughout\n",
              label, games, static_cast<unsigned long long>(dropsPlayed),
              static_cast<unsigned long long>(promotedCaptures));
  return true;
}

constexpr uint64_t STANDARD_PERFT[6] = {1, 20, 400, 8902, 197281, 4865609};

bool run_perft_anchors() {
  // crazyhouse must reproduce standard chess exactly.
  for (int depth = 1; depth <= 4; ++depth) {
    Position pos;
    pos.set_variant(VARIANT_CRAZYHOUSE);
    pos.setFromFEN(DROP_STARTPOS);
    const uint64_t got = perft(pos, depth);
    if (got != STANDARD_PERFT[depth]) {
      std::printf("FAIL: crazyhouse perft(%d) = %llu, expected %llu "
                  "(no drop is legal this shallow, so it must match chess)\n",
                  depth, static_cast<unsigned long long>(got),
                  static_cast<unsigned long long>(STANDARD_PERFT[depth]));
      ++failures;
      return false;
    }
  }
  std::printf(
      "PASS: crazyhouse perft matches standard chess through depth 4\n");

  Position pos;
  pos.set_variant(VARIANT_CRAZYHOUSE);
  pos.setFromFEN(DROP_STARTPOS);
  const uint64_t d5 = perft(pos, 5);
  if (d5 <= STANDARD_PERFT[5]) {
    std::printf("FAIL: crazyhouse perft(5) = %llu, must exceed chess's %llu "
                "once drops become legal\n",
                static_cast<unsigned long long>(d5),
                static_cast<unsigned long long>(STANDARD_PERFT[5]));
    ++failures;
    return false;
  }
  std::printf("PASS: crazyhouse perft(5) = %llu (chess %llu, +%llu drop "
              "continuations)\n",
              static_cast<unsigned long long>(d5),
              static_cast<unsigned long long>(STANDARD_PERFT[5]),
              static_cast<unsigned long long>(d5 - STANDARD_PERFT[5]));
  return true;
}

// silently loading the board and dropping the hand on the floor.
bool check_fen_isolation() {
  Position std_;
  if (std_.setFromFEN(DROP_STARTPOS)) {
    fail("standard Position accepted a bracketed variant FEN", DROP_STARTPOS);
    return false;
  }
  std::printf("PASS: standard mode rejects a bracketed variant FEN\n");
  return true;
}

bool expect_terminal(const char *fen, Variant v, const char *want,
                     const char *what) {
  Position pos;
  pos.set_variant(v);
  if (!pos.setFromFEN(fen)) {
    fail("terminal case FEN did not parse", fen);
    return false;
  }
  const std::string got = UCI::Validator::terminal_state(pos);
  if (got != want) {
    std::printf("FAIL: %s -- terminal is '%s', expected '%s'\n  %s\n", what,
                got.c_str(), want, fen);
    ++failures;
    return false;
  }
  return true;
}

bool run_validator_checks() {
  if (!expect_terminal("rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w "
                       "KQkq - 1 3",
                       VARIANT_STANDARD, "checkmate", "fool's mate"))
    return false;
  if (!expect_terminal("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", VARIANT_STANDARD,
                       "stalemate", "stalemate"))
    return false;
  if (!expect_terminal("8/8/4k3/8/8/4KB2/8/8 w - - 0 1", VARIANT_STANDARD,
                       "draw_insufficient_material", "K+B vs K"))
    return false;
  if (!expect_terminal("8/8/4k3/8/8/4K3/8/6R1 w - - 100 60", VARIANT_STANDARD,
                       "draw_fifty_move", "fifty-move"))
    return false;

  {
    Position pos;
    pos.setFromFEN("8/8/4k3/8/8/4KB2/8/8 w - - 0 1");
    if (can_side_mate(pos, WHITE) || can_side_mate(pos, BLACK)) {
      fail("K+B vs K reported as able to mate", pos.toFEN());
      return false;
    }
    pos.setFromFEN("8/8/4k3/8/8/4KBN1/8/8 w - - 0 1");
    if (!can_side_mate(pos, WHITE) || can_side_mate(pos, BLACK)) {
      fail("K+B+N vs K mating material misreported", pos.toFEN());
      return false;
    }
  }

  // In a drop variant a reserve alone is sufficient: the bare king below can
  // still be mated by a dropped piece.
  {
    Position pos;
    pos.set_variant(VARIANT_CRAZYHOUSE);
    pos.setFromFEN("8/8/4k3/8/8/4K3/8/8[Q] w - - 0 1");
    if (!can_side_mate(pos, WHITE)) {
      fail("reserve piece not counted as mating material", pos.toFEN());
      return false;
    }
    if (can_side_mate(pos, BLACK)) {
      fail("empty-reserve bare king reported as able to mate", pos.toFEN());
      return false;
    }
  }

  // queen enters a reserve as a pawn, not as a queen.
  {
    Position pos;
    pos.set_variant(VARIANT_CRAZYHOUSE);
    if (!pos.setFromFEN("3Q~3k/8/8/8/8/K7/8/3r4[] b - - 0 1")) {
      fail("promoted-piece FEN did not parse", "3Q~3k/8/8/8/8/K7/8/3r4[]");
      return false;
    }
    MoveList legal;
    generate_legal_moves(pos, legal);
    Move capture = Move::none();
    for (int i = 0; i < legal.size(); ++i) {
      if (legal[i].to_sq() == SQ_D8 && legal[i].is_capture())
        capture = legal[i];
    }
    if (!capture.is_ok()) {
      fail("no capture of the promoted queen was generated", pos.toFEN());
      return false;
    }
    UndoInfo undo{};
    pos.make_move(capture, undo);
    const PieceType dropType = Position::captured_drop_type(capture, undo);
    if (dropType != PAWN) {
      std::printf("FAIL: captured promoted queen reports drop type %d, "
                  "expected PAWN (%d)\n",
                  int(dropType), int(PAWN));
      ++failures;
      return false;
    }
    if (pos.in_hand(BLACK, PAWN) != 1 || pos.in_hand(BLACK, QUEEN) != 0) {
      fail("promoted queen entered the reserve as a queen", pos.toFEN());
      return false;
    }
  }

  // and the host can force the standard rules back on.
  {
    Position pos;
    pos.set_variant(VARIANT_BUGHOUSE);
    pos.setFromFEN("8/8/4k3/8/8/4K3/8/6R1[] w - - 100 60");
    if (pos.standard_draws()) {
      fail("bughouse defaulted to standard draw rules", pos.toFEN());
      return false;
    }
    if (std::string(UCI::Validator::terminal_state(pos)) != "none") {
      fail("bughouse scored a fifty-move draw", pos.toFEN());
      return false;
    }
    pos.set_standard_draws(true);
    if (std::string(UCI::Validator::terminal_state(pos)) != "draw_fifty_move") {
      fail("forced standard draws did not restore the fifty-move draw",
           pos.toFEN());
      return false;
    }
  }

  // back to the start position must reach a repetition count of 2.
  {
    Position pos;
    pos.setFromFEN("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1");
    const char *shuffle[] = {"g1f3", "g8f6", "f3g1", "f6g8",
                             "g1f3", "g8f6", "f3g1", "f6g8"};
    std::vector<UndoInfo> undos;
    for (const char *uci : shuffle) {
      MoveList legal;
      generate_legal_moves(pos, legal);
      Move chosen = Move::none();
      for (int i = 0; i < legal.size(); ++i) {
        if (UCI::move_to_uci(legal[i]) == uci)
          chosen = legal[i];
      }
      if (!chosen.is_ok()) {
        fail(std::string("shuffle move not legal: ").append(uci).c_str(),
             pos.toFEN());
        return false;
      }
      undos.emplace_back();
      pos.make_move(chosen, undos.back());
    }
    if (pos.repetition_count() < 2) {
      std::printf("FAIL: repetition_count() is %d after a threefold shuffle, "
                  "expected at least 2\n",
                  pos.repetition_count());
      ++failures;
      return false;
    }
  }

  std::printf("PASS: validator -- terminal states, mating material, "
              "capturedDropType promotion revert, draw-rule policy, "
              "threefold counting\n");
  return true;
}

} // namespace

int main(int argc, char **argv) {
  Attacks::init();
  Zobrist::init();

  if (argc == 2) {
    auto search = std::make_unique<Search::EngineSearch>(8);
    Position pos;
    pos.set_variant(VARIANT_CRAZYHOUSE);
    if (!pos.setFromFEN("7k/8/8/8/8/8/8/K7[Q] w - - 0 1")) {
      std::printf("FAIL: evaluation-policy FEN rejected\n");
      return 1;
    }
    search->set_nnue_enabled(false);
    const int classical = search->evaluate(pos);
    if (classical < 500 || !search->load_nnue(argv[1])) {
      std::printf("FAIL: evaluation-policy baseline=%d, net=%s\n", classical,
                  argv[1]);
      return 1;
    }
    search->set_nnue_enabled(true);
    if (search->evaluate(pos) != classical) {
      std::printf("FAIL: loaded net changed variant static evaluation\n");
      return 1;
    }
    search->set_threads(2);
    Search::Limits limits;
    limits.maxDepth = 3;
    limits.maxNodes = 20000;
    for (const auto variant : {VARIANT_CRAZYHOUSE, VARIANT_BUGHOUSE}) {
      pos.set_variant(variant);
      search->clear();
      const auto result = search->search(pos, limits, {});
      if (!result.bestMove.is_ok() || result.scoreCp < 500) {
        std::printf("FAIL: variant=%d SMP score=%d depth=%d nodes=%llu\n",
                    int(variant), result.scoreCp, result.completedDepth,
                    (unsigned long long)result.nodes);
        return 1;
      }
    }
    Position standard;
    if (!standard.setFromFEN(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
      return 1;
    if (search->evaluate(standard) != search->evaluator().evaluate(standard)) {
      std::printf("FAIL: standard chess did not restore NNUE evaluation\n");
      return 1;
    }
    search->clear();
    const auto result = search->search(standard, limits, {});
    MoveList legal;
    generate_legal_moves(standard, legal);
    if (!list_contains(legal, result.bestMove) || result.nodes == 0) {
      std::printf("FAIL: standard SMP search did not return a legal result\n");
      return 1;
    }
    return 0;
  }

  if (!check_fen_isolation())
    return 1;
  if (!run_perft_anchors())
    return 1;
  if (!run_validator_checks())
    return 1;
  if (!run_games(VARIANT_CRAZYHOUSE, "crazyhouse", DROP_STARTPOS, 150, 120))
    return 1;
  if (!run_games(VARIANT_BUGHOUSE, "bughouse", BUGHOUSE_STOCKED, 150, 120))
    return 1;

  return failures == 0 ? 0 : 1;
}
