// iter.c
#include "core.h"
#include <string.h>
#include <stdlib.h>

List* iter_list_int_range(int start, int end, int step) {
    if (step == 0) return NULL;

    int size = 0;
    if ((step > 0 && start < end))
        size = (end - start + step - 1) / step;
    else if ((step < 0 && start > end))
        size = (start - end - step - 1) / (-step);

    List* lst = core_list_create(sizeof(int), false);
    for (int i = 0, val = start; i < size; ++i, val += step)
        core_list_append(lst, &val);
    return lst;
}

List* string_split(const char* src, const char* delimiter) {
    if (!src || !delimiter || !*delimiter) return NULL;

    List* parts = core_list_create(sizeof(char*), true);
    const char* start = src;
    const char* pos;

    size_t delim_len = strlen(delimiter);

    while ((pos = strstr(start, delimiter)) != NULL) {
        size_t len = pos - start;
        char* part = malloc(len + 1);
        memcpy(part, start, len);
        part[len] = '\0';
        core_list_append(parts, &part);
        start = pos + delim_len;
    }

    if (*start) {
        char* part = strdup(start);
        core_list_append(parts, &part);
    }

    return parts;
}
