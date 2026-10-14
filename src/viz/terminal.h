#ifndef VIZ_TERMINAL_H
#define VIZ_TERMINAL_H

#include "session.h"

namespace Viz {

// Redraws in place and blocks until the session stops.
int run_terminal(Session &session);

} // namespace Viz

#endif
