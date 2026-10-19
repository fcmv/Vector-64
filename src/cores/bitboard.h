#ifndef BITBOARD_H
#define BITBOARD_H

#include "types.h"
#include <bit>
#include <iostream>
#include <string>

#ifdef _MSC_VER
#include <intrin.h>
#endif

namespace Core {

constexpr Bitboard FILE_A_BB = 0x0101010101010101ULL;
constexpr Bitboard FILE_B_BB = FILE_A_BB << 1;
constexpr Bitboard FILE_G_BB = FILE_A_BB << 6;
constexpr Bitboard FILE_H_BB = FILE_A_BB << 7;

constexpr Bitboard RANK_1_BB = 0xFFULL;
constexpr Bitboard RANK_3_BB = RANK_1_BB << 16;
constexpr Bitboard RANK_6_BB = RANK_1_BB << 40;
constexpr Bitboard RANK_8_BB = RANK_1_BB << 56;

inline void set_bit(Bitboard &b, Square s) { b |= (1ULL << s); }

inline bool has_bit(Bitboard b, Square s) { return b & (1ULL << s); }

inline int popcount(Bitboard b) {
#ifdef _MSC_VER
  return (int)__popcnt64(b);
#else
  return __builtin_popcountll(b);
#endif
}

inline Square lsb(Bitboard b) {
#ifdef _MSC_VER
  unsigned long idx;
  _BitScanForward64(&idx, b);
  return (Square)idx;
#else
  return (Square)__builtin_ctzll(b);
#endif
}

inline Square pop_lsb(Bitboard &b) {
  Square s = lsb(b);
  b &= b - 1;
  return s;
}

inline Bitboard square_bb(Square s) { return (1ULL << s); }

template <Direction D> constexpr Bitboard shift(Bitboard b) {
  if constexpr (D == NORTH)
    return b << 8;
  else if constexpr (D == SOUTH)
    return b >> 8;
  else if constexpr (D == EAST)
    return (b & ~FILE_H_BB) << 1;
  else if constexpr (D == WEST)
    return (b & ~FILE_A_BB) >> 1;

  else if constexpr (D == NORTH_EAST)
    return (b & ~FILE_H_BB) << 9;
  else if constexpr (D == NORTH_WEST)
    return (b & ~FILE_A_BB) << 7;
  else if constexpr (D == SOUTH_EAST)
    return (b & ~FILE_H_BB) >> 7;
  else if constexpr (D == SOUTH_WEST)
    return (b & ~FILE_A_BB) >> 9;

  else
    return 0;
}

} // namespace Core

#endif
