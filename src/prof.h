#ifndef STK_PROF_H
#define STK_PROF_H

// ENGINE_PROF adds per-thread counters; normal builds compile these macros
// away. Use tools/profile_nnue.sh for a dedicated profiling build.
#ifdef ENGINE_PROF

#include <chrono>
#include <cstdint>

#if defined(_MSC_VER)
#include <intrin.h>
#elif defined(__x86_64__) || defined(__i386__)
#include <x86intrin.h>
#endif

namespace prof {

// Portable, low-overhead tick counter.
//   x86    : rdtsc (invariant TSC, ~cycle granularity).
//   arm64  : cntvct_el0, the userspace virtual counter. Coarse per read
//            (~24 MHz / ~42 ns on Apple Silicon) but summed over millions of
//            evals it gives an accurate *relative* breakdown, which is all the
//            audit needs.
//   other  : steady_clock nanoseconds.
// Ticks are arch-specific: compare the percentages, never raw ticks across
// machines.
inline uint64_t now() {
#if defined(__aarch64__) && (defined(__GNUC__) || defined(__clang__))
  uint64_t v;
  asm volatile("mrs %0, cntvct_el0" : "=r"(v));
  return v;
#elif (defined(_MSC_VER) && defined(_M_X64)) || defined(__x86_64__) ||         \
    defined(__i386__)
  return __rdtsc();
#else
  return static_cast<uint64_t>(
      std::chrono::steady_clock::now().time_since_epoch().count());
#endif
}

// Per-thread cycle attribution for the NNUE forward + accumulator update.
// thread_local so a multi-threaded datagen run does not race; a 1-thread
// `bench` (the profiling target) puts every eval on the reporting thread.
struct Counters {
  uint64_t pairwiseCyc = 0, l1Cyc = 0, l2Cyc = 0, outCyc = 0;
  uint64_t forwards = 0;
  // King-move refreshes include cached placement diffs and full cache misses.
  uint64_t updIncrCyc = 0, updKingCyc = 0;
  uint64_t updIncr = 0, updKing = 0;
  void reset() {
    pairwiseCyc = l1Cyc = l2Cyc = outCyc = forwards = 0;
    updIncrCyc = updKingCyc = updIncr = updKing = 0;
  }
};
inline thread_local Counters fwd;

} // namespace prof

#define STK_PROF_T0() uint64_t _pt0 = ::prof::now()
#define STK_PROF_LAP(field)                                                    \
  do {                                                                         \
    uint64_t _n = ::prof::now();                                               \
    ::prof::fwd.field += _n - _pt0;                                            \
    _pt0 = _n;                                                                 \
  } while (0)
#define STK_PROF_END(cycfield, cntfield)                                       \
  do {                                                                         \
    ::prof::fwd.cycfield += ::prof::now() - _pt0;                              \
    ++::prof::fwd.cntfield;                                                    \
  } while (0)

#else

#define STK_PROF_T0() ((void)0)
#define STK_PROF_LAP(field) ((void)0)
#define STK_PROF_END(cycfield, cntfield) ((void)0)

#endif
#endif
