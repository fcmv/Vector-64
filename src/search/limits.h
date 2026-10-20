#ifndef SEARCH_LIMITS_H
#define SEARCH_LIMITS_H

namespace Search {

constexpr int MAX_PLY = 256;
// Extensions and quiescence need room beyond the nominal iteration depth.
constexpr int MAX_DEPTH = MAX_PLY - 10;
static_assert(MAX_DEPTH > 0 && MAX_DEPTH <= 255);

} // namespace Search

#endif
