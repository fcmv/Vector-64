#ifndef VIZ_SERVER_H
#define VIZ_SERVER_H

#include "session.h"

#include <string>

namespace Viz {

struct ServerOptions {
  std::string host = "127.0.0.1"; // loopback only; see run_server()
  int port = 7777;
  bool openBrowser = true;
};

// Serve the visualizer UI and stream `session` state over HTTP.
//
// Endpoints:
//   GET  /                     the embedded single-file UI
//   GET  /api/state?since=N    long-poll; framed binary state (see wire.h)
//   GET  /api/net              net inspector data (JSON)
//   POST /api/control          control commands (JSON)
//   GET  /api/health           liveness probe
//
// Unauthenticated engine control is loopback-only; non-loopback hosts are
// rejected.
//
// Blocks until the server stops. Returns 0 on clean shutdown.
int run_server(Session &session, const ServerOptions &opts);

} // namespace Viz

#endif
