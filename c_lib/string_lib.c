#include "string_lib.h"
#include <string.h>
#include <stdlib.h>
#include <ctype.h>

char* str_substring(const char* src, int start, int end) {
    if (!src || start < 0 || end < start) return NULL;
    int len = strlen(src);
    if (end > len) end = len;

    int sub_len = end - start;
    char* result = malloc(sub_len + 1);
    if (!result) return NULL;

    strncpy(result, src + start, sub_len);
    result[sub_len] = '\0';
    return result;
}

char* str_repeat(const char* src, int times) {
    if (!src || times <= 0) return strdup("");
    int len = strlen(src);
    char* result = malloc(len * times + 1);
    if (!result) return NULL;

    char* p = result;
    for (int i = 0; i < times; i++) {
        memcpy(p, src, len);
        p += len;
    }
    *p = '\0';
    return result;
}

char* str_join(const char** parts, int count, const char* delimiter) {
    if (count == 0) return strdup("");
    if (!delimiter) delimiter = "";

    int delim_len = strlen(delimiter);
    int total = 0;
    for (int i = 0; i < count; i++)
        total += strlen(parts[i]) + (i < count - 1 ? delim_len : 0);

    char* result = malloc(total + 1);
    if (!result) return NULL;
    result[0] = '\0';

    for (int i = 0; i < count; i++) {
        strcat(result, parts[i]);
        if (i < count - 1) strcat(result, delimiter);
    }
    return result;
}

char* str_trim_left(const char* src) {
    if (!src) return NULL;
    while (isspace((unsigned char)*src)) src++;
    return strdup(src);
}

char* str_trim_right(const char* src) {
    if (!src) return NULL;
    int len = strlen(src);
    while (len > 0 && isspace((unsigned char)src[len - 1])) len--;
    char* result = malloc(len + 1);
    if (!result) return NULL;
    strncpy(result, src, len);
    result[len] = '\0';
    return result;
}

char* str_trim(const char* src) {
    char* left = str_trim_left(src);
    char* both = str_trim_right(left);
    free(left);
    return both;
}

char* str_replace(const char* src, const char* find, const char* replace) {
    if (!src || !find || !replace) return NULL;
    const char* pos = src;
    int find_len = strlen(find);
    int replace_len = strlen(replace);
    int count = 0;

    while ((pos = strstr(pos, find))) {
        count++;
        pos += find_len;
    }
    if (count == 0) return strdup(src);

    // Allocate final buffer
    int new_len = strlen(src) + count * (replace_len - find_len);
    char* result = malloc(new_len + 1);
    if (!result) return NULL;

    const char* current = src;
    char* dest = result;
    while ((pos = strstr(current, find))) {
        int segment_len = pos - current;
        memcpy(dest, current, segment_len);
        dest += segment_len;
        memcpy(dest, replace, replace_len);
        dest += replace_len;
        current = pos + find_len;
    }
    strcpy(dest, current);
    return result;
}

int str_index_of(const char* src, const char* substr) {
    if (!src || !substr) return -1;
    char* p = strstr(src, substr);
    return p ? (int)(p - src) : -1;
}

int str_last_index_of(const char* src, const char* substr) {
    if (!src || !substr) return -1;
    int last = -1;
    int len = strlen(substr);
    const char* p = src;
    while ((p = strstr(p, substr))) {
        last = p - src;
        p += len;
    }
    return last;
}

bool str_starts_with(const char* src, const char* prefix) {
    if (!src || !prefix) return false;
    return strncmp(src, prefix, strlen(prefix)) == 0;
}

bool str_ends_with(const char* src, const char* suffix) {
    if (!src || !suffix) return false;
    int len_src = strlen(src);
    int len_suf = strlen(suffix);
    if (len_suf > len_src) return false;
    return strcmp(src + len_src - len_suf, suffix) == 0;
}

char* str_to_lower(const char* src) {
    if (!src) return NULL;
    char* result = strdup(src);
    for (char* p = result; *p; p++)
        *p = tolower((unsigned char)*p);
    return result;
}

char* str_to_upper(const char* src) {
    if (!src) return NULL;
    char* result = strdup(src);
    for (char* p = result; *p; p++)
        *p = toupper((unsigned char)*p);
    return result;
}

bool str_is_numeric(const char* src) {
    if (!src || !*src) return false;
    for (const char* p = src; *p; p++)
        if (!isdigit((unsigned char)*p)) return false;
    return true;
}

bool str_is_alpha(const char* src) {
    if (!src || !*src) return false;
    for (const char* p = src; *p; p++)
        if (!isalpha((unsigned char)*p)) return false;
    return true;
}

bool str_is_space(const char* src) {
    if (!src || !*src) return false;
    for (const char* p = src; *p; p++)
        if (!isspace((unsigned char)*p)) return false;
    return true;
}
