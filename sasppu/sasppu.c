// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"

struct Sprite
{
    short x;
    short y;
    unsigned char width;
    unsigned char height;
    unsigned short flags;
    unsigned char graphics_x;
    unsigned char graphics_y;
};

#define SPR_ENABLED (1 << 0)
#define SPR_FLIP_X (1 << 1)
#define SPR_FLIP_Y (1 << 2)
#define SPR_MAIN_SCREEN (1 << 3)
#define SPR_SUB_SCREEN (1 << 4)
#define SPR_C_MATH (1 << 5)
#define SPR_PRIORITY (1 << 6)
#define SPR_DOUBLE (1 << 7)
#define SPR_MAIN_IN_WINDOW (1 << 8)
#define SPR_MAIN_OUT_WINDOW (1 << 9)
#define SPR_MAIN_WINDOW_LOG2_LOG2 (10)
#define SPR_MAIN_WINDOW_LOG1 (1 << 10)
#define SPR_MAIN_WINDOW_LOG2 (1 << 11)
#define SPR_SUB_IN_WINDOW (1 << 12)
#define SPR_SUB_OUT_WINDOW (1 << 13)
#define SPR_SUB_WINDOW_LOG2_LOG2 (14)
#define SPR_SUB_WINDOW_LOG1 (1 << 14)
#define SPR_SUB_WINDOW_LOG2 (1 << 15)

unsigned short screen[240][240];

unsigned short palette[64];

// background

unsigned short mainscreen_colour;
unsigned short subscreen_colour;

bool enable_bg0;
bool enable_bg1;

#define BG0_WIDTH_POWER 9
#define BG0_HEIGHT_POWER 9
#define BG0_WIDTH (1 << BG0_WIDTH_POWER)
#define BG0_HEIGHT (1 << BG0_HEIGHT_POWER)
#define BG1_WIDTH_POWER 9
#define BG1_HEIGHT_POWER 9
#define BG1_WIDTH (1 << BG1_WIDTH_POWER)
#define BG1_HEIGHT (1 << BG1_HEIGHT_POWER)

unsigned short BG0[BG0_WIDTH][BG0_HEIGHT];
short bg0scrollh;
short bg0scrollv;
unsigned short BG1[BG1_WIDTH][BG1_HEIGHT];
short bg1scrollh;
short bg1scrollv;

// color math
bool bg0_cmath_enable;
bool bg1_cmath_enable;
bool bg0_main_screen_enable;
bool bg0_sub_screen_enable;
bool bg1_main_screen_enable;
bool bg1_sub_screen_enable;
bool half_main_screen;
bool double_main_screen;
bool half_sub_screen;
bool double_sub_screen;
bool add_sub_screen;
bool sub_sub_screen;
bool fade_enable;
unsigned short screen_fade;
bool cmath_enable;

// windowing
bool bg0_main_in_window;
bool bg0_main_out_window;
unsigned char bg0_main_window_log;
bool bg1_main_in_window;
bool bg1_main_out_window;
unsigned char bg1_main_window_log;
bool bg0_sub_in_window;
bool bg0_sub_out_window;
unsigned char bg0_sub_window_log;
bool bg1_sub_in_window;
bool bg1_sub_out_window;
unsigned char bg1_sub_window_log;

unsigned char window_1_left;
unsigned char window_1_right;
unsigned char window_2_left;
unsigned char window_2_right;

// sprites
#define SPRITE_COUNT 256

struct Sprite *low_sprite_cache[16];
struct Sprite *high_sprite_cache[16];
struct Sprite OAM[SPRITE_COUNT];

#define OAM_LIMIT (OAM + SPRITE_COUNT)

#define SPR_WIDTH_POWER 8
#define SPR_HEIGHT_POWER 8
#define SPR_WIDTH (1 << SPR_WIDTH_POWER)
#define SPR_HEIGHT (1 << SPR_HEIGHT_POWER)

unsigned char sprites[SPR_WIDTH][SPR_HEIGHT];

static bool inline get_window(unsigned char logic, bool window_1, bool window_2, bool in_window, bool out_window)
{
    bool window = false;
    switch (logic)
    {
    case 0:
        window = ~(window_1 ^ window_2);
        break;

    case 1:
        window = window_1 ^ window_2;
        break;
    case 2:
        window = window_1 & window_2;
        break;
    case 3:
        window = window_1 | window_2;
        break;
    }
    return ((window & in_window) | ((!window) & out_window));
}

static void inline handle_bg0(unsigned short *main_col, unsigned short *sub_col, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
{
    if (enable_bg0)
    {
        short bg0 = BG0[(x + bg0scrollh) & (BG0_WIDTH - 1)][(y + bg0scrollv) & (BG0_HEIGHT - 1)];
        if (bg0 != 0)
        {
            if (bg0_main_screen_enable && get_window(bg0_main_window_log, window_1, window_2, bg0_main_in_window, bg0_main_out_window))
            {
                *main_col = bg0;
                *c_math = bg0_cmath_enable;
            }
            if (bg0_sub_screen_enable && get_window(bg0_sub_window_log, window_1, window_2, bg0_sub_in_window, bg0_sub_out_window))
            {
                *sub_col = bg0;
            }
        }
    }
}

static void inline handle_bg1(unsigned short *main_col, unsigned short *sub_col, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
{
    if (enable_bg1)
    {
        short bg1 = BG1[(x + bg1scrollh) & (BG1_WIDTH - 1)][(y + bg1scrollv) & (BG1_HEIGHT - 1)];
        if (bg1 != 0)
        {
            if (bg1_main_screen_enable && get_window(bg1_main_window_log, window_1, window_2, bg1_main_in_window, bg1_main_out_window))
            {
                *main_col = bg1;
                *c_math = bg1_cmath_enable;
            }
            if (bg1_sub_screen_enable && get_window(bg1_sub_window_log, window_1, window_2, bg1_sub_in_window, bg1_sub_out_window))
            {
                *sub_col = bg1;
            }
        }
    }
}

static void inline handle_sprite(struct Sprite *sprite, unsigned short *main_col, unsigned short *sub_col, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
{
    unsigned short flags = sprite->flags;
    bool double_sprite = (flags & SPR_DOUBLE);
    short sprite_width = sprite->width;
    if (double_sprite)
    {
        sprite_width <<= 1;
    }
    short offsetx = (short)x - sprite->x;
    if ((offsetx >= 0) && (offsetx < sprite_width))
    {
        if (flags & SPR_FLIP_X)
        {
            offsetx = sprite_width - offsetx - 1;
        }
        short offsety = (short)y - sprite->y;
        if (flags & SPR_FLIP_Y)
        {
            offsety = sprite_width - offsetx - 1;
        }
        if (double_sprite)
        {
            offsetx >>= 1;
            offsety >>= 1;
        }
        unsigned char spr_pal = sprites[offsety + (sprite->graphics_y)][offsetx + (sprite->graphics_x)];
        if (spr_pal != 0)
        {
            short col = palette[spr_pal - 1];
            if (flags & SPR_MAIN_SCREEN)
            {
                if (get_window((flags >> SPR_MAIN_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_MAIN_IN_WINDOW, flags & SPR_MAIN_OUT_WINDOW))
                {
                    *main_col = col;
                    *c_math = flags & SPR_C_MATH;
                }
            }
            if (flags & SPR_SUB_SCREEN)
            {
                if (get_window((flags >> SPR_SUB_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_SUB_IN_WINDOW, flags & SPR_SUB_OUT_WINDOW))
                {
                    *sub_col = col;
                }
            }
        }
    }
}

static short per_pixel(unsigned char x, unsigned char y)
{
    unsigned short main_col = mainscreen_colour;
    unsigned short sub_col = subscreen_colour;

    bool c_math = false;
    bool window_1 = (x >= window_1_left) && (x <= window_1_right);
    bool window_2 = (x >= window_2_left) && (x <= window_2_right);

    handle_bg0(&main_col, &sub_col, &c_math, x, y, window_1, window_2);

    for (int i = 0; i < 16; i++)
    {
        struct Sprite *sprite = low_sprite_cache[i];
        if (sprite == NULL)
        {
            break;
        }
        handle_sprite(sprite, &main_col, &sub_col, &c_math, x, y, window_1, window_2);
    }

    handle_bg1(&main_col, &sub_col, &c_math, x, y, window_1, window_2);

    for (int i = 0; i < 16; i++)
    {
        struct Sprite *sprite = high_sprite_cache[i];
        if (sprite == NULL)
        {
            break;
        }
        handle_sprite(sprite, &main_col, &sub_col, &c_math, x, y, window_1, window_2);
    }

    bool use_cmath = cmath_enable & c_math;
    if (use_cmath || fade_enable)
    {
        unsigned char main_r = (main_col >> 11) & 0b00011111;
        unsigned char main_g = (main_col >> 5) & 0b00111111;
        unsigned char main_b = (main_col >> 0) & 0b00011111;
        if (use_cmath)
        {
            unsigned char sub_r = (sub_col >> 11) & 0b00011111;
            unsigned char sub_g = (sub_col >> 5) & 0b00111111;
            unsigned char sub_b = (sub_col >> 0) & 0b00011111;

            if (double_main_screen)
            {
                main_r = (main_r << 1) & 0b00011111;
                main_g = (main_g << 1) & 0b00111111;
                main_b = (main_b << 1) & 0b00011111;
            }
            if (half_main_screen)
            {
                main_r = (main_r >> 1);
                main_g = (main_g >> 1);
                main_b = (main_b >> 1);
            }
            if (double_sub_screen)
            {
                sub_r = (sub_r << 1) & 0b00011111;
                sub_g = (sub_g << 1) & 0b00111111;
                sub_b = (sub_b << 1) & 0b00011111;
            }
            if (half_sub_screen)
            {
                sub_r = (sub_r >> 1);
                sub_g = (sub_g >> 1);
                sub_b = (sub_b >> 1);
            }
            if (add_sub_screen)
            {
                main_r = (main_r + sub_r) & 0b00011111;
                main_g = (main_g + sub_g) & 0b00111111;
                main_b = (main_b + sub_b) & 0b00011111;
            }
            if (sub_sub_screen)
            {
                main_r = (main_r - sub_r) & 0b00011111;
                main_g = (main_g - sub_g) & 0b00111111;
                main_b = (main_b - sub_b) & 0b00011111;
            }
        }
        if (fade_enable)
        {
            main_r = (unsigned char)(((unsigned short)main_r * screen_fade) >> 8) & 0b00011111;
            main_g = (unsigned char)(((unsigned short)main_g * screen_fade) >> 8) & 0b00111111;
            main_b = (unsigned char)(((unsigned short)main_b * screen_fade) >> 8) & 0b00011111;
        }
        return (main_r << 11) | (main_g << 5) | (main_b);
    }
    return main_col;
}

// sprite_caches are updated once per scanline
static void per_scanline(unsigned short y)
{
    int sprites_low_prio = 0;
    int sprites_high_prio = 0;
    for (struct Sprite *sprite = OAM; sprite < OAM_LIMIT; sprite++)
    {
        unsigned short flags = sprite->flags;
        if (
            (flags & SPR_ENABLED) &&
            (((flags & SPR_MAIN_SCREEN) &&
              ((flags & SPR_MAIN_IN_WINDOW) ||
               (flags & SPR_MAIN_OUT_WINDOW))) ||
             ((flags & SPR_SUB_SCREEN) &&
              ((flags & SPR_SUB_IN_WINDOW) ||
               (flags & SPR_SUB_OUT_WINDOW)))) &&
            (y >= sprite->y) && (((flags & SPR_DOUBLE) && (y < (sprite->height << 1))) || (y < sprite->height)))
        {
            if (flags & SPR_PRIORITY)
            {
                high_sprite_cache[sprites_high_prio++] = sprite;
            }
            else
            {
                low_sprite_cache[sprites_low_prio++] = sprite;
            }
        }
        if ((sprites_high_prio + sprites_low_prio) == 16)
        {
            break;
        }
    }
    if (sprites_low_prio < 16)
    {
        low_sprite_cache[sprites_low_prio] = NULL;
    }
    if (sprites_high_prio < 16)
    {
        high_sprite_cache[sprites_high_prio] = NULL;
    }
}

STATIC mp_obj_t render(void)
{
    for (unsigned char y = 0; y < 240; y++)
    {
        per_scanline(y);
        for (unsigned char x = 0; x < 240; x++)
        {
            screen[x][y] = per_pixel(x, y);
        }
    }
    return mp_const_none;
}
// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_0(render_obj, (render));

STATIC mp_obj_t get_bg0_enabled(void)
{
    return mp_obj_new_bool(enable_bg0);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(get_bg0_enabled_obj, get_bg0_enabled);
STATIC mp_obj_t set_bg0_enabled(mp_obj_t b)
{
    enable_bg0 = mp_obj_is_true(b);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(set_bg0_enabled_obj, set_bg0_enabled);
STATIC mp_obj_t get_mainscreen_colour(void)
{
    return mp_obj_new_int(mainscreen_colour);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(get_mainscreen_colour_obj, get_mainscreen_colour);
STATIC mp_obj_t set_mainscreen_colour(mp_obj_t b)
{
    mainscreen_colour = mp_obj_get_int_truncated(b) & 0xFFFF;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(set_mainscreen_colour_obj, set_mainscreen_colour);

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_render, MP_OBJ_FROM_PTR(&render_obj));
    mp_store_global(MP_QSTR_get_bg0_enabled, MP_OBJ_FROM_PTR(&get_bg0_enabled_obj));
    mp_store_global(MP_QSTR_set_bg0_enabled, MP_OBJ_FROM_PTR(&set_bg0_enabled_obj));
    mp_store_global(MP_QSTR_get_mainscreen_colour, MP_OBJ_FROM_PTR(&get_mainscreen_colour_obj));
    mp_store_global(MP_QSTR_set_mainscreen_colour, MP_OBJ_FROM_PTR(&set_mainscreen_colour_obj));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
