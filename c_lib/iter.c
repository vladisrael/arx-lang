#include "core.h"

List* iter_list_int_range(int start, int end, int step) {
    int size = (end - start + step - 1) / step;
    List* lst = core_list_create_int();
    for (int i = 0; i < size; ++i) {
        core_list_append_int(lst, start + i * step);
    }
    return lst;
}