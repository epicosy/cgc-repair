add_library(tiny-AES128-C aes.c)

set(LIB_DESTINATION "/usr/local/lib64/cgc")
if(DEFINED ENV{M32})
    set(LIB_DESTINATION "/usr/local/lib32/cgc")
endif()

set_target_properties(tiny-AES128-C PROPERTIES PUBLIC_HEADER "aes.h")
INSTALL(TARGETS tiny-AES128-C 
        LIBRARY DESTINATION ${LIB_DESTINATION}
        PUBLIC_HEADER DESTINATION /usr/local/include/cgc/aes
)
