// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"

struct Sprite
{
    short x;
    short y;
    unsigned char width;
    unsigned char height;
    unsigned short flags;
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

short screen[240][240];

short palette[64];

// background

short mainscreen_colour;
short subscreen_colour;

bool disable_background;

#define BG0_WIDTH_POWER 9
#define BG0_HEIGHT_POWER 9
#define BG0_WIDTH (1 << BG0_WIDTH_POWER)
#define BG0_HEIGHT (1 << BG0_HEIGHT_POWER)

short BG0[BG0_WIDTH][BG0_HEIGHT];
short bgscrollh;
short bgscrollv;

// color math
bool bg0_cmath_enable;
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
bool bg0_in_window;
bool bg0_out_window;
unsigned char bg0_window_log;

unsigned char window_1_left;
unsigned char window_1_right;
unsigned char window_2_left;
unsigned char window_2_right;

// sprites
#define SPRITE_COUNT 256

struct Sprite *main_sprite_cache[16];
struct Sprite *aux_sprite_cache[16];
struct Sprite OAM[SPRITE_COUNT];

#define OAM_LIMIT (OAM + SPRITE_COUNT)

unsigned char *sprites[256];

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

static void inline handle_bg(unsigned short *main, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
{
    if (!disable_background)
    {
        short bg0 = BG0[(x + bgscrollh) & (BG0_WIDTH - 1)][(y + bgscrollv) & (BG0_HEIGHT - 1)];
        if (bg0 != 0)
        {
            if (get_window(bg0_window_log, window_1, window_2, bg0_in_window, bg0_out_window))
            {
                *main = bg0;
                *c_math = bg0_cmath_enable;
            }
        }
    }
}

static short per_pixel(unsigned char x, unsigned char y)
{
    unsigned short main = mainscreen_colour;
    unsigned short sub = subscreen_colour;

    bool c_math = false;
    bool window_1 = (x >= window_1_left) && (x <= window_1_right);
    bool window_2 = (x >= window_2_left) && (x <= window_2_right);

    bool bg_handled = false;
    for (int i = 0; i < 16; i++)
    {
        struct Sprite *sprite = main_sprite_cache[i];
        if (sprite == NULL)
        {
            break;
        }
        unsigned short flags = sprite->flags;
        if ((flags & SPR_PRIORITY) && !bg_handled)
        {
            handle_bg(&main, &c_math, x, y, window_1, window_2);
            bg_handled = true;
        }
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
            unsigned char spr_pal = sprites[i][(offsety * (sprite->width)) + offsetx];
            if (spr_pal != 0)
            {
                short col = palette[spr_pal - 1];
                if (flags & SPR_MAIN_SCREEN)
                {
                    if (get_window((flags >> SPR_MAIN_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_MAIN_IN_WINDOW, flags & SPR_MAIN_OUT_WINDOW))
                    {
                        main = col;
                        c_math = flags & SPR_C_MATH;
                    }
                }
                if (flags & SPR_SUB_SCREEN)
                {
                    if (get_window((flags >> SPR_SUB_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_SUB_IN_WINDOW, flags & SPR_SUB_OUT_WINDOW))
                    {
                        sub = col;
                    }
                }
            }
        }
    }

    if (!bg_handled)
    {
        handle_bg(&main, &c_math, x, y, window_1, window_2);
    }

    bool use_cmath = cmath_enable & c_math;
    if (use_cmath || fade_enable)
    {
        unsigned char main_r = (main >> 11) & 0b00011111;
        unsigned char main_g = (main >> 5) & 0b00111111;
        unsigned char main_b = (main >> 0) & 0b00011111;
        if (use_cmath)
        {
            unsigned char sub_r = (sub >> 11) & 0b00011111;
            unsigned char sub_g = (sub >> 5) & 0b00111111;
            unsigned char sub_b = (sub >> 0) & 0b00011111;

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
    return main;
}

// main_sprite_cache is updated once per scanline
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
                aux_sprite_cache[sprites_high_prio++] = sprite;
            }
            else
            {
                main_sprite_cache[sprites_low_prio++] = sprite;
            }
        }
        if ((sprites_high_prio + sprites_low_prio) == 16)
        {
            break;
        }
    }
    for (int i = 0; i < sprites_high_prio;)
    {
        main_sprite_cache[sprites_low_prio++] = aux_sprite_cache[i++];
    }
    if (sprites_low_prio < 16)
    {
        main_sprite_cache[sprites_low_prio] = NULL;
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

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_render, MP_OBJ_FROM_PTR(&render_obj));

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
