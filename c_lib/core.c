#include "core.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

char* core_string_concat(const char* a, const char* b) {
    size_t len = strlen(a) + strlen(b) + 1;
    char* result = malloc(len);
    if (!result) return NULL;
    strcpy(result, a);
    strcat(result, b);
    return result;
}

List* core_list_create(int64_t element_size, bool is_pointer) {
    List* list = malloc(sizeof(List));
    if (!list) return NULL;

    list->capacity = 8;
    list->length = 0;
    list->element_size = element_size;
    list->is_pointer = is_pointer;
    list->data = malloc(element_size * list->capacity);

    if (!list->data) {
        free(list);
        return NULL;
    }

    return list;
}

List* core_list_create_from(void* data, int len, int64_t element_size, bool is_pointer) {
    List* list = malloc(sizeof(List));
    if (!list) return NULL;

    list->length = len;
    list->capacity = len;
    list->element_size = element_size;
    list->is_pointer = is_pointer;

    list->data = malloc(len * element_size);
    if (!list->data) {
        free(list);
        return NULL;
    }

    memcpy(list->data, data, len * element_size);
    return list;
}

void core_list_append(List* list, void* value) {
    if (!list) return;

    if (list->length >= list->capacity) {
        list->capacity *= 2;
        void* new_data = realloc(list->data, list->element_size * list->capacity);
        if (!new_data) return;
        list->data = new_data;
    }

    void* dest = (char*)list->data + list->length * list->element_size;
    memcpy(dest, value, list->element_size);
    list->length++;
}

int core_list_len(List* list) {
    return list ? list->length : 0;
}

void* core_list_get(List* list, int index) {
    if (!list || index < 0 || index >= list->length) return NULL;

    void* ptr = (void*)list->data + index * list->element_size;

    return list->is_pointer ? *(void**)ptr : ptr;
}

void core_list_free(List* list) {
    if (!list) return;
    free(list->data);
    free(list);
}
bool core_string_equal(const char* a, const char* b) {
    return strcmp(a, b) == 0;
}

List* core_list_slice(List* self, int start, int end) {
    if (!self || start < 0 || end > self->length || start > end) {
        fprintf(stderr, "Invalid slice indices: start=%d, end=%d, length=%d\n", start, end, self ? self->length : -1);
        exit(1);
    }

    int slice_len = end - start;
    List* result = malloc(sizeof(List));
    result->length = slice_len;
    result->capacity = slice_len;
    result->element_size = self->element_size;
    result->data = malloc(slice_len * self->element_size);

    void* src_ptr = (char*)self->data + (start * self->element_size);
    memcpy(result->data, src_ptr, slice_len * self->element_size);

    return result;
}

