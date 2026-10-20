if(ENGINE_VIZ)
    add_executable(test_viz tests/cpp/test_viz.cpp)
    target_link_libraries(test_viz chess_viz)
    set_target_properties(test_viz PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )
endif()

add_executable(test_zobrist tests/cpp/test_zobrist.cpp)
target_link_libraries(test_zobrist chess_core)
set_target_properties(test_zobrist PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)

add_executable(test_diagnostics tests/cpp/test_diagnostics.cpp)
add_executable(test_search_robustness tests/cpp/test_search_robustness.cpp)
target_link_libraries(test_search_robustness chess_core)
set_target_properties(test_search_robustness PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
add_test(NAME "search.robustness" COMMAND test_search_robustness)
target_link_libraries(test_diagnostics chess_core)
set_target_properties(test_diagnostics PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)

if(ENGINE_VARIANTS)
    add_executable(test_variants
            tests/cpp/test_variants.cpp
    )
    target_link_libraries(test_variants chess_core_variants)
    set_target_properties(test_variants PROPERTIES
            RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
    )
endif()

function(add_perft_test name fen depth expected)
    add_test(NAME "perft.${name}"
             COMMAND ChessEngine --perft-one "${fen}" ${depth} ${expected})
endfunction()

set(FEN_START  "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")
set(FEN_KIWI   "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1")
set(FEN_POS3   "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1")
set(FEN_POS4   "r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1")
set(FEN_POS5   "rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8")
set(FEN_POS6   "r4rk1/1pp1qppp/p1np1n2/2b1p1B1/2B1P1b1/P1NP1N2/1PP1QPPP/R4RK1 w - - 0 10")

add_perft_test(startpos_d1 "${FEN_START}" 1 20)
add_perft_test(startpos_d2 "${FEN_START}" 2 400)
add_perft_test(startpos_d3 "${FEN_START}" 3 8902)
add_perft_test(startpos_d4 "${FEN_START}" 4 197281)
add_perft_test(startpos_d5 "${FEN_START}" 5 4865609)
add_perft_test(kiwipete_d1 "${FEN_KIWI}" 1 48)
add_perft_test(kiwipete_d2 "${FEN_KIWI}" 2 2039)
add_perft_test(kiwipete_d3 "${FEN_KIWI}" 3 97862)
add_perft_test(kiwipete_d4 "${FEN_KIWI}" 4 4085603)
add_perft_test(kiwipete_d5 "${FEN_KIWI}" 5 193690690)
add_perft_test(position3_d1 "${FEN_POS3}" 1 14)
add_perft_test(position3_d2 "${FEN_POS3}" 2 191)
add_perft_test(position3_d3 "${FEN_POS3}" 3 2812)
add_perft_test(position3_d4 "${FEN_POS3}" 4 43238)
add_perft_test(position3_d5 "${FEN_POS3}" 5 674624)
add_perft_test(position3_d6 "${FEN_POS3}" 6 11030083)
add_perft_test(position4_d1 "${FEN_POS4}" 1 6)
add_perft_test(position4_d2 "${FEN_POS4}" 2 264)
add_perft_test(position4_d3 "${FEN_POS4}" 3 9467)
add_perft_test(position4_d4 "${FEN_POS4}" 4 422333)
add_perft_test(position4_d5 "${FEN_POS4}" 5 15833292)
add_perft_test(position5_d1 "${FEN_POS5}" 1 44)
add_perft_test(position5_d2 "${FEN_POS5}" 2 1486)
add_perft_test(position5_d3 "${FEN_POS5}" 3 62379)
add_perft_test(position5_d4 "${FEN_POS5}" 4 2103487)
add_perft_test(position6_d1 "${FEN_POS6}" 1 46)
add_perft_test(position6_d2 "${FEN_POS6}" 2 2079)
add_perft_test(position6_d3 "${FEN_POS6}" 3 89890)
add_perft_test(position6_d4 "${FEN_POS6}" 4 3894594)

add_test(NAME "consistency.nnue_simd_bitexact" COMMAND test_zobrist nnue)
add_test(NAME "consistency.make_unmake_and_movegen" COMMAND test_zobrist games)
add_test(NAME "diagnostics.perft_divide" COMMAND test_diagnostics divide)
add_test(NAME "movegen.legal_captures" COMMAND test_diagnostics captures)
add_test(NAME "state.fullmove_clock" COMMAND test_diagnostics clocks)
add_test(NAME "datagen.writer_boundaries" COMMAND test_diagnostics shards
         "${CMAKE_BINARY_DIR}/shard_writer_test")

# Drop variants: reserves, promoted-piece tracking and drop legality, plus the
# perft anchor that crazyhouse must equal standard chess until drops exist.
if(ENGINE_VARIANTS)
    add_test(NAME "variants.drops_state_and_perft" COMMAND test_variants)
    add_test(NAME "variants.smp_evaluation_policy" COMMAND test_variants "${CMAKE_SOURCE_DIR}/nets/stk-vector-64.nnue")
endif()

# Unguarded, these report as "Not Run" in an ENGINE_VIZ=OFF tree.
if(ENGINE_VIZ)
    # Layer attributions must sum to the same outputs as ordinary evaluation.
    add_test(NAME "viz.telemetry_exact" COMMAND test_viz frame)
    add_test(NAME "viz.recording_append" COMMAND test_viz recording "${CMAKE_BINARY_DIR}/recording_append.jsonl")
    add_test(NAME "viz.session_selfplay" COMMAND test_viz session)
    # Disable random openings so they cannot hide missing root-move variety.
    add_test(NAME "viz.selfplay_variety" COMMAND test_viz variety)
    # A resumed shard sequence must neither skip a file nor regenerate earlier games.
    add_test(NAME "viz.datagen_shards" COMMAND test_viz shards)
    # CI feeds this binary fixture to the TypeScript decoder to catch wire-format drift.
    add_test(NAME "viz.wire_fixture" COMMAND test_viz fixture "${CMAKE_BINARY_DIR}/viz_frame.bin")
endif()

if(WIN32)
    string(TOLOWER "${BASH_EXECUTABLE}" _bash_path)
    # The WSL launcher cannot execute native Windows CTest commands.
    if(_bash_path MATCHES "/(system32|sysnative)/bash(\\.exe)?$")
        unset(BASH_EXECUTABLE CACHE)
    endif()
    find_program(BASH_EXECUTABLE bash HINTS "$ENV{ProgramFiles}/Git/bin" "$ENV{ProgramFiles}/Git/usr/bin")
else()
    find_program(BASH_EXECUTABLE bash)
endif()
if(BASH_EXECUTABLE)
    add_test(NAME "search.bench_signature"
             COMMAND "${BASH_EXECUTABLE}" "${CMAKE_SOURCE_DIR}/tools/bench_signature.sh" $<TARGET_FILE:ChessEngine>)
endif()
