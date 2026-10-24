#include "cores/attacks.h"
#include "cores/zobrist.h"
#include "search/search.h"
#include "search/syzygy.h"
#include "uci/uci_util.h"

#include <iostream>
#include <memory>
#include <stdexcept>
#include <string>

namespace {
void require(bool value, const char *message) {
  if (!value)
    throw std::runtime_error(message);
}

Core::Move find_move(Core::Position &pos, const std::string &uci) {
  Core::MoveList legal;
  Core::generate_legal_moves(pos, legal);
  for (Core::Move m : legal)
    if (UCI::move_to_uci(m) == uci)
      return m;
  throw std::runtime_error("illegal test move: " + uci);
}

void restriction_test(const std::string &path) {
  require(Search::Syzygy::init(path) >= 3, "three-piece tables not loaded");
  Core::Position pos;
  require(pos.setFromFEN("7k/8/5KQ1/8/8/8/8/8 w - - 0 1"), "bad KQvK FEN");
  require(Search::Syzygy::probe_wdl(pos) == Search::Syzygy::Wdl::WIN,
          "KQvK WDL did not return win");
  Core::MoveList legal;
  Core::generate_legal_moves(pos, legal);
  for (Core::Move m : legal) {
    Core::MoveList only, out;
    only.push_back(m);
    require(Search::Syzygy::probe_root_moves(pos, only, out) == 1 &&
                out[0] == m,
            "real tablebase escaped a singleton root restriction");
  }
  const auto drawing = find_move(pos, "g6g8");
  for (int threads : {1, 2}) {
    auto search = std::make_unique<Search::EngineSearch>(1);
    search->set_threads(threads);
    Search::Limits limits;
    limits.maxDepth = 3;
    limits.searchMoves.push_back(drawing);
    uint64_t hits = 0;
    Search::Callbacks callbacks;
    callbacks.onInfo = [&](const Search::IterInfo &info) {
      hits = info.tbHits;
      require(info.pvLen && info.pv[0] == drawing,
              "real-table PV escaped searchmoves");
    };
    const auto result = search->search(pos, limits, callbacks);
    require(result.bestMove == drawing && hits > 0,
            "real-table searchmoves restriction or root probe failed");
  }
  require(pos.setFromFEN("7k/8/5KQ1/8/8/8/8/8 w - - 99 1"),
          "bad fifty-move fixture");
  Core::generate_legal_moves(pos, legal);
  Core::MoveList nearDraw;
  const auto mate = find_move(pos, "g6g7");
  require(Search::Syzygy::probe_root_moves(pos, legal, nearDraw) == 1 &&
              nearDraw[0] == mate,
          "DTZ near the fifty-move boundary did not preserve mate");
}

void repetition_test() {
  Core::Position pos;
  require(pos.setFromFEN("7k/8/5KQ1/8/8/8/8/8 w - - 0 1"), "bad cycle FEN");
  for (const char *uci : {"g6g5", "h8h7", "g5g6", "h7h8", "g6e4", "h8g8"}) {
    const auto m = find_move(pos, uci);
    Core::UndoInfo undo{};
    pos.make_move(m, undo);
  }
  require(pos.has_repeated() && !pos.is_repetition(),
          "fixture did not retain an earlier cycle");
  Core::Position noHistory;
  require(noHistory.setFromFEN(pos.toFEN()), "bad fresh root");
  Core::MoveList legal, repeated, fresh;
  Core::generate_legal_moves(pos, legal);
  require(Search::Syzygy::probe_root_moves(pos, legal, repeated) > 0,
          "repeated DTZ root probe failed");
  require(Search::Syzygy::probe_root_moves(noHistory, legal, fresh) >
              repeated.size(),
          "DTZ did not prefer progress after an earlier cycle");
}
} // namespace

int main(int argc, char **argv) {
  Core::Attacks::init();
  Core::Zobrist::init();
  try {
    require(argc == 2, "pass a directory with three-piece WDL and DTZ files");
    restriction_test(argv[1]);
    repetition_test();
    Search::Syzygy::shutdown();
    std::cout << "PASS: real Syzygy restrictions, DTZ fifty-move and history\n";
  } catch (const std::exception &error) {
    Search::Syzygy::shutdown();
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
