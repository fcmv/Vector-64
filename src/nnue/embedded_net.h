#ifndef NNUE_EMBEDDED_NET_H
#define NNUE_EMBEDDED_NET_H

#include <cstddef>

// NNUE, all and viz targets share the embedded image; the classical target
// never references it. Accessors use .incbin labels or MSVC RCDATA.
namespace NNUE {

const unsigned char *embedded_net_data();
std::size_t embedded_net_size();

} // namespace NNUE

#endif
