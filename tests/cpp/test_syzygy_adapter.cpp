#include "cores/attacks.h"
#include "cores/zobrist.h"
#include "search/search.h"
#include "search/syzygy.h"
#include "tbprobe.h"
#include "uci/uci_util.h"

#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>
#include <vector>

namespace {
struct RankedMove {
  Core::Move move;
  int rank;
};
std::vector<RankedMove> answers;
bool dtzSucceeds = true;
bool wdlSucceeds = true;
bool sawRepeated = false;
int wdlCalls = 0;

void require(bool value, const char *message) {
  if (!value)
    throw std::runtime_error(message);
}

Core::Move find_move(const Core::Position &pos, const std::string &uci) {
  Core::MoveList legal;
  Core::Position copy = pos;
  Core::generate_legal_moves(copy, legal);
  for (Core::Move m : legal)
    if (UCI::move_to_uci(m) == uci)
      return m;
  throw std::runtime_error("illegal test move: " + uci);
}

void play(Core::Position &pos, const char *uci) {
  Core::UndoInfo undo{};
  pos.make_move(find_move(pos, uci), undo);
}

void history_test() {
  Core::Position pos;
  require(pos.setFromFEN(
              "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
          "bad history FEN");
  require(!pos.has_repeated(), "new game has repetition history");
  play(pos, "g1f3");
  play(pos, "g8f6");
  play(pos, "f3g1");
  require(!pos.has_repeated(), "unfinished cycle marked repeated");
  play(pos, "f6g8");
  require(pos.is_repetition() && pos.has_repeated(), "missed root repetition");
  play(pos, "b1c3");
  require(!pos.is_repetition() && pos.has_repeated(),
          "missed an earlier repetition with a fresh root");
  Core::Position restored;
  require(restored.setFromFEN(pos.toFEN()), "bad history roundtrip");
  require(!restored.has_repeated(), "FEN invented repetition history");
  const Core::Move pawn = find_move(pos, "e7e5");
  Core::UndoInfo undo{};
  pos.make_move(pawn, undo);
  require(!pos.has_repeated(), "pawn move retained old repetition window");
  pos.unmake_move(pawn, undo);
  require(pos.has_repeated(), "undo lost the earlier repetition");

  answers = {{find_move(pos, "g8f6"), 1000}};
  Core::MoveList legal, out;
  Core::generate_legal_moves(pos, legal);
  require(Search::Syzygy::probe_root_moves(pos, legal, out) == 1 && sawRepeated,
          "DTZ did not receive earlier repetition history");
  out.clear();
  require(Search::Syzygy::probe_root_moves(restored, legal, out) == 1 &&
              !sawRepeated,
          "DTZ invented history for a FEN root");
}

void restriction_test() {
  Core::Position pos;
  require(pos.setFromFEN("7k/8/5KQ1/8/8/8/8/8 w - - 0 1"), "bad root FEN");
  const auto globalBest = find_move(pos, "g6g7");
  const auto allowedBest = find_move(pos, "g6g8");
  const auto allowedOther = find_move(pos, "f6e6");
  answers = {{globalBest, 1000}, {allowedOther, 800}, {allowedBest, 900}};
  Core::MoveList candidates, out;
  candidates.push_back(allowedOther);
  candidates.push_back(allowedBest);
  require(Search::Syzygy::probe_root_moves(pos, candidates, out) == 1 &&
              out[0] == allowedBest,
          "DTZ ranked outside restricted candidates");
  answers[1].rank = 900;
  out.clear();
  require(Search::Syzygy::probe_root_moves(pos, candidates, out) == 2,
          "DTZ discarded an equally ranked candidate");
  require(out[0] == allowedOther && out[1] == allowedBest,
          "DTZ returned an unrequested move");

  dtzSucceeds = false;
  out.clear();
  wdlCalls = 0;
  require(Search::Syzygy::probe_root_moves(pos, candidates, out) == 2 &&
              wdlCalls == 1,
          "WDL fallback lost the candidate restriction");
  wdlSucceeds = false;
  out.clear();
  out.push_back(allowedBest);
  require(Search::Syzygy::probe_root_moves(pos, candidates, out) == 0 &&
              out.size() == 1 && out[0] == allowedBest,
          "failed tablebase probe changed the caller's moves");
  dtzSucceeds = wdlSucceeds = true;

  auto search = std::make_unique<Search::EngineSearch>(1);
  Search::Limits limits;
  limits.searchMoves.push_back(allowedOther);
  limits.maxDepth = 1;
  Search::Callbacks callbacks;
  callbacks.shouldStop = [] { return true; };
  const auto result = search->search(pos, limits, callbacks);
  require(result.bestMove == allowedOther,
          "search replaced searchmoves during root tablebase ranking");
}

void promotion_test() {
  Core::Position pos;
  require(pos.setFromFEN("7k/P7/6K1/8/8/8/8/8 w - - 0 1"), "bad promotion FEN");
  const auto queen = find_move(pos, "a7a8q");
  const auto knight = find_move(pos, "a7a8n");
  answers = {{queen, 1000}, {knight, 0}};
  Core::MoveList candidates, out;
  candidates.push_back(knight);
  require(Search::Syzygy::probe_root_moves(pos, candidates, out) == 1 &&
              out[0] == knight,
          "root restriction lost underpromotion identity");
}

void fill_results(TbRootMoves *results) {
  results->size = static_cast<unsigned>(answers.size());
  for (unsigned i = 0; i < results->size; ++i) {
    const auto m = answers[i].move;
    const unsigned promo =
        !m.is_promotion()                    ? TB_PROMOTES_NONE
        : m.promotion_type() == Core::QUEEN  ? TB_PROMOTES_QUEEN
        : m.promotion_type() == Core::ROOK   ? TB_PROMOTES_ROOK
        : m.promotion_type() == Core::BISHOP ? TB_PROMOTES_BISHOP
                                             : TB_PROMOTES_KNIGHT;
    results->moves[i].move = static_cast<TbMove>(
        unsigned(m.to_sq()) | (unsigned(m.from_sq()) << 6) | (promo << 12));
    results->moves[i].tbRank = answers[i].rank;
  }
}
} // namespace

extern "C" {
unsigned TB_LARGEST = 3;
bool tb_init(const char *) { return true; }
void tb_free() {}
unsigned tb_probe_wdl_impl(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t,
                           uint64_t, uint64_t, uint64_t, unsigned, bool) {
  return TB_RESULT_FAILED;
}
int tb_probe_root_dtz(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t,
                      uint64_t, uint64_t, uint64_t, unsigned, unsigned,
                      unsigned, bool, bool repeated, bool useRule50,
                      TbRootMoves *results) {
  require(useRule50, "DTZ disabled the fifty-move rule");
  sawRepeated = repeated;
  if (dtzSucceeds)
    fill_results(results);
  return dtzSucceeds;
}
int tb_probe_root_wdl(uint64_t, uint64_t, uint64_t, uint64_t, uint64_t,
                      uint64_t, uint64_t, uint64_t, unsigned, unsigned,
                      unsigned, bool, bool useRule50, TbRootMoves *results) {
  require(useRule50, "WDL disabled the fifty-move rule");
  ++wdlCalls;
  if (wdlSucceeds)
    fill_results(results);
  return wdlSucceeds;
}
}

int main() {
  Core::Attacks::init();
  Core::Zobrist::init();
  try {
    history_test();
    restriction_test();
    promotion_test();
    std::cout << "PASS: Syzygy history, restricted ranking and fallback\n";
  } catch (const std::exception &error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
