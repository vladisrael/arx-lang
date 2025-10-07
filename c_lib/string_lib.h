#ifndef CORE_STRING_LIB_H
#define CORE_STRING_LIB_H

#include <stdbool.h>

char* str_substring(const char* src, int start, int end);
char* str_repeat(const char* src, int times);
char* str_join(const char** parts, int count, const char* delimiter);
char* str_trim(const char* src);
char* str_trim_left(const char* src);
char* str_trim_right(const char* src);
char* str_replace(const char* src, const char* find, const char* replace);
int   str_index_of(const char* src, const char* substr);
int   str_last_index_of(const char* src, const char* substr);
bool  str_starts_with(const char* src, const char* prefix);
bool  str_ends_with(const char* src, const char* suffix);
char* str_to_lower(const char* src);
char* str_to_upper(const char* src);
bool  str_is_numeric(const char* src);
bool  str_is_alpha(const char* src);
bool  str_is_space(const char* src);

#endif
