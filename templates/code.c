/** -*- mode: c-mode -*-
 * @file   {module_name}.c
 * @author Peter Züger
 * @date   {date}
 * @brief  generated
 *
 * This code was automatically generated from a python file.
 *
 * DO NOT MODIFY THIS FILE BY HAND.
 */
#include "py/runtime.h"

#if defined(MODULE_{module_name_u}_ENABLED) && MODULE_{module_name_u}_ENABLED

typedef struct _mp_obj_float_t{{
    mp_obj_base_t base;
    mp_float_t value;
}}mp_obj_float_t;

/**
 * This is an adaptation of MP_DEFINE_ATTRTUPLE and can be used to
 * define a constant tuple.
 *
 * See:
 * https://github.com/micropython/micropython/blob/0fff2e03fe07471997a6df6f92c6960cfd225dc0/py/objtuple.h
 */
#define MP_DEFINE_TUPLE(tuple_obj_name, nitems, ...) \
    const mp_rom_obj_tuple_t tuple_obj_name = {{ \
        .base = {{&mp_type_tuple}}, \
        .len = nitems, \
        .items = {{ __VA_ARGS__ }} \
    }}

#define MP_DEFINE_DICT(dict_name, table_name) \
    const mp_obj_dict_t dict_name = {{ \
        .base = {{&mp_type_dict}}, \
        .map = {{ \
            .all_keys_are_qstrs = 0, \
            .is_fixed = 1, \
            .is_ordered = 1, \
            .used = MP_ARRAY_SIZE(table_name), \
            .alloc = MP_ARRAY_SIZE(table_name), \
            .table = (mp_map_elem_t *)(mp_rom_map_elem_t *)table_name, \
        }}, \
    }}



{generated_code}

static const mp_rom_map_elem_t {module_name}_module_globals_table[] = {{
    {{ MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_{module_name}) }},
    {rom_table_entries}
}};
static MP_DEFINE_CONST_DICT({module_name}_module_globals, {module_name}_module_globals_table);

const mp_obj_module_t {module_name}_user_cmodule = {{
    .base = {{ &mp_type_module }},
    .globals = (mp_obj_dict_t *)&{module_name}_module_globals,
}};

MP_REGISTER_MODULE(MP_QSTR_{module_name}, {module_name}_user_cmodule);

#endif /* defined(MODULE_{module_name_u}_ENABLED) && MODULE_{module_name_u}_ENABLED */
