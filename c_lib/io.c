// io.c
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

// Internal implementations
void io_print_int(int x) {
    printf("%d", x);
}

void io_print_str(const char* s) {
    printf("%s", s);
}

void io_print_bool(bool b) {
    printf(b ? "true\n" : "false");
}

// Read a line from stdin (simple version)
char* io_input_str(const char* prompt) {
    static char buffer[256];
    static char decoded[256];

    // Print prompt if not empty
    if (prompt && strlen(prompt) > 0) {
        fputs(prompt, stdout);
        fflush(stdout);
    }

    if (fgets(buffer, sizeof(buffer), stdin)) {
        buffer[strcspn(buffer, "\n")] = 0; // remove trailing newline
        // Decode escape sequences manually
        char* src = buffer;
        char* dst = decoded;

        while (*src) {
            if (*src == '\\') {
                src++;
                switch (*src) {
                    case 'n': *dst++ = '\n'; break;
                    case 't': *dst++ = '\t'; break;
                    case '\\': *dst++ = '\\'; break;
                    case '\"': *dst++ = '\"'; break;
                    case '\'': *dst++ = '\''; break;
                    case 'r': *dst++ = '\r'; break;
                    case '0': *dst++ = '\0'; break;
                    default: *dst++ = '\\'; *dst++ = *src; break;
                }
                src++;
            } else {
                *dst++ = *src++;
            }
        }
        *dst = '\0';
        return decoded;
    }
    return "";
}

int io_input_int(const char* prompt) {
    char* str = io_input_str(prompt);
    if (str == NULL || str[0] == '\0') {
        return 0;  // empty input fallback
    }
    return atoi(str);
}