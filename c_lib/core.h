// core.h
#ifndef CORE_H
#define CORE_H

#include <stdbool.h>

typedef struct {
    int* data;
    int length;
    int capacity;
} List;

char* core_string_concat(const char* a, const char* b);
List* core_list_create_int();
List* core_list_create_int_from(int* data, int len);
void core_list_append_int(List* list, int value);
int core_list_len(List* list);
int core_list_get(List* list, int index);
bool core_string_equal(const char* a, const char* b);

#endif
