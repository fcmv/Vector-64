// Reuse the native wire encoder and control handler so the browser transport
// has the same contract. Built by tools/build_wasm.sh under Emscripten.
#ifdef __EMSCRIPTEN__

#include "../cores/attacks.h"
#include "../cores/zobrist.h"
#include "session.h"
#include "wire.h"

#include <emscripten/emscripten.h>

#include <memory>
#include <string>

namespace {

std::unique_ptr<Viz::Session> g_session;
// Keeps the most recently encoded frame alive while JS copies it out.
std::string g_state;
std::string g_control;

} // namespace

extern "C" {

EMSCRIPTEN_KEEPALIVE
void stk_viz_init(int nodes, int threads, int hashMb, int delayMs, int seed) {
  Core::Attacks::init();
  Core::Zobrist::init();
  Viz::Config cfg;
  cfg.nodes = nodes > 0 ? nodes : 20000;
  cfg.threads = threads > 0 ? threads : 1;
  cfg.hashMb = hashMb > 0 ? hashMb : 32;
  cfg.moveDelayMs = delayMs >= 0 ? delayMs : 300;
  cfg.seed = static_cast<uint64_t>(seed);
  g_session = std::make_unique<Viz::Session>(cfg);
}

// JS supplies the same H=1024 net used by native builds.
EMSCRIPTEN_KEEPALIVE
int stk_viz_load_net(const unsigned char *data, int size) {
  if (!g_session || !data || size <= 0)
    return 0;
  return g_session->load_net_buffer(data, static_cast<std::size_t>(size)) ? 1
                                                                          : 0;
}

EMSCRIPTEN_KEEPALIVE
void stk_viz_start() {
  if (g_session)
    g_session->start();
}

EMSCRIPTEN_KEEPALIVE
void stk_viz_stop() {
  if (g_session)
    g_session->stop();
}

// Current publish sequence: JS polls this cheaply and only re-encodes when it
// moves, mirroring the long-poll behaviour of the native transport.
EMSCRIPTEN_KEEPALIVE
double stk_viz_seq() {
  return g_session ? static_cast<double>(g_session->snapshot().seq) : 0.0;
}

EMSCRIPTEN_KEEPALIVE
int stk_viz_encode_state() {
  if (!g_session) {
    g_state.clear();
    return 0;
  }
  g_state = Viz::encode_state(g_session->snapshot());
  return static_cast<int>(g_state.size());
}

EMSCRIPTEN_KEEPALIVE
const char *stk_viz_state_ptr() { return g_state.data(); }

// Returns the JSON response; `okOut` receives 1 on success, 0 on rejection.
EMSCRIPTEN_KEEPALIVE
const char *stk_viz_control(const char *json, int *okOut) {
  if (!g_session || !json) {
    g_control = "{\"ok\":false,\"error\":\"no session\"}";
    if (okOut)
      *okOut = 0;
    return g_control.c_str();
  }
  int status = 200;
  g_control = Viz::handle_control(*g_session, std::string(json), status);
  if (okOut)
    *okOut = status == 200 ? 1 : 0;
  return g_control.c_str();
}

EMSCRIPTEN_KEEPALIVE
const char *stk_viz_net_info() {
  if (!g_session) {
    g_control = "{\"loaded\":false}";
    return g_control.c_str();
  }
  g_control =
      Viz::encode_net_info(g_session->net(), g_session->snapshot().nnueActive);
  return g_control.c_str();
}
}

#endif
