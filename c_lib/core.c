#include "core.h"
#include <string.h>
#include <stdlib.h>
#include <stdbool.h>

char* core_string_concat(const char* a, const char* b) {
    size_t len = strlen(a) + strlen(b) + 1;
    char* result = malloc(len);
    if (!result) return NULL;
    strcpy(result, a);
    strcat(result, b);
    return result;
}

List* core_list_create_int() {
    List* list = malloc(sizeof(List));
    if (!list) return NULL;
    list->capacity = 8;
    list->length = 0;
    list->data = malloc(sizeof(int) * list->capacity);
    if (!list->data) {
        free(list);
        return NULL;
    }
    return list;
}

List* core_list_create_int_from(int* data, int len) {
    List* list = malloc(sizeof(List));
    list->data = malloc(sizeof(int) * len);
    for (int i = 0; i < len; ++i)
        list->data[i] = data[i];
    list->length = len;
    return list;
}

void core_list_append_int(List* list, int value) {
    if (!list) return;
    if (list->length >= list->capacity) {
        list->capacity *= 2;
        int* new_data = realloc(list->data, sizeof(int) * list->capacity);
        if (!new_data) return; // Could handle error here
        list->data = new_data;
    }
    list->data[list->length++] = value;
}

int core_list_len(List* list) {
    return list->length;
}

int core_list_get(List* list, int index) {
    return list->data[index];
}

bool core_string_equal(const char* a, const char* b) {
    return strcmp(a, b) == 0;
}
