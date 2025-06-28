#include <string.h>
#include <stdlib.h>

char* core_string_concat(const char* a, const char* b) {
    size_t len = strlen(a) + strlen(b) + 1;
    char* result = malloc(len);
    if (!result) return NULL;
    strcpy(result, a);
    strcat(result, b);
    return result;
}
