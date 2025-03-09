// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"
#include "sasppu_fast.h"

#define DEFINE_TRIVIAL_ACCESSOR(name, mask)                              \
    static mp_obj_t name##_accessor(size_t n_args, const mp_obj_t *args) \
    {                                                                    \
        if (n_args > 0)                                                  \
        {                                                                \
            mp_int_t value = mp_obj_get_int(args[0]) & (mask);           \
            SASPPU_##name = value;                                       \
        }                                                                \
        return mp_obj_new_int(SASPPU_##name);                            \
    }                                                                    \
    static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(name##_obj, 0, 1, name##_accessor);

DEFINE_TRIVIAL_ACCESSOR(main_state_mainscreen_colour, 0xFFFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_subscreen_colour, 0xFFFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_window_1_left, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_window_1_right, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_window_2_left, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_window_2_right, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(main_state_flags, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(cmath_state_screen_fade, 0xFF);
DEFINE_TRIVIAL_ACCESSOR(cmath_state_flags, 0xFF);

typedef struct
{
    mp_obj_base_t base;
    mp_int_t x;
    mp_int_t y;
    mp_int_t windows;
    mp_int_t flags;
} mp_obj_background_t;

mp_obj_full_type_t mp_type_background;

static mp_obj_t background_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args_in)
{
    mp_arg_check_num(n_args, n_kw, 0, 0, false);

    mp_obj_background_t *o = mp_obj_malloc(mp_obj_background_t, type);

    return MP_OBJ_FROM_PTR(o);
}

typedef struct
{
    mp_obj_base_t base;
    mp_int_t x;
    mp_int_t y;
    mp_int_t width;
    mp_int_t height;
    mp_int_t graphics_x;
    mp_int_t graphics_y;
    mp_int_t windows;
    mp_int_t flags;
} mp_obj_sprite_t;

mp_obj_full_type_t mp_type_sprite;

static mp_obj_t sprite_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args_in)
{
    mp_arg_check_num(n_args, n_kw, 0, 0, false);

    mp_obj_sprite_t *o = mp_obj_malloc(mp_obj_sprite_t, type);

    return MP_OBJ_FROM_PTR(o);
}

static mp_obj_t bg0_state_accessor(size_t n_args, const mp_obj_t *args)
{
    if (n_args > 0)
    {
        mp_obj_background_t *value = MP_OBJ_TO_PTR(args[0]);
        SASPPU_bg0_state.x = value->x;
        SASPPU_bg0_state.y = value->y;
        SASPPU_bg0_state.windows = value->windows;
        SASPPU_bg0_state.flags = value->flags;
        return args[0];
    }
    else
    {
        mp_obj_background_t *value = MP_OBJ_TO_PTR(background_make_new((mp_obj_type_t *)&mp_type_background, 0, 0, NULL));
        value->x = SASPPU_bg0_state.x;
        value->y = SASPPU_bg0_state.y;
        value->windows = SASPPU_bg0_state.windows;
        value->flags = SASPPU_bg0_state.flags;
        return MP_OBJ_FROM_PTR(value);
    }
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(bg0_state_obj, 0, 1, bg0_state_accessor);

static mp_obj_t bg1_state_accessor(size_t n_args, const mp_obj_t *args)
{
    if (n_args > 0)
    {
        mp_obj_background_t *value = MP_OBJ_TO_PTR(args[0]);
        SASPPU_bg1_state.x = value->x;
        SASPPU_bg1_state.y = value->y;
        SASPPU_bg1_state.windows = value->windows;
        SASPPU_bg1_state.flags = value->flags;
        return args[0];
    }
    else
    {
        mp_obj_background_t *value = MP_OBJ_TO_PTR(background_make_new((mp_obj_type_t *)&mp_type_background, 0, 0, NULL));
        value->x = SASPPU_bg1_state.x;
        value->y = SASPPU_bg1_state.y;
        value->windows = SASPPU_bg1_state.windows;
        value->flags = SASPPU_bg1_state.flags;
        return MP_OBJ_FROM_PTR(value);
    }
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(bg1_state_obj, 0, 1, bg1_state_accessor);

static mp_obj_t oam_accessor(size_t n_args, const mp_obj_t *args)
{
    if (n_args > 1)
    {
        mp_int_t index = mp_obj_get_int(args[0]);
        mp_obj_sprite_t *value = MP_OBJ_TO_PTR(args[1]);
        SASPPU_oam[index].x = value->x;
        SASPPU_oam[index].y = value->y;
        SASPPU_oam[index].width = value->width;
        SASPPU_oam[index].height = value->height;
        SASPPU_oam[index].graphics_x = value->graphics_x;
        SASPPU_oam[index].graphics_y = value->graphics_y;
        SASPPU_oam[index].windows = value->windows;
        SASPPU_oam[index].flags = value->flags;
        return args[0];
    }
    else
    {
        mp_int_t index = mp_obj_get_int(args[0]);
        mp_obj_sprite_t *value = MP_OBJ_TO_PTR(sprite_make_new((mp_obj_type_t *)&mp_type_sprite, 0, 0, NULL));
        value->x = SASPPU_oam[index].x;
        value->y = SASPPU_oam[index].y;
        value->width = SASPPU_oam[index].width;
        value->height = SASPPU_oam[index].height;
        value->graphics_x = SASPPU_oam[index].graphics_x;
        value->graphics_y = SASPPU_oam[index].graphics_y;
        value->windows = SASPPU_oam[index].windows;
        value->flags = SASPPU_oam[index].flags;
        return MP_OBJ_FROM_PTR(value);
    }
}
static MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(oam_obj, 1, 2, oam_accessor);

static mp_obj_t get_framebuffer(void)
{
    // Create a list holding all items from the framebuffer
    mp_obj_list_t *lst = MP_OBJ_TO_PTR(mp_obj_new_list(MP_ARRAY_SIZE(SASPPU_frame_buffer), NULL));
    for (int i = 0; i < MP_ARRAY_SIZE(SASPPU_frame_buffer); ++i)
    {
        lst->items[i] = mp_obj_new_int(SASPPU_frame_buffer[i]);
    }
    return MP_OBJ_FROM_PTR(lst);
}
static MP_DEFINE_CONST_FUN_OBJ_0(get_framebuffer_obj, get_framebuffer);

static mp_obj_t render(void)
{
    SASPPU_render();
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_0(render_obj, render);

static mp_obj_t render_scanline(mp_obj_t x, mp_obj_t y)
{
    SASPPU_render_scanline(mp_obj_get_int(x), mp_obj_get_int(y));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(render_scanline_obj, render_scanline);

static mp_obj_t per_scanline(mp_obj_t x, mp_obj_t y)
{
    SASPPU_per_scanline(mp_obj_get_int(x), mp_obj_get_int(y));
    return mp_const_none;
}
static MP_DEFINE_CONST_FUN_OBJ_2(per_scanline_obj, per_scanline);

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Messages can be printed as usual
    mp_printf(&mp_plat_print, "initialising module sasppu=%p\n", self);

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_sasppuinternal_main_state_mainscreen_colour, MP_OBJ_FROM_PTR(&main_state_mainscreen_colour_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_subscreen_colour, MP_OBJ_FROM_PTR(&main_state_subscreen_colour_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_window_1_left, MP_OBJ_FROM_PTR(&main_state_window_1_left_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_window_1_right, MP_OBJ_FROM_PTR(&main_state_window_1_right_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_window_2_left, MP_OBJ_FROM_PTR(&main_state_window_2_left_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_window_2_right, MP_OBJ_FROM_PTR(&main_state_window_2_right_obj));
    mp_store_global(MP_QSTR_sasppuinternal_main_state_flags, MP_OBJ_FROM_PTR(&main_state_flags_obj));
    mp_store_global(MP_QSTR_sasppuinternal_cmath_state_screen_fade, MP_OBJ_FROM_PTR(&cmath_state_screen_fade_obj));
    mp_store_global(MP_QSTR_sasppuinternal_cmath_state_flags, MP_OBJ_FROM_PTR(&cmath_state_flags_obj));

    // Initialise the type.
    mp_type_background.base.type = (void *)&mp_type_type;
    mp_type_background.flags = MP_TYPE_FLAG_NONE;
    mp_type_background.name = MP_QSTR_Background;
    MP_OBJ_TYPE_SET_SLOT(&mp_type_background, make_new, background_make_new, 0);

    // Make the type available on the module.
    mp_store_global(MP_QSTR_sasppuinternal_Background, MP_OBJ_FROM_PTR(&mp_type_background));

    // Initialise the type.
    mp_type_sprite.base.type = (void *)&mp_type_type;
    mp_type_sprite.flags = MP_TYPE_FLAG_NONE;
    mp_type_sprite.name = MP_QSTR_Sprite;
    MP_OBJ_TYPE_SET_SLOT(&mp_type_sprite, make_new, sprite_make_new, 0);

    // Make the type available on the module.
    mp_store_global(MP_QSTR_sasppuinternal_Sprite, MP_OBJ_FROM_PTR(&mp_type_sprite));

    mp_store_global(MP_QSTR_sasppuinternal_bg0_state, MP_OBJ_FROM_PTR(&bg0_state_obj));
    mp_store_global(MP_QSTR_sasppuinternal_bg1_state, MP_OBJ_FROM_PTR(&bg1_state_obj));
    mp_store_global(MP_QSTR_sasppuinternal_oam, MP_OBJ_FROM_PTR(&oam_obj));

    mp_store_global(MP_QSTR_sasppuinteral_get_framebuffer, MP_OBJ_FROM_PTR(&get_framebuffer_obj));

    // Add some constants to the module's namespace
    mp_store_global(MP_QSTR_BG_WIDTH_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_BG_WIDTH_POWER));
    mp_store_global(MP_QSTR_BG_HEIGHT_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_BG_HEIGHT_POWER));
    mp_store_global(MP_QSTR_BG_WIDTH, MP_OBJ_NEW_SMALL_INT(MP_QSTR_BG_WIDTH));
    mp_store_global(MP_QSTR_BG_HEIGHT, MP_OBJ_NEW_SMALL_INT(MP_QSTR_BG_HEIGHT));
    mp_store_global(MP_QSTR_SPRITE_COUNT, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPRITE_COUNT));
    mp_store_global(MP_QSTR_SPRITE_CACHE, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPRITE_CACHE));
    mp_store_global(MP_QSTR_SPR_WIDTH_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_WIDTH_POWER));
    mp_store_global(MP_QSTR_SPR_HEIGHT_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_HEIGHT_POWER));
    mp_store_global(MP_QSTR_SPR_WIDTH, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_WIDTH));
    mp_store_global(MP_QSTR_SPR_HEIGHT, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_HEIGHT));
    mp_store_global(MP_QSTR_MAP_WIDTH_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_MAP_WIDTH_POWER));
    mp_store_global(MP_QSTR_MAP_HEIGHT_POWER, MP_OBJ_NEW_SMALL_INT(MP_QSTR_MAP_HEIGHT_POWER));
    mp_store_global(MP_QSTR_MAP_WIDTH, MP_OBJ_NEW_SMALL_INT(MP_QSTR_MAP_WIDTH));
    mp_store_global(MP_QSTR_MAP_HEIGHT, MP_OBJ_NEW_SMALL_INT(MP_QSTR_MAP_HEIGHT));
    mp_store_global(MP_QSTR_SPR_ENABLED, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_ENABLED));
    mp_store_global(MP_QSTR_SPR_PRIORITY, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_PRIORITY));
    mp_store_global(MP_QSTR_SPR_FLIP_X, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_FLIP_X));
    mp_store_global(MP_QSTR_SPR_FLIP_Y, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_FLIP_Y));
    mp_store_global(MP_QSTR_SPR_C_MATH, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_C_MATH));
    mp_store_global(MP_QSTR_SPR_DOUBLE, MP_OBJ_NEW_SMALL_INT(MP_QSTR_SPR_DOUBLE));
    mp_store_global(MP_QSTR_BG_C_MATH, MP_OBJ_NEW_SMALL_INT(MP_QSTR_BG_C_MATH));
    mp_store_global(MP_QSTR_CMATH_HALF_MAIN_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_HALF_MAIN_SCREEN));
    mp_store_global(MP_QSTR_CMATH_DOUBLE_MAIN_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_DOUBLE_MAIN_SCREEN));
    mp_store_global(MP_QSTR_CMATH_HALF_SUB_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_HALF_SUB_SCREEN));
    mp_store_global(MP_QSTR_CMATH_DOUBLE_SUB_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_DOUBLE_SUB_SCREEN));
    mp_store_global(MP_QSTR_CMATH_ADD_SUB_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_ADD_SUB_SCREEN));
    mp_store_global(MP_QSTR_CMATH_SUB_SUB_SCREEN, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_SUB_SUB_SCREEN));
    mp_store_global(MP_QSTR_CMATH_FADE_ENABLE, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_FADE_ENABLE));
    mp_store_global(MP_QSTR_CMATH_CMATH_ENABLE, MP_OBJ_NEW_SMALL_INT(MP_QSTR_CMATH_CMATH_ENABLE));
    mp_store_global(MP_QSTR_WINDOW_A, MP_OBJ_NEW_SMALL_INT(MP_QSTR_WINDOW_A));
    mp_store_global(MP_QSTR_WINDOW_B, MP_OBJ_NEW_SMALL_INT(MP_QSTR_WINDOW_B));
    mp_store_global(MP_QSTR_WINDOW_AB, MP_OBJ_NEW_SMALL_INT(MP_QSTR_WINDOW_AB));
    mp_store_global(MP_QSTR_WINDOW_X, MP_OBJ_NEW_SMALL_INT(MP_QSTR_WINDOW_X));

    mp_store_global(MP_QSTR_sasppuinternal_render, MP_OBJ_FROM_PTR(&render_obj));
    mp_store_global(MP_QSTR_sasppuinternal_render_scanline, MP_OBJ_FROM_PTR(&render_scanline_obj));
    mp_store_global(MP_QSTR_sasppuinternal_per_scanline, MP_OBJ_FROM_PTR(&per_scanline_obj));

    // SASPPU_table_init();

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}