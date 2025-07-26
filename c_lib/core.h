// core.h
#ifndef CORE_H
#define CORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct {
    void* data;
    int length;
    int capacity;
    int64_t element_size;
    bool is_pointer;
} List;

char* core_string_concat(const char* a, const char* b);
List* core_list_create(int64_t element_size, bool is_pointer);
List* core_list_create_from(void* data, int len, int64_t element_size, bool is_pointer);
void core_list_append(List* list, void* value);
int core_list_len(List* list);
void* core_list_get(List* list, int index);
bool core_string_equal(const char* a, const char* b);

#endif
