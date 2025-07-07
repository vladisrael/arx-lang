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

typedef struct {
    int* data;
    int length;
} List;

List* core_list_create_int(int* data, int len) {
    List* list = malloc(sizeof(List));
    list->data = malloc(sizeof(int) * len);
    for (int i = 0; i < len; ++i)
        list->data[i] = data[i];
    list->length = len;
    return list;
}

int core_list_len(List* list) {
    return list->length;
}

int core_list_get(List* list, int index) {
    return list->data[index];
}
