file(GLOB srcs *.c)
add_library(pov ${srcs})

target_compile_definitions(pov PUBLIC -DNPATCHED)
if(NOT WIN32)
    target_compile_options(pov PUBLIC
        -pedantic
        -fno-builtin
        -O0
    )
endif()

target_include_directories(pov PUBLIC ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(pov LINK_PUBLIC cgc)

set(LIB_DESTINATION "/usr/local/lib64/cgc")
if(DEFINED ENV{M32})
    set(LIB_DESTINATION "/usr/local/lib32/cgc")
endif()

set_target_properties(pov PROPERTIES PUBLIC_HEADER "libpov.h;cgc_ucp.h;cgc_pcre_internal.h;cgc_config.h")
INSTALL(TARGETS pov 
        LIBRARY DESTINATION ${LIB_DESTINATION}
        PUBLIC_HEADER DESTINATION /usr/local/include/cgc/libpov
)

set_target_properties(pov PROPERTIES PUBLIC_HEADER "pov/cgc_ctype.h;pov/cgc_limits.h;pov/cgc_pcre.h;pov/cgc_stdlib.h;pov/cgc_string.h;pov/cgc_types.h")
INSTALL(TARGETS pov 
        PUBLIC_HEADER DESTINATION /usr/local/include/cgc/libpov/pov
)
