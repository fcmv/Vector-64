#ifndef VIZ_SESSION_H
#define VIZ_SESSION_H

#include "../datagen/selfplay.h"
#include "../search/search.h"
#include "probe.h"

#include <atomic>
#include <condition_variable>
#include <cstdint>
#include <fstream>
#include <mutex>
#include <random>
#include <string>
#include <thread>
#include <utility>
#include <vector>

// Publish immutable snapshots so transports read a coherent position and
// telemetry.
namespace Viz {

enum class Mode { SelfPlay, Analysis, Human, Datagen };

// Shared selfplay helpers keep rows compatible with CLI datagen. The node cap
// bounds the depth-limited search, rather than replacing it.
struct DatagenConfig {
  // Dataset directory containing shard_0000.txt, shard_0001.txt, ...
  std::string out = "data/selfplay";
  int64_t targetPositions = 500000000;
  // Optional second stop condition: finish after this many games even if the
  // position target is not reached. 0 = no game cap, positions decide. The CLI
  // is games-driven (--games), a dataset is positions-driven, so both are here
  // and whichever is reached first ends the run.
  int64_t targetGames = 0;
  int nodes = 5000;
  int depth = 9;      // 0 = node-limited only
  int skipPlies = 12; // opening plies to leave unlabelled
  int maxPlies = 200;
  int openingPlies = 8;
  int balance = 150;
  // Root-move variety, as in Config -- Stockfish's random-multi-pv. Random
  // openings alone leave every game after ply openingPlies deterministic, so
  // the same opening always produces the same game.
  int varietyCp = 30;
  int varietyPlies = 16;
  // Rows per shard. ~5M rows is ~400 MB of text, so a 500M run lands around a
  // hundred shards -- small enough to copy or convert one at a time. 0 writes
  // a single file at `out` instead.
  int64_t shardPositions = 5000000;
  double lam = 0.5;
  bool raw = true; // raw = fen|eval|wdl (bullet-native); false = fen|blended cp
  uint64_t seed = 12345;
};

struct DatagenState {
  bool running = false;
  std::string out;
  int64_t positions = 0;
  int64_t games = 0;
  int64_t target = 0;
  int64_t targetGames = 0;
  int wins = 0, draws = 0, losses = 0;
  double positionsPerSec = 0.0;
  double etaMinutes = 0.0;
  bool resumable = false;
  int64_t resumablePositions = 0;
  int shard = 0;
  std::string shardPath;
  // Resume restores these row-shaping settings instead of the caller's values.
  bool hasConfig = false;
  DatagenConfig config;
};

// Random-opening length when one is requested but the config asks for none
// (self-play defaults to starting from the real initial position).
inline constexpr int kDefaultOpeningPlies = 8;

const char *mode_name(Mode m);
bool mode_from_name(const std::string &s, Mode &out);

struct Config {
  int nodes = 20000; // per-move node budget (0 = depth-limited only)
  int depth = 0;     // 0 = no depth cap
  int hashMb = 32;
  int threads = 1;
  int moveDelayMs = 300;
  // 0 means no preference: the first game uses startpos, later games use
  // kDefaultOpeningPlies. A nonzero value pins the opening length.
  int openingPlies = 0;
  int balance = 150;
  int maxPlies = 300;
  uint64_t seed = 0;
  int l1TopK = 12;
  // Human mode clock, per side. The engine also keeps thinking on the
  // opponent's time (see ponder handling in human_step).
  int clockMs = 300000; // 5 minutes
  // Core search defaults to single-PV; the visualizer requests four candidates.
  int multiPv = 4;
  // 0 always picks best. Otherwise variety needs multiPv > 1 and applies only
  // for varietyPlies, choosing scored moves within this many centipawns of
  // best.
  int varietyCp = 30;
  // Only the opening is varied. Past this the engine plays its best move, so a
  // sharp middlegame or endgame is never thrown away for the sake of variety.
  int varietyPlies = 16;
};

struct Candidate {
  std::string move;
  int scoreCp = 0;
  std::vector<std::string> pv;
};

struct SearchInfo {
  int depth = 0;
  int seldepth = 0;
  int scoreCp = 0;
  uint64_t nodes = 0;
  uint64_t tbHits = 0;
  int elapsedMs = 0;
  int nps = 0;
  std::vector<std::string> pv;
  double qsearchTtHitRate = 0.0;
  double negamaxTtHitRate = 0.0;
  std::vector<Candidate> candidates;
};

struct GameState {
  std::string fen;
  std::vector<std::string> moves; // long algebraic, from the game's start
  std::string startFen;
  std::string lastMove;
  int ply = 0;
  bool over = false;
  std::string result; // "1-0" | "0-1" | "1/2-1/2" | ""
  std::string reason; // checkmate | stalemate | repetition | fifty | material |
                      // maxplies
  int gameIndex = 0;
  int wins = 0, draws = 0, losses = 0; // session tally, white perspective
  // Human-mode clocks, milliseconds remaining.
  int whiteMs = 0;
  int blackMs = 0;
  bool clockRunning = false;
};

// One coherent view of the session. `seq` increments on every publish so a
// client can tell whether anything changed.
struct Snapshot {
  uint64_t seq = 0;
  Mode mode = Mode::SelfPlay;
  bool running = false;
  bool paused = false;
  bool thinking = false;
  bool nnueActive = false;
  int threads = 1;
  int varietyCp = 0;
  int engineColor = 1; // Human mode: the colour the engine plays (Core::Color)
  GameState game;
  SearchInfo search;
  VizFrame frame;
  bool compareActive = false;
  VizFrame compareFrame;
  std::string compareName;
  std::vector<std::string> legalMoves; // side to move, for Human mode
  DatagenState datagen;
  // Frame recording. Reported so the UI shows what is actually happening
  // rather than what it last asked for -- a recording can be started from the
  // command line too, and a failed open must not look like success.
  bool recording = false;
  std::string recordPath;
  int64_t recordedFrames = 0;
};

class Session {
public:
  explicit Session(Config cfg);
  ~Session();
  Session(const Session &) = delete;
  Session &operator=(const Session &) = delete;

  bool load_net(const std::string &path);
  bool load_net_buffer(const unsigned char *data, std::size_t size);
  // A second net, evaluated on the same positions so two nets can be compared
  // directly. Empty path clears it.
  bool load_compare_net(const std::string &path);

  bool start_recording(const std::string &path);
  void stop_recording();
  bool recording() const;

  void start();
  void stop();

  void set_mode(Mode m);
  void set_paused(bool p);
  void step();
  void set_move_delay(int ms);
  void set_nodes(int nodes);
  // Applied between searches, never during one: set_threads reconfigures lazy
  // SMP and is not safe to change under a running search.
  void set_threads(int n);
  // 0 = no depth cap (node-limited only). Clamped to the engine's ceiling.
  void set_depth(int d);
  // Root-move variety in centipawns; 0 plays the best move always. See
  // Config::varietyCp.
  void set_variety(int cp);
  static int max_depth();
  void new_game();
  // Analysis/Human: set the board. `moves` are long-algebraic from `fen`.
  bool set_position(const std::string &fen,
                    const std::vector<std::string> &moves);
  bool play_move(const std::string &uci);
  void set_engine_color(int color);
  void set_random_opening(bool v);

  // Data generation. start_datagen switches to Datagen mode and begins writing;
  // `resume` continues a previous run's file and counters instead of
  // truncating.
  bool start_datagen(const DatagenConfig &wanted, bool resume);
  void stop_datagen();
  static DatagenState probe_datagen(const std::string &out);

  Snapshot snapshot() const;
  Snapshot wait_for(uint64_t have, int timeoutMs) const;

  // this instead of guessing a maximum.
  static int hardware_threads();

  // The net the engine is using, for the inspector. Weights are immutable once
  // loaded, so this is safe to read while the worker searches.
  const NNUE::Network &net() const { return search_.evaluator().big(); }

private:
  void run();
  void self_play_step();
  void analysis_step();
  void human_step();
  void datagen_step();
  void datagen_write(const std::vector<std::pair<std::string, int>> &rec,
                     double wdl);
  void datagen_save_state();
  // Search the current position, publishing per-iteration telemetry.
  // `ponder` runs one long search instead of a short budgeted one: it is the
  // engine thinking on the opponent's clock and ends when they move.
  // `linesOut`, when given, receives the last iteration's root lines so the
  // caller can pick among near-equal moves (see pick_varied).
  Search::Result think(bool ponder = false,
                       std::vector<Search::RootLine> *linesOut = nullptr);
  void publish_frame(const Core::Position &pos, bool thinking);
  void publish_frame_current();
  void publish();
  void record(const Snapshot &s);
  void apply_move_internal(Core::Move m);
  bool detect_terminal(bool hadLegalMove);
  void reset_game(bool randomOpening);

  Config cfg_;
  Search::EngineSearch search_;

  mutable std::mutex mu_;
  mutable std::condition_variable cv_;
  Snapshot snap_;
  uint64_t seq_ = 0;

  std::thread worker_;
  std::atomic<bool> stop_{false};
  std::atomic<bool> paused_{false};
  std::atomic<bool> stepOnce_{false};
  std::atomic<bool> abortSearch_{false};
  std::atomic<int> moveDelayMs_{300};
  std::atomic<int> nodes_{20000};
  std::atomic<int> threads_{1};
  std::atomic<int> depth_{0};
  std::atomic<int> varietyCp_{0};
  // Rate-limits telemetry during a long ponder so the UI is not flooded.
  std::chrono::steady_clock::time_point lastPublish_{};
  int appliedThreads_ = 1;

  // Board state, touched only by the worker thread except through commands.
  std::mutex cmdMu_;
  Core::Position pos_;
  Core::Position startPos_;
  std::vector<std::string> moves_;
  std::string startFen_;
  std::vector<uint64_t> history_; // for repetition detection
  Mode mode_ = Mode::SelfPlay;
  int engineColor_ = 1;
  int gameIndex_ = 0;
  int wins_ = 0, draws_ = 0, losses_ = 0;
  bool gameOver_ = false;
  std::string result_, reason_;
  uint64_t rngState_ = 0;
  bool pendingReset_ = false;
  bool pendingRandomOpening_ = false;
  bool randomOpening_ = false;
  // Human-mode clocks. Only the side to move burns time.
  int whiteMs_ = 0, blackMs_ = 0;
  std::chrono::steady_clock::time_point turnStart_{};
  bool clockRunning_ = false;
  void tick_clock();
  // Bumped whenever the board changes from outside the worker, so a search
  // whose position was replaced mid-flight discards its result.
  uint64_t boardGen_ = 0;
  bool publish_needed_ = false;
  // Second net for side-by-side comparison, and the recorder.
  std::unique_ptr<NNUE::Network> compareNet_;
  std::string compareName_;
  mutable std::mutex recMu_;
  std::ofstream rec_;
  std::string recPath_;
  int64_t recFrames_ = 0;

  DatagenConfig dgCfg_;
  Datagen::ShardWriter dgOut_;
  std::mutex dgMu_;
  DatagenState dgState_;
  std::chrono::steady_clock::time_point dgStart_{};
  int64_t dgStartPositions_ = 0;
  // Rows for the game in progress; banked when it ends.
  std::vector<std::pair<std::string, int>> dgRecord_;
};

} // namespace Viz

#endif
