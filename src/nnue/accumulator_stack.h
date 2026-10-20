#ifndef NNUE_ACCUMULATOR_STACK_H
#define NNUE_ACCUMULATOR_STACK_H

#include "network.h"
#include <vector>

namespace NNUE {

template <int H> class AccumulatorStackT {
public:
  void resize(size_t count) {
    values_.resize(count);
    ready_.resize(count);
    dirty_.resize(count);
    null_.resize(count);
  }

  void reset(const Core::Position &root, const NetworkT<H> &net,
             bool deferred) {
    deferred_ = deferred;
    for (auto &ready : ready_)
      ready = {false, false};
    if (!deferred_) {
      net.refresh(root, values_[0]);
      ready_[0] = {true, true};
    }
  }

  void push(int ply, const Core::Position &after, Core::Move move,
            const Core::UndoInfo &undo, const NetworkT<H> &net,
            RefreshTableT<H> *cache) {
    if (deferred_) {
      dirty_[ply + 1] = net.make_dirty(after, move, undo);
      null_[ply + 1] = false;
      ready_[ply + 1] = {false, false};
    } else {
      net.update(values_[ply], values_[ply + 1], after, move, undo, cache);
      ready_[ply + 1] = {true, true};
    }
  }

  void push_null(int ply) {
    if (deferred_) {
      null_[ply + 1] = true;
      ready_[ply + 1] = {false, false};
    } else {
      values_[ply + 1] = values_[ply];
      ready_[ply + 1] = {true, true};
    }
  }

  const AccumulatorT<H> &resolve(const Core::Position &pos, int ply,
                                 const NetworkT<H> &net,
                                 RefreshTableT<H> &cache) {
    if (!deferred_)
      return values_[ply];
    for (int pc = Core::WHITE; pc <= Core::BLACK; ++pc) {
      if (ready_[ply][pc])
        continue;
      const auto persp = Core::Color(pc);
      int base = ply;
      while (base > 0 && !ready_[base][pc] &&
             (null_[base] || !dirty_[base].kingMoved ||
              dirty_[base].mover != persp))
        --base;
      if (!ready_[base][pc]) {
        // A king barrier invalidates earlier deltas for this perspective.
        STK_PROF_T0();
        net.refresh_perspective(pos, persp, values_[ply], cache);
        STK_PROF_END(updKingCyc, updKing);
        ready_[ply][pc] = true;
        continue;
      }
      const auto king = Core::lsb(pos.pieces(Core::KING, persp));
      for (int next = base + 1; next <= ply; ++next) {
        if (null_[next]) {
          values_[next].acc[pc] = values_[next - 1].acc[pc];
          values_[next].psqt[pc] = values_[next - 1].psqt[pc];
        } else {
          STK_PROF_T0();
          net.apply_dirty_fused(persp, king, dirty_[next], values_[next - 1],
                                values_[next]);
          STK_PROF_END(updIncrCyc, updIncr);
        }
        ready_[next][pc] = true;
      }
    }
    return values_[ply];
  }

private:
  std::vector<AccumulatorT<H>> values_;
  std::vector<std::array<bool, 2>> ready_;
  std::vector<DirtyMove> dirty_;
  std::vector<bool> null_;
  bool deferred_ = false;
};

using AccumulatorStack = AccumulatorStackT<1024>;

} // namespace NNUE
#endif
