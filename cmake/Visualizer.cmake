# Keep viz dependencies outside chess_core. With ENGINE_VIZ=OFF, no viz target
# may remain: its sources require the headers fetched inside this block.
option(ENGINE_VIZ "Build the NNUE visualizer binary (needs network on first configure)" ON)
if(ENGINE_VIZ)
    add_library(chess_viz STATIC
            src/viz/probe.cpp
            src/viz/probe.h
            src/viz/session.cpp
            src/viz/session.h
            src/viz/wire.cpp
            src/viz/wire.h
            src/viz/terminal.cpp
            src/viz/terminal.h
    )
    target_link_libraries(chess_viz PUBLIC chess_core)

    # Header-only MIT dependencies, pinned and fetched as single files (no git
    # history, no build system of their own). They are attached to chess_viz
    # only: the tournament binaries never see them.
    include(FetchContent)
    FetchContent_Declare(stk_json
            URL https://raw.githubusercontent.com/nlohmann/json/v3.11.3/single_include/nlohmann/json.hpp
            URL_HASH SHA256=9bea4c8066ef4a1c206b2be5a36302f8926f7fdc6087af5d20b417d0cf103ea6
            DOWNLOAD_NO_EXTRACT TRUE)
    FetchContent_Declare(stk_httplib
            URL https://raw.githubusercontent.com/yhirose/cpp-httplib/v0.18.3/httplib.h
            URL_HASH SHA256=a0a0c13dc086663863dbe6730a19716f7d3744904b6205496e8301750814dbd5
            DOWNLOAD_NO_EXTRACT TRUE)
    FetchContent_MakeAvailable(stk_json stk_httplib)
    target_include_directories(chess_viz PUBLIC
            ${stk_json_SOURCE_DIR} ${stk_httplib_SOURCE_DIR})
    target_compile_definitions(chess_viz PUBLIC STK_VIZ_DEPS)

    # --- ChessEngine-viz --------------------------------------------------
    # Embeds the default net (so it visualizes a real net out of the box) and,
    # when built, the single-file UI bundle. Both use the same .incbin / RCDATA
    # mechanism as ChessEngine-nnue.
    set(_viz_sources
            src/viz/main_viz.cpp
            src/viz/server.cpp
            src/viz/server.h
            src/viz/embedded_ui.cpp
            src/viz/embedded_ui.h)
    set(_viz_defs "")

    set(STK_UI_BUNDLE "${CMAKE_SOURCE_DIR}/ui/dist/index.html"
            CACHE FILEPATH "Single-file UI bundle embedded into ChessEngine-viz")

    if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang|MSVC")
        if(EXISTS "${EMBED_NNUE}")
            set(STK_EMBED_NNUE_PATH "${EMBED_NNUE}")
            list(APPEND _viz_defs STK_EMBED_NNUE)
            if(MSVC)
                enable_language(RC)
                configure_file(src/nnue/embedded_net.rc.in
                        ${CMAKE_BINARY_DIR}/viz_embedded_net.rc @ONLY)
                set_source_files_properties(${CMAKE_BINARY_DIR}/viz_embedded_net.rc
                        PROPERTIES OBJECT_DEPENDS "${EMBED_NNUE}")
                list(APPEND _viz_sources ${CMAKE_BINARY_DIR}/viz_embedded_net.rc)
            else()
                enable_language(ASM)
                configure_file(src/nnue/embedded_net.S.in
                        ${CMAKE_BINARY_DIR}/viz_embedded_net.S @ONLY)
                set_source_files_properties(${CMAKE_BINARY_DIR}/viz_embedded_net.S
                        PROPERTIES OBJECT_DEPENDS "${EMBED_NNUE}")
                list(APPEND _viz_sources ${CMAKE_BINARY_DIR}/viz_embedded_net.S)
            endif()
            list(APPEND _viz_sources src/nnue/embedded_net.cpp)
        endif()

        if(EXISTS "${STK_UI_BUNDLE}")
            set(STK_EMBED_UI_PATH "${STK_UI_BUNDLE}")
            list(APPEND _viz_defs STK_EMBED_UI)
            if(MSVC)
                enable_language(RC)
                configure_file(src/viz/embedded_ui.rc.in
                        ${CMAKE_BINARY_DIR}/embedded_ui.rc @ONLY)
                set_source_files_properties(${CMAKE_BINARY_DIR}/embedded_ui.rc
                        PROPERTIES OBJECT_DEPENDS "${STK_UI_BUNDLE}")
                list(APPEND _viz_sources ${CMAKE_BINARY_DIR}/embedded_ui.rc)
            else()
                enable_language(ASM)
                configure_file(src/viz/embedded_ui.S.in
                        ${CMAKE_BINARY_DIR}/embedded_ui.S @ONLY)
                # Rebuild the embed whenever the bundle changes -- otherwise
                # `npm run build` appears to do nothing.
                set_source_files_properties(${CMAKE_BINARY_DIR}/embedded_ui.S
                        PROPERTIES OBJECT_DEPENDS "${STK_UI_BUNDLE}")
                list(APPEND _viz_sources ${CMAKE_BINARY_DIR}/embedded_ui.S)
            endif()
            message(STATUS "Visualizer: embedding UI bundle ${STK_UI_BUNDLE}")
        else()
            message(STATUS "Visualizer: no UI bundle yet (serving placeholder); build ui/ to create ${STK_UI_BUNDLE}")
        endif()

        add_executable(ChessEngine-viz ${_viz_sources})
        target_link_libraries(ChessEngine-viz chess_viz)
        if(_viz_defs)
            target_compile_definitions(ChessEngine-viz PRIVATE ${_viz_defs})
        endif()
        if(WIN32)
            # ws2_32: sockets. shell32: ShellExecute, used to open the browser
            # without spawning a command processor.
            target_link_libraries(ChessEngine-viz ws2_32 shell32)
        endif()
        find_package(Threads REQUIRED)
        target_link_libraries(ChessEngine-viz Threads::Threads)
        set_target_properties(ChessEngine-viz PROPERTIES
                RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin)
    endif()

else()
    message(STATUS "Visualizer: skipped (ENGINE_VIZ=OFF); no viz targets or viz.* tests")
endif()
