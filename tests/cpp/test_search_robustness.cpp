#include "cores/attacks.h"
#include "cores/movegen.h"
#include "cores/zobrist.h"
#include "nnue/accumulator_stack.h"
#include "search/search.h"
#include "uci/uci_util.h"

#include <atomic>
#include <iostream>
#include <memory>
#include <random>
#include <stdexcept>
#include <thread>
#include <vector>

namespace {
void require(bool value, const char *message) {
  if (!value)
    throw std::runtime_error(message);
}

void tt_test() {
  Search::TranspositionTable table(1);
  std::atomic<bool> failed{false};
  std::vector<std::thread> workers;
  for (int worker = 0; worker < 8; ++worker) {
    workers.emplace_back([&, worker] {
      for (int i = 1; i <= 30000; ++i) {
        const uint64_t key = (uint64_t(worker + 1) << 32) | 17;
        table.store(key, i, Core::Move::none(), i % 255, Search::BOUND_EXACT, 0,
                    i % 30000);
        Search::TTEntry entry;
        if (table.probe(key, entry) && (entry.key32 != uint32_t(worker + 1) ||
                                        entry.depth != entry.score % 255 ||
                                        entry.eval != entry.score % 30000 ||
                                        entry.bound() != Search::BOUND_EXACT))
          failed.store(true);
      }
    });
  }
  for (auto &worker : workers)
    worker.join();
  require(!failed.load(), "TT returned a mixed concurrent snapshot");
}

void accumulator_test() {
  auto net = std::make_unique<NNUE::SmallNetwork>();
  net->randomize(777);
  auto cache = std::make_unique<NNUE::SmallRefreshTable>();
  NNUE::AccumulatorStackT<128> stack;
  stack.resize(Search::MAX_PLY + 2);
  const char *fens[] = {
      "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
      "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1",
      "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", "Rr2k3/P7/8/8/8/8/8/4K3 w - - 0 1"};
  for (const char *fen : fens) {
    Core::Position pos;
    require(pos.setFromFEN(fen), "bad accumulator fixture FEN");
    stack.reset(pos, *net, true);
    auto compare = [&](int ply) {
      NNUE::SmallAccumulator full;
      net->refresh(pos, full);
      const auto &lazy = stack.resolve(pos, ply, *net, *cache);
      require(lazy.acc == full.acc && lazy.psqt == full.psqt,
              "deferred accumulator differs from full refresh");
    };
    std::vector<Core::Move> moves;
    std::vector<Core::UndoInfo> undos;
    std::mt19937 rng(42);
    for (int ply = 0; ply < 90; ++ply) {
      Core::MoveList legal;
      Core::generate_legal_moves(pos, legal);
      if (!legal.size())
        break;
      auto move = legal[rng() % legal.size()];
      // Prioritize special moves when the fixture makes them available.
      for (int i = 0; i < legal.size(); ++i)
        if (legal[i].is_castling() || legal[i].is_en_passant() ||
            legal[i].is_promotion()) {
          move = legal[i];
          break;
        }
      Core::UndoInfo undo{};
      pos.make_move(move, undo);
      stack.push(ply, pos, move, undo, *net, cache.get());
      moves.push_back(move);
      undos.push_back(undo);
      if (ply % 7 == 6)
        compare(ply + 1);
    }
    compare(int(moves.size()));
    while (!moves.empty()) {
      pos.unmake_move(moves.back(), undos.back());
      moves.pop_back();
      undos.pop_back();
      compare(int(moves.size()));
      if (!pos.in_check()) {
        Core::UndoInfo nullUndo{};
        pos.make_null_move(nullUndo);
        stack.push_null(int(moves.size()));
        compare(int(moves.size()) + 1);
        pos.unmake_null_move(nullUndo);
      }
    }
    compare(0);
    for (int ply = 0; ply < Search::MAX_PLY; ++ply) {
      Core::UndoInfo undo{};
      pos.make_null_move(undo);
      stack.push_null(ply);
    }
    compare(Search::MAX_PLY);
  }
}
} // namespace

int main() {
  Core::Attacks::init();
  Core::Zobrist::init();
  try {
    require(Search::MAX_PLY == Search::MoveOrdering::MAX_PLY &&
                Search::Limits{}.maxDepth < Search::MAX_PLY,
            "search limits have no selective-depth headroom");
    tt_test();
    accumulator_test();
    std::cout << "PASS: coherent TT snapshots, search limits and deferred "
                 "accumulators\n";
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
