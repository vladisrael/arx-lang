#include "core.h"

List* iter_list_int_range(int start, int end, int step) {
    int size = (end - start + step - 1) / step;
    List* lst = core_list_create(sizeof(int), false);
    for (int i = 0; i < size; ++i) {
        int value = start + i * step;
        core_list_append(lst, &value);
    }
    return lst;
}
