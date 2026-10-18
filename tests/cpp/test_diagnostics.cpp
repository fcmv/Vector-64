#include "cores/attacks.h"
#include "cores/movegen.h"
#include "cores/position.h"
#include "cores/zobrist.h"
#include "datagen/selfplay.h"
#include "perfts.h"
#include "uci/uci_util.h"

#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <set>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using namespace Core;

namespace {
constexpr const char *START =
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

void require(bool value, const char *message) {
  if (!value)
    throw std::runtime_error(message);
}

Move find_move(Position &pos, const std::string &uci) {
  MoveList moves;
  generate_legal_moves(pos, moves);
  for (int i = 0; i < moves.size(); ++i) {
    if (UCI::move_to_uci(moves[i]) == uci)
      return moves[i];
  }
  throw std::runtime_error("fixture move is not legal: " + uci);
}

void divide_test() {
  Position pos;
  require(pos.setFromFEN(START), "start FEN failed");
  const uint64_t originalHash = pos.hash();
  const std::string originalFen = pos.toFEN();
  std::ostringstream out;
  require(perft_divide(pos, 3, out) == 8902, "wrong divide total");
  require(pos.hash() == originalHash && pos.toFEN() == originalFen,
          "divide changed position state");
  const std::map<std::string, uint64_t> expected = {
      {"a2a3", 380}, {"a2a4", 420}, {"b2b3", 420}, {"b2b4", 421},
      {"c2c3", 420}, {"c2c4", 441}, {"d2d3", 539}, {"d2d4", 560},
      {"e2e3", 599}, {"e2e4", 600}, {"f2f3", 380}, {"f2f4", 401},
      {"g2g3", 420}, {"g2g4", 421}, {"h2h3", 380}, {"h2h4", 420},
      {"b1a3", 400}, {"b1c3", 440}, {"g1f3", 440}, {"g1h3", 400}};
  std::istringstream lines(out.str());
  std::map<std::string, uint64_t> actual;
  std::string move;
  uint64_t count = 0;
  while (lines >> move >> count) {
    if (move == "Total:") {
      require(count == 8902, "wrong printed total");
      continue;
    }
    require(move.back() == ':', "invalid divide move format");
    move.pop_back();
    require(actual.emplace(move, count).second, "duplicate divide root move");
  }
  require(actual == expected, "divide root counts differ from reference");
  out.str("");
  require(perft_divide(pos, 0, out) == 1 && out.str() == "Total: 1\n",
          "divide depth zero is incorrect");
  bool negativeRejected = false;
  try {
    perft_divide(pos, -1, out);
  } catch (const std::invalid_argument &) {
    negativeRejected = true;
  }
  require(negativeRejected, "negative divide depth accepted");
  require(pos.setFromFEN("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
          "stalemate FEN failed");
  out.str("");
  require(perft_divide(pos, 2, out) == 0 && out.str() == "Total: 0\n",
          "terminal divide is incorrect");
  require(pos.setFromFEN("1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
          "promotion FEN failed");
  out.str("");
  perft_divide(pos, 1, out);
  for (char suffix : std::string("qrbn")) {
    require(out.str().find(std::string("a7b8") + suffix + ": 1\n") !=
                std::string::npos,
            "divide omitted capture underpromotion suffix");
  }
}

void capture_test() {
  struct Case {
    const char *fen;
    std::set<std::string> moves;
  };
  const std::vector<Case> cases = {
      {START, {}},
      {"4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 17", {"e5d6"}},
      {"k3r3/8/8/3pP3/8/8/8/4K3 w - d6 0 17", {}},
      {"1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1",
       {"a7b8q", "a7b8r", "a7b8b", "a7b8n"}},
      {"4k3/8/8/8/8/8/p7/1R2K3 b - - 0 1",
       {"a2b1q", "a2b1r", "a2b1b", "a2b1n"}},
      {"4k3/8/8/8/8/4r3/4p3/4K3 w - - 0 1", {}},
      {"4k3/8/8/8/8/8/4r3/4K3 w - - 0 1", {"e1e2"}},
      {"k3r3/8/8/8/8/3pR3/8/4K3 w - - 0 1", {"e3e8"}}};
  for (const auto &test : cases) {
    Position pos;
    require(pos.setFromFEN(test.fen), "capture FEN failed");
    const auto hash = pos.hash();
    MoveList captures;
    generate_legal_captures(pos, captures);
    std::set<std::string> actual;
    for (int i = 0; i < captures.size(); ++i) {
      require(captures[i].is_capture(),
              "capture generator returned quiet promotion");
      actual.insert(UCI::move_to_uci(captures[i]));
    }
    if (actual != test.moves ||
        static_cast<int>(actual.size()) != captures.size())
      throw std::runtime_error(std::string("wrong captures for ") + test.fen);
    require(pos.hash() == hash && pos.toFEN() == test.fen,
            "capture generation changed state");
  }
}

void clock_test() {
  for (int initial : {1, 17, 2048}) {
    Position pos;
    require(pos.setFromFEN(
                std::string(START).substr(0, std::string(START).size() - 1) +
                std::to_string(initial)),
            "clock FEN failed");
    require(pos.fullmove_number() == initial, "parsed clock differs from FEN");
    require(pos.hand_size(WHITE) == 0 && pos.hand_size(BLACK) == 0,
            "standard chess has reserves");
    const Move white = find_move(pos, "e2e4");
    UndoInfo first{}, second{};
    pos.make_move(white, first);
    require(pos.fullmove_number() == initial,
            "white move advanced fullmove number");
    const Move black = find_move(pos, "e7e5");
    pos.make_move(black, second);
    require(pos.fullmove_number() == initial + 1,
            "black move failed to advance fullmove number");
    pos.unmake_move(black, second);
    require(pos.fullmove_number() == initial,
            "black unmake failed to restore clock");
    pos.unmake_move(white, first);
    require(pos.fullmove_number() == initial, "white unmake changed clock");
    const std::string before = pos.toFEN();
    UndoInfo nullUndo{};
    pos.make_null_move(nullUndo);
    require(pos.fullmove_number() == initial,
            "search null move advanced clock");
    pos.unmake_null_move(nullUndo);
    require(pos.toFEN() == before, "null unmake failed to restore FEN");
  }
}

void shard_test(const std::filesystem::path &dir) {
  std::filesystem::create_directories(dir);
  require(std::filesystem::is_empty(dir), "shard test directory must be empty");
  struct Cleanup {
    std::filesystem::path directory;
    ~Cleanup() {
      std::error_code error;
      for (const char *name :
           {"shard_0000.txt", "shard_0001.txt", "shard_0002.txt"})
        std::filesystem::remove(directory / name, error);
      std::filesystem::remove(directory, error);
    }
  } cleanup{dir};
  Datagen::ShardWriter writer;
  require(writer.open(dir.string(), 2, false), "cannot open shard writer");
  require(writer.shard() == 0 && writer.rows_in_shard() == 0,
          "wrong initial shard state");
  require(writer.write_row("first") && writer.rows_in_shard() == 1,
          "wrong first row count");
  require(writer.write_row("second") && writer.shard() == 1 &&
              writer.rows_in_shard() == 0,
          "full shard did not roll over");
  require(writer.write_row("third") && writer.rows_in_shard() == 1,
          "wrong second shard count");
  writer.close();
  require(writer.open(dir.string(), 2, true), "cannot resume partial shard");
  require(writer.shard() == 1 && writer.rows_in_shard() == 1,
          "resume forgot partial row count");
  require(writer.write_row("fourth") && writer.shard() == 2 &&
              writer.rows_in_shard() == 0,
          "resumed shard boundary incorrect");
  writer.close();
  require(writer.open(dir.string(), 2, true),
          "cannot resume at exact boundary");
  require(writer.shard() == 2 && writer.rows_in_shard() == 0,
          "exact boundary created a gap");
  writer.close();
  const auto emptyShard = dir / "shard_0002.txt";
  require(std::filesystem::exists(emptyShard), "rollover omitted next shard");
  std::filesystem::remove(emptyShard);
  require(writer.open(dir.string(), 2, true), "cannot resume full last shard");
  require(writer.shard() == 2 && writer.rows_in_shard() == 0,
          "full last shard grew past its cap");
  writer.close();
  for (const auto &[name, expected] : std::map<std::string, std::string>{
           {"shard_0000.txt", "first\nsecond\n"},
           {"shard_0001.txt", "third\nfourth\n"}}) {
    std::ifstream input(dir / name, std::ios::binary);
    std::ostringstream contents;
    contents << input.rdbuf();
    require(contents.str() == expected,
            "resume changed completed shard content");
  }
}
} // namespace

int main(int argc, char **argv) {
  Attacks::init();
  Zobrist::init();
  try {
    const std::string group = argc > 1 ? argv[1] : "";
    if (group == "divide")
      divide_test();
    else if (group == "captures")
      capture_test();
    else if (group == "clocks")
      clock_test();
    else if (group == "shards" && argc == 3)
      shard_test(argv[2]);
    else
      return 2;
    std::cout << "PASS: " << group << '\n';
    return 0;
  } catch (const std::exception &error) {
    std::cerr << "FAIL: " << error.what() << '\n';
    return 1;
  }
}
