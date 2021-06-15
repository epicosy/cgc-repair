add_library(tiny-AES128-C aes.c)

set_target_properties(tiny-AES128-C PROPERTIES PUBLIC_HEADER "aes.h")
INSTALL(TARGETS tiny-AES128-C 
        LIBRARY DESTINATION /usr/local/lib/cgc/aes
        PUBLIC_HEADER DESTINATION /usr/local/include/cgc/aes
)
