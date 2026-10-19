# Compile variant state and branches into a separate core library so the
# standard binaries retain their position layout and 256-entry move buffers.
option(ENGINE_VARIANTS "Build ChessEngine-variants (crazyhouse + bughouse)" ON)
# Plies of quiescence that generate checking drops. Kept a compile-time knob
# (not a UCI option) so an SPRT compares two binaries built from the same
# source rather than one binary in two modes -- see tools/sprt_dropchecks.ps1.
#
# Default 0 (off), and that is a measured result, not a guess. Crazyhouse SPRT
# at 25k nodes, H0 elo<=0 / H1 elo>=5:
#   qdepth 2 vs 0: -20.8 Elo +/- 12.4 over 3014 games, H0 accepted
#   qdepth 4 vs 2: -146.6 Elo +/- 36.0 over 429 games, H0 accepted
# Monotonic in depth, which points at node cost rather than bad tactics: every
# checking drop hands the opponent a full set of evasions, so the qsearch tree
# grows fast and a fixed node budget buys less real depth than the extra
# tactics are worth.
#
# With reserve material enabled, qdepth 2 vs 0 still lost:
# -21.4 Elo +/- 12.5 over 2960 games, H0 accepted, LLR -2.96.
set(ENGINE_DROP_CHECK_QDEPTH "0" CACHE STRING
        "Quiescence plies that generate checking drops (0 = off)")

# Count reserve material in the evaluation. 0 reproduces the original
# behaviour, in which a piece in hand was worth nothing while the same piece on
# the board was worth PieceValue, so a drop appeared to win a full piece out of
# nowhere. Only ever set to 0 to re-measure the fix.
#
# Crazyhouse SPRT at 25k nodes, H0 elo<=0 / H1 elo>=5:
#   ON vs OFF: +502 Elo over 57 games (+54 =0 -3), H1 accepted, LLR +3.65
# The error bar is unbounded at that score, so read the verdict rather than
# the point estimate -- but the direction is not in doubt.
set(ENGINE_VARIANT_HAND_MATERIAL "1" CACHE STRING
        "Count reserve material in the evaluation (0 = off, pre-fix behaviour)")

# Per-piece centipawn values of a reserve, as a C initialiser list indexed by
# PieceType. Empty means "same as PieceValue", which makes a drop exactly
# material-neutral and leaves the piece-square table to judge the destination.
set(ENGINE_HAND_VALUES "" CACHE STRING
        "Reserve piece values, e.g. 0,110,330,330,480,860,0 (empty = PieceValue)")

# Scale of the drop king-danger term, in eighths of (empty king-ring squares x
# opponent reserve power). 0 disables it.
#
# Crazyhouse SPRT at 25k nodes, each against the term off:
#   scale  6: + 9.5 Elo +/- 8.7 over 6000 games, LLR +1.76, cap reached
#   scale 14: +10.5 Elo +/- 8.9 over 5830 games, LLR +1.96, cap reached
# Consistently positive and weight-insensitive in that range, but neither
# reached the SPRT bound alone. 6 is the value validated jointly with the
# piece values below (+25.2 Elo +/- 12.3 over 3061 games, H1 accepted).
set(ENGINE_KING_DANGER_SCALE "6" CACHE STRING
        "Drop king-danger weight in eighths (0 = off)")

# Board piece values used by the drop-variant evaluation, as a C initialiser
# list indexed by PieceType. Empty means "same as PieceValue". Applied as a
# correction inside the variant evaluation, not by retuning PieceValue, which
# also drives materialWb and see() and would move standard chess inside
# ChessEngine-all.
#
# Crazyhouse SPRT at 25k nodes, 0,100,340,320,450,800,0 vs the chess values:
#   +30.6 Elo +/- 13.6 over 2512 games, H1 accepted, LLR +2.98
# Knights outrank bishops and the majors lose ground against minors, which is
# the usual crazyhouse ordering. Set equal to PieceValue to disable.
set(ENGINE_PIECE_VALUES "0,100,340,320,450,800,0" CACHE STRING
        "Variant board piece values (set equal to PieceValue to disable)")

# The zugzwang guard ignores reserves, so null-move pruning is independently
# switchable for drop variants. Crazyhouse at 25k nodes, reserve material on:
# OFF vs ON: -16.1 Elo +/- 10.9 over 3850 games, H0 accepted, LLR -3.00.
# Keep it on; re-test for longer time controls or a variant-trained evaluation.
set(ENGINE_VARIANT_NULLMOVE "1" CACHE STRING
        "Allow null-move pruning in drop variants (0 = off)")

# Dedicated [color][droppedPiece][to] history for drops. The main history
# table is keyed [from][to], which a drop has no valid key for, so without this
# the largest class of quiet moves in the position is ordered by continuation
# history alone.
#
# Crazyhouse SPRT at 25k nodes on top of reserve material:
#   ON vs OFF: +51.3 Elo +/- 18.2 over 1406 games, H1 accepted, LLR +2.94
set(ENGINE_VARIANT_DROP_HISTORY "1" CACHE STRING
        "Keep a drop-specific history table (0 = off)")

if(ENGINE_VARIANTS)
        add_library(chess_core_variants STATIC ${CORE_SOURCES} ${CORE_HEADERS})
        set_source_files_properties(third_party/fathom/tbprobe.c PROPERTIES LANGUAGE CXX)
        target_compile_definitions(chess_core_variants PUBLIC ENGINE_VARIANTS
                ENGINE_DROP_CHECK_QDEPTH=${ENGINE_DROP_CHECK_QDEPTH}
                ENGINE_VARIANT_HAND_MATERIAL=${ENGINE_VARIANT_HAND_MATERIAL}
                ENGINE_KING_DANGER_SCALE=${ENGINE_KING_DANGER_SCALE}
                ENGINE_VARIANT_NULLMOVE=${ENGINE_VARIANT_NULLMOVE}
                ENGINE_VARIANT_DROP_HISTORY=${ENGINE_VARIANT_DROP_HISTORY})
        if(ENGINE_HAND_VALUES)
                target_compile_definitions(chess_core_variants PUBLIC
                        ENGINE_HAND_VALUES=${ENGINE_HAND_VALUES})
        endif()
        if(ENGINE_PIECE_VALUES)
                target_compile_definitions(chess_core_variants PUBLIC
                        ENGINE_PIECE_VALUES=${ENGINE_PIECE_VALUES})
        endif()
        target_include_directories(chess_core_variants PUBLIC src)
        target_include_directories(chess_core_variants PRIVATE third_party/fathom)

        add_executable(ChessEngine-variants
                app/main.cpp
        )
        target_link_libraries(ChessEngine-variants chess_core_variants)
        set_target_properties(ChessEngine-variants PROPERTIES
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
        # Validator workers need neither a net nor search; keep startup cheap for resident pools.
        add_executable(ChessEngine-validator
                app/main.cpp
        )
        target_compile_definitions(ChessEngine-validator PRIVATE STK_VALIDATOR_ONLY)
        target_link_libraries(ChessEngine-validator chess_core_variants)
        set_target_properties(ChessEngine-validator PROPERTIES
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

        message(STATUS "Variant binary: ChessEngine-variants (crazyhouse, bughouse)")
        message(STATUS "Validator binary: ChessEngine-validator (no search, no net)")
endif()
