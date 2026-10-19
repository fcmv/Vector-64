# Embed the default net with RCDATA on MSVC and GNU-as .incbin on
# ELF, Mach-O and MinGW. Override it with -DEMBED_NNUE=/path/to/net.nnue.
set(EMBED_NNUE "${CMAKE_SOURCE_DIR}/nets/stk-vector-64.nnue"
        CACHE FILEPATH "Net embedded into the ChessEngine-nnue binary")
if(EXISTS "${EMBED_NNUE}" AND CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|MSVC")
        set(STK_EMBED_NNUE_PATH "${EMBED_NNUE}")
        set(_nnue_embed src/nnue/embedded_net.cpp)
        if(MSVC)
                # Windows resource (RCDATA); accessed via FindResource.
                enable_language(RC)
                configure_file(src/nnue/embedded_net.rc.in
                        ${CMAKE_BINARY_DIR}/embedded_net.rc @ONLY)
                # The resource only references the net by path, so make cannot
                # see that dependency by itself: state it, or a changed net
                # silently keeps the previously embedded bytes.
                set_source_files_properties(${CMAKE_BINARY_DIR}/embedded_net.rc
                        PROPERTIES OBJECT_DEPENDS "${EMBED_NNUE}")
                list(APPEND _nnue_embed ${CMAKE_BINARY_DIR}/embedded_net.rc)
        else()
                # GNU-as .incbin (ELF: Linux, Mach-O: macOS, PE-COFF: MinGW).
                enable_language(ASM)
                configure_file(src/nnue/embedded_net.S.in
                        ${CMAKE_BINARY_DIR}/embedded_net.S @ONLY)
                # .incbin pulls the net in at assemble time; make cannot see
                # that, so declare it or a changed net is silently ignored.
                set_source_files_properties(${CMAKE_BINARY_DIR}/embedded_net.S
                        PROPERTIES OBJECT_DEPENDS "${EMBED_NNUE}")
                list(APPEND _nnue_embed ${CMAKE_BINARY_DIR}/embedded_net.S)
        endif()
        add_executable(ChessEngine-nnue
                app/main.cpp
                ${_nnue_embed}
        )
        target_compile_definitions(ChessEngine-nnue PRIVATE STK_EMBED_NNUE)
        target_link_libraries(ChessEngine-nnue chess_core)
        set_target_properties(ChessEngine-nnue PROPERTIES
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
        message(STATUS "NNUE binary: ChessEngine-nnue embeds ${EMBED_NNUE}")
else()
        message(STATUS "NNUE binary: skipped (net '${EMBED_NNUE}' missing or unsupported toolchain)")
endif()

# Configure embed sources before this target reuses them. Drop variants suppress
# NNUE without unloading the net, so returning to chess restores NNUE.
if(ENGINE_VARIANTS AND TARGET ChessEngine-nnue)
        add_executable(ChessEngine-all
                app/main.cpp
                ${_nnue_embed}
        )
        target_compile_definitions(ChessEngine-all PRIVATE STK_EMBED_NNUE)
        target_link_libraries(ChessEngine-all chess_core_variants)
        set_target_properties(ChessEngine-all PROPERTIES
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
        message(STATUS "Combined binary: ChessEngine-all (chess+NNUE, crazyhouse, bughouse)")
endif()
