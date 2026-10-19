set(CORE_SOURCES
        src/perft/perft.cpp
        src/cores/position.cpp
        src/cores/movegen.cpp
        src/cores/attacks.cpp
        src/cores/zobrist.cpp
        src/uci/uci.cpp
        src/search/move_ordering.cpp
        src/search/evaluator.cpp
        src/search/search.cpp
        src/search/syzygy.cpp
        src/nnue/network.cpp
        src/datagen/datagen.cpp
        # Vendored Syzygy tablebase prober (Fathom, MIT). Built as C++ (see the
        # LANGUAGE property below) so it uses std::atomic / std::mutex on every
        # toolchain, avoiding MSVC's opt-in C11 atomics.
        third_party/fathom/tbprobe.c
)

set(CORE_HEADERS
        src/perft/perft.h
        src/cores/position.h
        src/cores/movegen.h
        src/cores/attacks.h
        src/cores/zobrist.h
        src/cores/types.h
        src/cores/bitboard.h
        src/cores/move.h
        src/cores/material.h
        src/cores/invariants.h
        src/uci/validator.h
        src/search/transposition_table.h
        src/search/move_ordering.h
        src/search/evaluator.h
        src/search/search.h
        src/search/syzygy.h
        src/nnue/halfka.h
        src/nnue/network.h
        src/datagen/datagen.h
)

add_library(chess_core STATIC ${CORE_SOURCES} ${CORE_HEADERS})
# Build Fathom's C source with the C++ compiler: it then selects std::atomic /
# std::mutex, which every toolchain supports without extra flags.
set_source_files_properties(third_party/fathom/tbprobe.c PROPERTIES LANGUAGE CXX)
target_include_directories(chess_core PUBLIC src)
# Fathom's own sources use quoted includes (tbconfig.h, stdendian.h, tbchess.c)
# resolved relative to this directory.
target_include_directories(chess_core PRIVATE third_party/fathom)

add_executable(ChessEngine
        app/main.cpp
)
target_link_libraries(ChessEngine chess_core)
set_target_properties(ChessEngine PROPERTIES
        RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)
