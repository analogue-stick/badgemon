// Include the header file to get access to the MicroPython API
#include "py/dynruntime.h"
// #include "extmod/modmachine.h"

#if !defined(__linux__)
void *memcpy(void *dst, const void *src, size_t n)
{
    return mp_fun_table.memmove_(dst, src, n);
}
void *memset(void *s, int c, size_t n)
{
    return mp_fun_table.memset_(s, c, n);
}
#endif

void *memmove(void *dest, const void *src, size_t n)
{
    return mp_fun_table.memmove_(dest, src, n);
}

typedef struct _sprite_obj_t
{
    mp_obj_base_t base;
    short x;
    short y;
    unsigned char width;
    unsigned char height;
    unsigned char graphics_x;
    unsigned char graphics_y;
    unsigned short flags;
} sprite_obj_t;

typedef sprite_obj_t Sprite;

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

mp_obj_t SPI;
mp_obj_t write_fun;
mp_obj_t CS;
mp_obj_t cs_on_fun;
mp_obj_t cs_off_fun;
mp_obj_t DC;
mp_obj_t dc_on_fun;
mp_obj_t dc_off_fun;
mp_obj_t RST;
mp_obj_t rst_on_fun;
mp_obj_t rst_off_fun;
mp_obj_t BACKLIGHT;
mp_obj_t backlight_on_fun;
mp_obj_t backlight_off_fun;

#define spi_write(buf) mp_call_function_n_kw(write_fun, 1, 0, ((mp_obj_t[1]){(buf)}))
#define cs_on mp_call_function_n_kw(cs_on_fun, 0, 0, mp_const_none)
#define cs_off mp_call_function_n_kw(cs_off_fun, 0, 0, mp_const_none)
#define dc_on mp_call_function_n_kw(dc_on_fun, 0, 0, mp_const_none)
#define dc_off mp_call_function_n_kw(dc_off_fun, 0, 0, mp_const_none)
#define rst_on mp_call_function_n_kw(rst_on_fun, 0, 0, mp_const_none)
#define rst_off mp_call_function_n_kw(rst_off_fun, 0, 0, mp_const_none)
#define backlight_on mp_call_function_n_kw(backlight_on_fun, 0, 0, mp_const_none)
#define backlight_off mp_call_function_n_kw(backlight_off_fun, 0, 0, mp_const_none)

#define GC9A01_SWRESET 0x01
#define GC9A01_SLPIN 0x10
#define GC9A01_SLPOUT 0x11
#define GC9A01_INVOFF 0x20
#define GC9A01_INVON 0x21
#define GC9A01_DISPOFF 0x28
#define GC9A01_DISPON 0x29
#define GC9A01_CASET 0x2A
#define GC9A01_RASET 0x2B
#define GC9A01_RAMWR 0x2C
#define GC9A01_VSCRDEF 0x33
#define GC9A01_COLMOD 0x3A
#define GC9A01_MADCTL 0x36
#define GC9A01_VSCSAD 0x37

// background
#define BG0_WIDTH_POWER 9
#define BG0_HEIGHT_POWER 9
#define BG0_WIDTH (1 << BG0_WIDTH_POWER)
#define BG0_HEIGHT (1 << BG0_HEIGHT_POWER)
#define BG1_WIDTH_POWER 9
#define BG1_HEIGHT_POWER 9
#define BG1_WIDTH (1 << BG1_WIDTH_POWER)
#define BG1_HEIGHT (1 << BG1_HEIGHT_POWER)

unsigned short BG0[BG0_WIDTH][BG0_HEIGHT];
unsigned short BG1[BG1_WIDTH][BG1_HEIGHT];

typedef struct _state_obj_t
{
    mp_obj_base_t base;
    unsigned short mainscreen_colour;
    unsigned short subscreen_colour;

    bool enable_bg0;
    bool enable_bg1;

    short bg0scrollh;
    short bg0scrollv;
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
    unsigned char screen_fade;
    bool cmath_enable;
    bool cmath_default;

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
} state_obj_t;

state_obj_t state;

// sprites
#define SPRITE_COUNT 256

Sprite *low_sprite_cache[16];
Sprite *high_sprite_cache[16];
Sprite OAM[SPRITE_COUNT];

#define OAM_LIMIT (OAM + SPRITE_COUNT)

#define SPR_WIDTH_POWER 8
#define SPR_HEIGHT_POWER 8
#define SPR_WIDTH (1 << SPR_WIDTH_POWER)
#define SPR_HEIGHT (1 << SPR_HEIGHT_POWER)

unsigned short sprites[SPR_WIDTH][SPR_HEIGHT];

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
    if (state.enable_bg0)
    {
        short bg0 = BG0[(x + state.bg0scrollh) & (BG0_WIDTH - 1)][(y + state.bg0scrollv) & (BG0_HEIGHT - 1)];
        if (bg0 != 0)
        {
            if (state.bg0_main_screen_enable && get_window(state.bg0_main_window_log, window_1, window_2, state.bg0_main_in_window, state.bg0_main_out_window))
            {
                *main_col = bg0;
                *c_math = state.bg0_cmath_enable;
            }
            if (state.bg0_sub_screen_enable && get_window(state.bg0_sub_window_log, window_1, window_2, state.bg0_sub_in_window, state.bg0_sub_out_window))
            {
                *sub_col = bg0;
            }
        }
    }
}

static void inline handle_bg1(unsigned short *main_col, unsigned short *sub_col, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
{
    if (state.enable_bg1)
    {
        short bg1 = BG1[(x + state.bg1scrollh) & (BG1_WIDTH - 1)][(y + state.bg1scrollv) & (BG1_HEIGHT - 1)];
        if (bg1 != 0)
        {
            if (state.bg1_main_screen_enable && get_window(state.bg1_main_window_log, window_1, window_2, state.bg1_main_in_window, state.bg1_main_out_window))
            {
                *main_col = bg1;
                *c_math = state.bg1_cmath_enable;
            }
            if (state.bg1_sub_screen_enable && get_window(state.bg1_sub_window_log, window_1, window_2, state.bg1_sub_in_window, state.bg1_sub_out_window))
            {
                *sub_col = bg1;
            }
        }
    }
}

static void inline handle_sprite(Sprite *sprite, unsigned short *main_col, unsigned short *sub_col, bool *c_math, unsigned char x, unsigned char y, bool window_1, bool window_2)
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
        unsigned short spr_col = sprites[offsety + (sprite->graphics_y)][offsetx + (sprite->graphics_x)];
        if (spr_col != 0)
        {
            if (flags & SPR_MAIN_SCREEN)
            {
                if (get_window((flags >> SPR_MAIN_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_MAIN_IN_WINDOW, flags & SPR_MAIN_OUT_WINDOW))
                {
                    *main_col = spr_col;
                    *c_math = flags & SPR_C_MATH;
                }
            }
            if (flags & SPR_SUB_SCREEN)
            {
                if (get_window((flags >> SPR_SUB_WINDOW_LOG2_LOG2) & 3, window_1, window_2, flags & SPR_SUB_IN_WINDOW, flags & SPR_SUB_OUT_WINDOW))
                {
                    *sub_col = spr_col;
                }
            }
        }
    }
}

static unsigned short per_pixel(unsigned char x, unsigned char y)
{
    unsigned short main_col = state.mainscreen_colour;
    unsigned short sub_col = state.subscreen_colour;

    bool c_math = state.cmath_default;
    bool window_1 = (x >= state.window_1_left) && (x <= state.window_1_right);
    bool window_2 = (x >= state.window_2_left) && (x <= state.window_2_right);

    handle_bg0(&main_col, &sub_col, &c_math, x, y, window_1, window_2);

    for (int i = 0; i < 16; i++)
    {
        Sprite *sprite = low_sprite_cache[i];
        if (sprite == NULL)
        {
            break;
        }
        handle_sprite(sprite, &main_col, &sub_col, &c_math, x, y, window_1, window_2);
    }

    handle_bg1(&main_col, &sub_col, &c_math, x, y, window_1, window_2);

    for (int i = 0; i < 16; i++)
    {
        Sprite *sprite = high_sprite_cache[i];
        if (sprite == NULL)
        {
            break;
        }
        handle_sprite(sprite, &main_col, &sub_col, &c_math, x, y, window_1, window_2);
    }

    bool use_cmath = state.cmath_enable & c_math;
    if (use_cmath || state.fade_enable)
    {
        unsigned char main_r = (main_col >> 11) & 0b00011111;
        unsigned char main_g = (main_col >> 5) & 0b00111111;
        unsigned char main_b = (main_col >> 0) & 0b00011111;
        if (use_cmath)
        {
            unsigned char sub_r = (sub_col >> 11) & 0b00011111;
            unsigned char sub_g = (sub_col >> 5) & 0b00111111;
            unsigned char sub_b = (sub_col >> 0) & 0b00011111;

            if (state.double_main_screen)
            {
                main_r = (main_r << 1) & 0b00011111;
                main_g = (main_g << 1) & 0b00111111;
                main_b = (main_b << 1) & 0b00011111;
            }
            if (state.half_main_screen)
            {
                main_r = (main_r >> 1);
                main_g = (main_g >> 1);
                main_b = (main_b >> 1);
            }
            if (state.double_sub_screen)
            {
                sub_r = (sub_r << 1) & 0b00011111;
                sub_g = (sub_g << 1) & 0b00111111;
                sub_b = (sub_b << 1) & 0b00011111;
            }
            if (state.half_sub_screen)
            {
                sub_r = (sub_r >> 1);
                sub_g = (sub_g >> 1);
                sub_b = (sub_b >> 1);
            }
            if (state.add_sub_screen)
            {
                main_r = MIN(main_r + sub_r, 0b00011111);
                main_g = MIN(main_g + sub_g, 0b00111111);
                main_b = MIN(main_b + sub_b, 0b00011111);
            }
            if (state.sub_sub_screen)
            {
                main_r -= sub_r;
                if (main_r > 0b00011111)
                    main_r = 0;
                main_g -= sub_g;
                if (main_g > 0b00111111)
                    main_g = 0;
                main_b -= sub_b;
                if (main_b > 0b00011111)
                    main_b = 0;
            }
        }
        if (state.fade_enable)
        {
            main_r = (unsigned char)(((unsigned short)main_r * state.screen_fade) >> 8) & 0b00011111;
            main_g = (unsigned char)(((unsigned short)main_g * state.screen_fade) >> 8) & 0b00111111;
            main_b = (unsigned char)(((unsigned short)main_b * state.screen_fade) >> 8) & 0b00011111;
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
    for (Sprite *sprite = OAM; sprite < OAM_LIMIT; sprite++)
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

/*
static mp_obj_t blit_buffer(size_t n_args, const mp_obj_t *args)
{
    gc9a01_GC9A01_obj_t *self = MP_OBJ_TO_PTR(args[0]);
    mp_buffer_info_t buf_info;

    mp_get_buffer_raise(args[1], &buf_info, MP_BUFFER_READ);

    mp_int_t x = mp_obj_get_int(args[2]);
    mp_int_t y = mp_obj_get_int(args[3]);
    mp_int_t w = mp_obj_get_int(args[4]);
    mp_int_t h = mp_obj_get_int(args[5]);

    set_window(self, x, y, x + w - 1, y + h - 1);
    DC_HIGH();
    CS_LOW();

    const int buf_size = 256;
    int limit = MIN(buf_info.len, w * h * 2);
    int chunks = limit / buf_size;
    int rest = limit % buf_size;
    int i = 0;

    for (; i < chunks; i++)
    {
        write_spi(self->spi_obj, (const uint8_t *)buf_info.buf + i * buf_size, buf_size);
    }
    if (rest)
    {
        write_spi(self->spi_obj, (const uint8_t *)buf_info.buf + i * buf_size, rest);
    }
    CS_HIGH();
    mp_machine_spi_p_t

        return mp_const_none;
}
*/

STATIC mp_obj_t render(void)
{
    for (unsigned char y = 0; y < 240; y++)
        for (unsigned char x = 0; x < 240; x++)
        {
            unsigned short col = (31 << 11);
            screen[y][x] = (col >> 8) | (col << 8);
        }
    for (unsigned char y = 110; y < 130; y++)
    {
        per_scanline(y);
        for (unsigned char x = 110; x < 130; x++)
        {
            unsigned short col = per_pixel(x, y);
            screen[y][x] = (col >> 8) | (col << 8);
        }
    }
    // spi_write(mp_obj_new_bytes((unsigned char *)screen, sizeof(screen)));
    return mp_obj_new_bytes((unsigned char *)screen, sizeof(screen));
}
// Define a Python reference to the function above
STATIC MP_DEFINE_CONST_FUN_OBJ_0(render_obj, (render));

mp_obj_full_type_t sprite_type;
mp_obj_full_type_t state_type;

STATIC mp_obj_t save_sprite(mp_obj_t sprite, mp_obj_t position)
{
    if (!mp_obj_is_type(sprite, (mp_obj_type_t *)(&sprite_type)))
    {
        mp_raise_TypeError("argument is not a sprite");
    }
    sprite_obj_t *sprite_local = MP_OBJ_TO_PTR(sprite);
    mp_int_t pos = mp_obj_get_int(position) & 0xFF;
    OAM[pos] = *sprite_local;
    return mp_const_none;
}

STATIC mp_obj_t load_sprite(mp_obj_t position)
{
    mp_int_t pos = mp_obj_get_int(position) & 0xFF;
    return MP_OBJ_TO_PTR(&OAM[pos]);
}

STATIC MP_DEFINE_CONST_FUN_OBJ_2(save_sprite_obj, save_sprite);
STATIC MP_DEFINE_CONST_FUN_OBJ_1(load_sprite_obj, load_sprite);

STATIC mp_obj_t blit_sprite(size_t n_args, const mp_obj_t *args)
{
    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(args[0], &buf_info, MP_BUFFER_READ);
    mp_int_t x = mp_obj_get_int(args[1]);
    mp_int_t y = mp_obj_get_int(args[2]);
    mp_int_t w = mp_obj_get_int(args[3]);
    mp_int_t h = mp_obj_get_int(args[4]);
    mp_int_t endh = x + w;
    mp_int_t endv = y + h;
    if (buf_info.len < w * h * 2)
    {
        mp_raise_ValueError("This ain't it bro");
    }
    short *bufpos = buf_info.buf;
    for (; y < endv; y++)
        for (; x < endh; x++)
            sprites[y][x] = *bufpos++;

    return mp_const_none;
}

STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(blit_sprite_obj, 5, 5, blit_sprite);

STATIC inline mp_obj_t blit_background(unsigned short BG[BG0_WIDTH][BG0_HEIGHT], size_t n_args, const mp_obj_t *args)
{
    mp_buffer_info_t buf_info;
    mp_get_buffer_raise(args[0], &buf_info, MP_BUFFER_READ);
    mp_int_t x = mp_obj_get_int(args[1]);
    mp_int_t y = mp_obj_get_int(args[2]);
    mp_int_t w = mp_obj_get_int(args[3]);
    mp_int_t h = mp_obj_get_int(args[4]);
    mp_int_t endh = x + w;
    mp_int_t endv = y + h;
    if (buf_info.len < w * h * 2)
    {
        mp_raise_ValueError("This ain't it bro");
    }
    short *bufpos = buf_info.buf;
    for (; y < endv; y++)
        for (; x < endh; x++)
            BG[y][x] = *bufpos++;

    return mp_const_none;
}

STATIC mp_obj_t blit_bg0(size_t n_args, const mp_obj_t *args)
{
    return blit_background(BG0, n_args, args);
}
STATIC mp_obj_t blit_bg1(size_t n_args, const mp_obj_t *args)
{
    return blit_background(BG1, n_args, args);
}

STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(blit_bg0_obj, 5, 5, blit_bg0);
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(blit_bg1_obj, 5, 5, blit_bg1);

STATIC void sprite_init(sprite_obj_t *self)
{
    self->flags = 0;
    self->x = 0;
    self->y = 0;
    self->graphics_x = 0;
    self->graphics_y = 0;
    self->width = 32;
    self->height = 32;
}

STATIC mp_obj_t sprite_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args)
{
    mp_arg_check_num(n_args, n_kw, 0, 0, false);
    sprite_obj_t *self = mp_obj_malloc(sprite_obj_t, type);
    return MP_OBJ_FROM_PTR(self);
}

STATIC void sprite_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest)
{
    sprite_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL)
    {
        if (attr == MP_QSTR_x)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->x);
            return;
        }
        if (attr == MP_QSTR_y)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->y);
            return;
        }
        if (attr == MP_QSTR_graphics_x)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->graphics_x);
            return;
        }
        if (attr == MP_QSTR_graphics_y)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->graphics_y);
            return;
        }
        if (attr == MP_QSTR_width)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->width);
            return;
        }
        if (attr == MP_QSTR_height)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->height);
            return;
        }
        if (attr == MP_QSTR_enabled)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_ENABLED);
            return;
        }
        if (attr == MP_QSTR_flip_x)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_FLIP_X);
            return;
        }
        if (attr == MP_QSTR_flip_y)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_FLIP_Y);
            return;
        }
        if (attr == MP_QSTR_main_screen)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_MAIN_SCREEN);
            return;
        }
        if (attr == MP_QSTR_sub_screen)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_SUB_SCREEN);
            return;
        }
        if (attr == MP_QSTR_c_math)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_C_MATH);
            return;
        }
        if (attr == MP_QSTR_priority)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_PRIORITY);
            return;
        }
        if (attr == MP_QSTR_double)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_DOUBLE);
            return;
        }
        if (attr == MP_QSTR_main_in_window)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_MAIN_IN_WINDOW);
            return;
        }
        if (attr == MP_QSTR_main_out_window)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_MAIN_OUT_WINDOW);
            return;
        }
        if (attr == MP_QSTR_main_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->flags >> SPR_MAIN_WINDOW_LOG2_LOG2) & 0x3);
            return;
        }
        if (attr == MP_QSTR_sub_in_window)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_SUB_IN_WINDOW);
            return;
        }
        if (attr == MP_QSTR_sub_out_window)
        {
            dest[0] = mp_obj_new_bool(self->flags & SPR_SUB_OUT_WINDOW);
            return;
        }
        if (attr == MP_QSTR_sub_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->flags >> SPR_SUB_WINDOW_LOG2_LOG2) & 0x3);
            return;
        }
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Unknown attribute"));
    }
    else
    {
        // Set or delete attribute
        if (dest[1] == MP_OBJ_NULL)
        {
            // We don't support deleting attributes.
            mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Cannot delete attribute"));
            return;
        }
        if (attr == MP_QSTR_x)
        {
            self->x = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_y)
        {
            self->y = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_graphics_x)
        {
            self->graphics_x = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_graphics_y)
        {
            self->graphics_y = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_width)
        {
            self->width = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_height)
        {
            self->height = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_enabled)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_ENABLED) : (self->flags & (~SPR_ENABLED));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_flip_x)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_FLIP_X) : (self->flags & (~SPR_FLIP_X));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_flip_y)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_FLIP_Y) : (self->flags & (~SPR_FLIP_Y));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_main_screen)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_MAIN_SCREEN) : (self->flags & (~SPR_MAIN_SCREEN));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_sub_screen)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_SUB_SCREEN) : (self->flags & (~SPR_SUB_SCREEN));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_c_math)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_C_MATH) : (self->flags & (~SPR_C_MATH));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_priority)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_PRIORITY) : (self->flags & (~SPR_PRIORITY));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_double)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_DOUBLE) : (self->flags & (~SPR_DOUBLE));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_main_in_window)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_MAIN_IN_WINDOW) : (self->flags & (~SPR_MAIN_IN_WINDOW));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_main_out_window)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_MAIN_OUT_WINDOW) : (self->flags & (~SPR_MAIN_OUT_WINDOW));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_main_window_log)
        {
            self->flags = ((self->flags & (~(0x3 << SPR_MAIN_WINDOW_LOG2_LOG2))) | (mp_obj_get_int(dest[1]) & 0x3 << SPR_MAIN_WINDOW_LOG2_LOG2));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_sub_in_window)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_SUB_IN_WINDOW) : (self->flags & (~SPR_SUB_IN_WINDOW));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_sub_out_window)
        {
            self->flags = mp_obj_is_true(dest[1]) ? (self->flags | SPR_SUB_OUT_WINDOW) : (self->flags & (~SPR_SUB_OUT_WINDOW));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_sub_window_log)
        {
            self->flags = ((self->flags & (~(0x3 << SPR_SUB_WINDOW_LOG2_LOG2))) | (mp_obj_get_int(dest[1]) & 0x3 << SPR_SUB_WINDOW_LOG2_LOG2));
            dest[0] = MP_OBJ_NULL;
            return;
        }
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Unknown attribute"));
    }
}

STATIC void state_attr(mp_obj_t self_in, qstr attr, mp_obj_t *dest)
{
    state_obj_t *self = MP_OBJ_TO_PTR(self_in);
    if (dest[0] == MP_OBJ_NULL)
    {
        if (attr == MP_QSTR_mainscreen_colour)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->mainscreen_colour);
            return;
        }
        if (attr == MP_QSTR_subscreen_colour)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->subscreen_colour);
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_r)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->mainscreen_colour >> 11) & 0x1F);
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_g)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->mainscreen_colour >> 5) & 0x3F);
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_b)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->mainscreen_colour >> 0) & 0x1F);
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_r)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->subscreen_colour >> 11) & 0x1F);
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_g)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->subscreen_colour >> 5) & 0x3F);
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_b)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT((self->subscreen_colour >> 0) & 0x1F);
            return;
        }
        if (attr == MP_QSTR_bg0scrollh)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg0scrollh & 0xFFFF);
            return;
        }
        if (attr == MP_QSTR_bg1scrollh)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg1scrollh & 0xFFFF);
            return;
        }
        if (attr == MP_QSTR_bg0scrollv)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg0scrollv & 0xFFFF);
            return;
        }
        if (attr == MP_QSTR_bg1scrollv)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg1scrollv & 0xFFFF);
            return;
        }
        if (attr == MP_QSTR_screen_fade)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->screen_fade & 0xFF);
            return;
        }
        if (attr == MP_QSTR_bg0_main_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg0_main_window_log & 0xFF);
            return;
        }
        if (attr == MP_QSTR_bg1_main_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg1_main_window_log & 0xFF);
            return;
        }
        if (attr == MP_QSTR_bg0_sub_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg0_sub_window_log & 0xFF);
            return;
        }
        if (attr == MP_QSTR_bg1_sub_window_log)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->bg1_sub_window_log & 0xFF);
            return;
        }
        if (attr == MP_QSTR_window_1_left)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->window_1_left & 0xFF);
            return;
        }
        if (attr == MP_QSTR_window_1_right)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->window_1_right & 0xFF);
            return;
        }
        if (attr == MP_QSTR_window_2_left)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->window_2_left & 0xFF);
            return;
        }
        if (attr == MP_QSTR_window_2_right)
        {
            dest[0] = MP_OBJ_NEW_SMALL_INT(self->window_2_right & 0xFF);
            return;
        }
        if (attr == MP_QSTR_enable_bg0)
        {
            dest[0] = mp_obj_new_bool(self->enable_bg0);
            return;
        }
        if (attr == MP_QSTR_enable_bg1)
        {
            dest[0] = mp_obj_new_bool(self->enable_bg1);
            return;
        }
        if (attr == MP_QSTR_bg0_cmath_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg0_cmath_enable);
            return;
        }
        if (attr == MP_QSTR_bg0_cmath_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg0_cmath_enable);
            return;
        }
        if (attr == MP_QSTR_bg1_cmath_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg1_cmath_enable);
            return;
        }
        if (attr == MP_QSTR_bg0_main_screen_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg0_main_screen_enable);
            return;
        }
        if (attr == MP_QSTR_bg1_main_screen_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg1_main_screen_enable);
            return;
        }
        if (attr == MP_QSTR_bg0_sub_screen_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg0_sub_screen_enable);
            return;
        }
        if (attr == MP_QSTR_bg1_sub_screen_enable)
        {
            dest[0] = mp_obj_new_bool(self->bg1_sub_screen_enable);
            return;
        }
        if (attr == MP_QSTR_half_main_screen)
        {
            dest[0] = mp_obj_new_bool(self->half_main_screen);
            return;
        }
        if (attr == MP_QSTR_double_main_screen)
        {
            dest[0] = mp_obj_new_bool(self->double_main_screen);
            return;
        }
        if (attr == MP_QSTR_half_sub_screen)
        {
            dest[0] = mp_obj_new_bool(self->half_sub_screen);
            return;
        }
        if (attr == MP_QSTR_double_sub_screen)
        {
            dest[0] = mp_obj_new_bool(self->double_sub_screen);
            return;
        }
        if (attr == MP_QSTR_add_sub_screen)
        {
            dest[0] = mp_obj_new_bool(self->add_sub_screen);
            return;
        }
        if (attr == MP_QSTR_sub_sub_screen)
        {
            dest[0] = mp_obj_new_bool(self->sub_sub_screen);
            return;
        }
        if (attr == MP_QSTR_fade_enable)
        {
            dest[0] = mp_obj_new_bool(self->fade_enable);
            return;
        }
        if (attr == MP_QSTR_cmath_enable)
        {
            dest[0] = mp_obj_new_bool(self->cmath_enable);
            return;
        }
        if (attr == MP_QSTR_cmath_default)
        {
            dest[0] = mp_obj_new_bool(self->cmath_default);
            return;
        }
        if (attr == MP_QSTR_bg0_main_in_window)
        {
            dest[0] = mp_obj_new_bool(self->bg0_main_in_window);
            return;
        }
        if (attr == MP_QSTR_bg0_main_out_window)
        {
            dest[0] = mp_obj_new_bool(self->bg0_main_out_window);
            return;
        }
        if (attr == MP_QSTR_bg1_main_in_window)
        {
            dest[0] = mp_obj_new_bool(self->bg1_main_in_window);
            return;
        }
        if (attr == MP_QSTR_bg1_main_out_window)
        {
            dest[0] = mp_obj_new_bool(self->bg1_main_out_window);
            return;
        }
        if (attr == MP_QSTR_bg0_sub_in_window)
        {
            dest[0] = mp_obj_new_bool(self->bg0_sub_in_window);
            return;
        }
        if (attr == MP_QSTR_bg0_sub_out_window)
        {
            dest[0] = mp_obj_new_bool(self->bg0_sub_out_window);
            return;
        }
        if (attr == MP_QSTR_bg1_sub_in_window)
        {
            dest[0] = mp_obj_new_bool(self->bg1_sub_in_window);
            return;
        }
        if (attr == MP_QSTR_bg1_sub_out_window)
        {
            dest[0] = mp_obj_new_bool(self->bg1_sub_out_window);
            return;
        }
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Unknown attribute"));
    }
    else
    {
        // Set or delete attribute
        if (dest[1] == MP_OBJ_NULL)
        {
            // We don't support deleting attributes.
            mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Cannot delete attribute"));
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour)
        {
            self->mainscreen_colour = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_subscreen_colour)
        {
            self->subscreen_colour = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_r)
        {
            self->mainscreen_colour = (self->mainscreen_colour & 0b0000011111111111) | ((mp_obj_get_int(dest[1]) & 0x1F) << 11);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_g)
        {
            self->mainscreen_colour = (self->mainscreen_colour & 0b1111100000011111) | ((mp_obj_get_int(dest[1]) & 0x3F) << 5);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_mainscreen_colour_b)
        {
            self->mainscreen_colour = (self->mainscreen_colour & 0b1111111111100000) | ((mp_obj_get_int(dest[1]) & 0x1F) << 0);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_r)
        {
            self->subscreen_colour = (self->subscreen_colour & 0b0000011111111111) | ((mp_obj_get_int(dest[1]) & 0x1F) << 11);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_g)
        {
            self->subscreen_colour = (self->subscreen_colour & 0b1111100000011111) | ((mp_obj_get_int(dest[1]) & 0x3F) << 5);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_subscreen_colour_b)
        {
            self->subscreen_colour = (self->subscreen_colour & 0b1111111111100000) | ((mp_obj_get_int(dest[1]) & 0x1F) << 0);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0scrollh)
        {
            self->bg0scrollh = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1scrollh)
        {
            self->bg1scrollh = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0scrollv)
        {
            self->bg0scrollv = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1scrollv)
        {
            self->bg1scrollv = mp_obj_get_int(dest[1]) & 0xFFFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_screen_fade)
        {
            self->screen_fade = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_main_window_log)
        {
            self->bg0_main_window_log = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_main_window_log)
        {
            self->bg1_main_window_log = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_sub_window_log)
        {
            self->bg0_sub_window_log = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_sub_window_log)
        {
            self->bg1_sub_window_log = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_window_1_left)
        {
            self->window_1_left = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_window_1_right)
        {
            self->window_1_right = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_window_2_left)
        {
            self->window_2_left = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_window_2_right)
        {
            self->window_2_right = mp_obj_get_int(dest[1]) & 0xFF;
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_enable_bg0)
        {
            self->enable_bg0 = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_enable_bg1)
        {
            self->enable_bg1 = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_cmath_enable)
        {
            self->bg0_cmath_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_cmath_enable)
        {
            self->bg0_cmath_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_cmath_enable)
        {
            self->bg1_cmath_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_main_screen_enable)
        {
            self->bg0_main_screen_enable = mp_obj_is_true(dest[1]);
            return;
        }
        if (attr == MP_QSTR_bg1_main_screen_enable)
        {
            self->bg1_main_screen_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_sub_screen_enable)
        {
            self->bg0_sub_screen_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_sub_screen_enable)
        {
            self->bg1_sub_screen_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_half_main_screen)
        {
            self->half_main_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_double_main_screen)
        {
            self->double_main_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_half_sub_screen)
        {
            self->half_sub_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_double_sub_screen)
        {
            self->double_sub_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_add_sub_screen)
        {
            self->add_sub_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_sub_sub_screen)
        {
            self->sub_sub_screen = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_fade_enable)
        {
            self->fade_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_cmath_enable)
        {
            self->cmath_enable = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_cmath_default)
        {
            self->cmath_default = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_main_in_window)
        {
            self->bg0_main_in_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_main_out_window)
        {
            self->bg0_main_out_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_main_in_window)
        {
            self->bg1_main_in_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_main_out_window)
        {
            self->bg1_main_out_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_sub_in_window)
        {
            self->bg0_sub_in_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg0_sub_out_window)
        {
            self->bg0_sub_out_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_sub_in_window)
        {
            self->bg1_sub_in_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        if (attr == MP_QSTR_bg1_sub_out_window)
        {
            self->bg1_sub_out_window = mp_obj_is_true(dest[1]);
            dest[0] = MP_OBJ_NULL;
            return;
        }
        mp_raise_msg(&mp_type_ValueError, MP_ERROR_TEXT("Unknown attribute"));
    }
}

#define AS_565(r, g, b) (((r) << 11) | ((g) << 5) | (b))

STATIC void state_init(state_obj_t *self)
{
    self->mainscreen_colour = AS_565(0, 0, 31);
    self->subscreen_colour = AS_565(31, 0, 0);
    self->enable_bg0 = false;
    self->enable_bg1 = false;
    self->bg0scrollh = 0;
    self->bg0scrollv = 0;
    self->bg1scrollh = 0;
    self->bg1scrollv = 0;
    self->bg0_cmath_enable = false;
    self->bg1_cmath_enable = false;
    self->bg0_main_screen_enable = false;
    self->bg0_sub_screen_enable = false;
    self->bg1_main_screen_enable = false;
    self->bg1_sub_screen_enable = false;
    self->half_main_screen = false;
    self->double_main_screen = false;
    self->half_sub_screen = false;
    self->double_sub_screen = false;
    self->add_sub_screen = false;
    self->sub_sub_screen = false;
    self->fade_enable = false;
    self->screen_fade = 0xFF;
    self->cmath_enable = false;
    self->cmath_default = false;
    self->bg0_main_in_window = true;
    self->bg0_main_out_window = true;
    self->bg0_main_window_log = 0;
    self->bg1_main_in_window = true;
    self->bg1_main_out_window = true;
    self->bg1_main_window_log = 0;
    self->bg0_sub_in_window = true;
    self->bg0_sub_out_window = true;
    self->bg0_sub_window_log = 0;
    self->bg1_sub_in_window = true;
    self->bg1_sub_out_window = true;
    self->bg1_sub_window_log = 0;
    self->window_1_left = 0;
    self->window_1_right = 255;
    self->window_2_left = 0;
    self->window_2_right = 255;
}

STATIC mp_obj_t state_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *args)
{
    mp_arg_check_num(n_args, n_kw, 0, 0, false);
    state_obj_t *self = mp_obj_malloc(state_obj_t, type);
    state_init(self);
    return MP_OBJ_FROM_PTR(self);
}

STATIC mp_obj_t get_bg0()
{
    return mp_obj_new_bytearray_by_ref(sizeof(BG0), &BG0);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(get_bg0_obj, get_bg0);
STATIC mp_obj_t get_bg1()
{
    return mp_obj_new_bytearray_by_ref(sizeof(BG1), &BG1);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(get_bg1_obj, get_bg1);
STATIC mp_obj_t get_sprite_page()
{
    return mp_obj_new_bytearray_by_ref(sizeof(sprites), &sprites);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(get_sprite_page_obj, get_sprite_page);

mp_obj_t sleep_ms;
#define msleep(buf) mp_call_function_n_kw(sleep_ms, 1, 0, ((mp_obj_t[1]){MP_OBJ_NEW_SMALL_INT(buf)}))

void write(unsigned char command, unsigned char *data, int data_len)
{
    cs_off;

    if (command != 0)
    {
        dc_off;
        spi_write(mp_obj_new_bytes(&command, 1));
    }
    if (data_len != 0)
    {
        dc_on;
        spi_write(mp_obj_new_bytes(data, data_len));
    }

    cs_on;
}

void hard_reset(void)
{
    cs_off;

    rst_on;
    msleep(50);
    rst_off;
    msleep(50);
    rst_on;
    msleep(150);

    cs_on;
}

void soft_reset(void)
{
    write(GC9A01_SWRESET, NULL, 0);
    msleep(150);
}

void sleep_mode(bool enable)
{
    if (enable)
    {
        write(GC9A01_SLPIN, NULL, 0);
    }
    else
    {
        write(GC9A01_SLPOUT, NULL, 0);
    }
}

void inversion_mode(bool enable)
{
    if (enable)
        write(GC9A01_INVON, NULL, 0);
    else
        write(GC9A01_INVOFF, NULL, 0);
}

void rotation(int rotation)
{
    unsigned char ROTATIONS[8] = {
        0x48,  // 0 - PORTRAIT
        0x28,  // 1 - LANDSCAPE
        0x88,  // 2 - INVERTED_PORTRAIT
        0xe8,  // 3 - INVERTED_LANDSCAPE
        0x08,  // 4 - PORTRAIT_MIRRORED
        0x68,  // 5 - LANDSCAPE_MIRRORED
        0xc8,  // 6 - INVERTED_PORTRAIT_MIRRORED
        0xa8}; // 7 - INVERTED_LANDSCAPE_MIRRORED
    write(GC9A01_MADCTL, ROTATIONS + (rotation & 0x3), 1);
}

void _set_columns(unsigned short start, unsigned short end)
{
    if (start <= end && end <= 240)
        write(GC9A01_CASET, (unsigned char *)(unsigned short[2]){start, end}, 4);
}

void _set_rows(unsigned short start, unsigned short end)
{
    if (start <= end && end <= 240)
        write(GC9A01_RASET, (unsigned char *)(unsigned short[2]){start, end}, 4);
}

void _set_window(unsigned short x0, unsigned short y0, unsigned short x1, unsigned short y1)
{
    _set_columns(x0, x1);
    _set_rows(y0, y1);
    write(GC9A01_RAMWR, NULL, 0);
}

STATIC mp_obj_t init_display(size_t n_args, const mp_obj_t *args)
{

    if (args[0] == mp_const_none)
    {
        mp_raise_ValueError("SPI object is required.");
    }
    if (args[1] == mp_const_none)
    {
        mp_raise_ValueError("cs pin is required.");
    }
    if (args[2] == mp_const_none)
    {
        mp_raise_ValueError("dc pin is required.");
    }
    if (args[3] == mp_const_none)
    {
        mp_raise_ValueError("rst pin is required.");
    }
    if (args[4] == mp_const_none)
    {
        mp_raise_ValueError("backlight pin is required.");
    }

    SPI = args[0];
    write_fun = mp_load_attr(SPI, MP_QSTR_write);
    CS = args[1];
    cs_on_fun = mp_load_attr(CS, MP_QSTR_on);
    cs_off_fun = mp_load_attr(CS, MP_QSTR_off);
    DC = args[2];
    dc_on_fun = mp_load_attr(DC, MP_QSTR_on);
    dc_off_fun = mp_load_attr(DC, MP_QSTR_off);
    RST = args[3];
    rst_on_fun = mp_load_attr(RST, MP_QSTR_on);
    rst_off_fun = mp_load_attr(RST, MP_QSTR_off);
    BACKLIGHT = args[4];
    backlight_on_fun = mp_load_attr(BACKLIGHT, MP_QSTR_on);
    backlight_off_fun = mp_load_attr(BACKLIGHT, MP_QSTR_off);

    hard_reset();
    msleep(100);

    write(0xEF, NULL, 0);
    write(0xEB, (unsigned char[1]){0x14}, 1);
    write(0xFE, NULL, 0);
    write(0xEF, NULL, 0);
    write(0xEB, (unsigned char[1]){0x14}, 1);
    write(0x84, (unsigned char[1]){0x40}, 1);
    write(0x85, (unsigned char[1]){0xFF}, 1);
    write(0x86, (unsigned char[1]){0xFF}, 1);
    write(0x87, (unsigned char[1]){0xFF}, 1);
    write(0x88, (unsigned char[1]){0x0A}, 1);
    write(0x89, (unsigned char[1]){0x21}, 1);
    write(0x8A, (unsigned char[1]){0x00}, 1);
    write(0x8B, (unsigned char[1]){0x80}, 1);
    write(0x8C, (unsigned char[1]){0x01}, 1);
    write(0x8D, (unsigned char[1]){0x01}, 1);
    write(0x8E, (unsigned char[1]){0xFF}, 1);
    write(0x8F, (unsigned char[1]){0xFF}, 1);
    write(0xB6, (unsigned char[2]){0x00, 0x00}, 2);
    write(0x3A, (unsigned char[1]){0x55}, 1);
    write(0x90, (unsigned char[4]){0x08, 0x08, 0x08, 0x08}, 4);
    write(0xBD, (unsigned char[1]){0x06}, 1);
    write(0xBC, (unsigned char[1]){0x00}, 1);
    write(0xFF, (unsigned char[3]){0x60, 0x01, 0x04}, 3);
    write(0xC3, (unsigned char[1]){0x13}, 1);
    write(0xC4, (unsigned char[1]){0x13}, 1);
    write(0xC9, (unsigned char[1]){0x22}, 1);
    write(0xBE, (unsigned char[1]){0x11}, 1);
    write(0xE1, (unsigned char[2]){0x10, 0x0E}, 2);
    write(0xDF, (unsigned char[3]){0x21, 0x0c, 0x02}, 3);
    write(0xF0, (unsigned char[6]){0x45, 0x09, 0x08, 0x08, 0x26, 0x2A}, 6);
    write(0xF1, (unsigned char[6]){0x43, 0x70, 0x72, 0x36, 0x37, 0x6F}, 6);
    write(0xF2, (unsigned char[6]){0x45, 0x09, 0x08, 0x08, 0x26, 0x2A}, 6);
    write(0xF3, (unsigned char[6]){0x43, 0x70, 0x72, 0x36, 0x37, 0x6F}, 6);
    write(0xED, (unsigned char[2]){0x1B, 0x0B}, 2);
    write(0xAE, (unsigned char[1]){0x77}, 1);
    write(0xCD, (unsigned char[1]){0x63}, 1);
    write(0x70, (unsigned char[9]){0x07, 0x07, 0x04, 0x0E, 0x0F, 0x09, 0x07, 0x08, 0x03}, 9);
    write(0xE8, (unsigned char[1]){0x34}, 1);

    write(
        0x62,
        (unsigned char[12]){0x18, 0x0D, 0x71, 0xED, 0x70, 0x70, 0x18, 0x0F, 0x71, 0xEF, 0x70, 0x70}, 12);

    write(
        0x63,
        (unsigned char[12]){0x18, 0x11, 0x71, 0xF1, 0x70, 0x70, 0x18, 0x13, 0x71, 0xF3, 0x70, 0x70}, 12);

    write(0x64, (unsigned char[7]){0x28, 0x29, 0xF1, 0x01, 0xF1, 0x00, 0x07}, 7);
    write(
        0x66,
        (unsigned char[10]){0x3C, 0x00, 0xCD, 0x67, 0x45, 0x45, 0x10, 0x00, 0x00, 0x00}, 10);

    write(
        0x67,
        (unsigned char[10]){0x00, 0x3C, 0x00, 0x00, 0x00, 0x01, 0x54, 0x10, 0x32, 0x98}, 10);

    write(0x74, (unsigned char[7]){0x10, 0x85, 0x80, 0x00, 0x00, 0x4E, 0x00}, 7);
    write(0x98, (unsigned char[2]){0x3e, 0x07}, 2);
    write(0x35, NULL, 0);
    write(0x21, NULL, 0);
    write(0x11, NULL, 0);
    msleep(120);

    write(0x29, NULL, 0);
    msleep(20);

    rotation(0);

    backlight_on;

    _set_window(110, 110, 130, 130);
    cs_off;
    dc_on;
    return mp_const_none;
}

STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(init_display_obj, 5, 5, init_display);

STATIC mp_obj_t init_spi(mp_obj_t spi)
{
    write_fun = mp_load_attr(spi, MP_QSTR_write);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(init_spi_obj, init_spi);

STATIC mp_obj_t save_state(mp_obj_t state_in)
{
    if (!mp_obj_is_type(state_in, (mp_obj_type_t *)(&state_type)))
    {
        mp_raise_TypeError("argument is not a state");
    }
    state_obj_t *state_local = MP_OBJ_TO_PTR(state_in);
    state = *state_local;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_1(save_state_obj, save_state);

STATIC mp_obj_t load_state()
{
    return MP_OBJ_TO_PTR(&state);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(load_state_obj, load_state);

// This is the entry point and is called when the module is imported
mp_obj_t mpy_init(mp_obj_fun_bc_t *self, size_t n_args, size_t n_kw, mp_obj_t *args)
{
    // This must be first, it sets up the globals dict and other things
    MP_DYNRUNTIME_INIT_ENTRY

    // Make the function available in the module's namespace
    mp_store_global(MP_QSTR_render, MP_OBJ_FROM_PTR(&render_obj));
    mp_store_global(MP_QSTR_load_sprite, MP_OBJ_FROM_PTR(&load_sprite_obj));
    mp_store_global(MP_QSTR_save_sprite, MP_OBJ_FROM_PTR(&save_sprite_obj));
    mp_store_global(MP_QSTR_get_sprite_page, MP_OBJ_FROM_PTR(&get_sprite_page_obj));
    mp_store_global(MP_QSTR_get_bg0, MP_OBJ_FROM_PTR(&get_bg0_obj));
    mp_store_global(MP_QSTR_get_bg1, MP_OBJ_FROM_PTR(&get_bg1_obj));

    mp_store_global(MP_QSTR_blit_sprite, MP_OBJ_FROM_PTR(&blit_sprite_obj));
    mp_store_global(MP_QSTR_blit_bg0, MP_OBJ_FROM_PTR(&blit_bg0_obj));
    mp_store_global(MP_QSTR_blit_bg1, MP_OBJ_FROM_PTR(&blit_bg1_obj));

    mp_store_global(MP_QSTR_init_display, MP_OBJ_FROM_PTR(&init_display_obj));
    // mp_store_global(MP_QSTR_spi, SPI);
    mp_store_global(MP_QSTR_init_spi, MP_OBJ_FROM_PTR(&init_spi_obj));
    mp_store_global(MP_QSTR_load_state, MP_OBJ_FROM_PTR(&load_state_obj));
    mp_store_global(MP_QSTR_save_state, MP_OBJ_FROM_PTR(&save_state_obj));

    mp_obj_t time = mp_import_name(MP_QSTR_time, mp_const_none, MP_OBJ_NEW_SMALL_INT(0));
    sleep_ms = mp_import_from(time, MP_QSTR_sleep_ms);

    // Initialise the sprite type.
    sprite_type.base.type = (void *)&mp_type_type;
    sprite_type.flags = MP_TYPE_FLAG_NONE;
    sprite_type.name = MP_QSTR_Sprite;
    MP_OBJ_TYPE_SET_SLOT(&sprite_type, make_new, sprite_make_new, 0);
    MP_OBJ_TYPE_SET_SLOT(&sprite_type, attr, sprite_attr, 1);

    // Initialise the state type.
    state_type.base.type = (void *)&mp_type_type;
    state_type.flags = MP_TYPE_FLAG_NONE;
    state_type.name = MP_QSTR_State;
    MP_OBJ_TYPE_SET_SLOT(&state_type, make_new, state_make_new, 0);
    MP_OBJ_TYPE_SET_SLOT(&state_type, attr, state_attr, 1);

    // Make the types available on the module.
    mp_store_global(MP_QSTR_Sprite, MP_OBJ_FROM_PTR(&sprite_type));
    mp_store_global(MP_QSTR_State, MP_OBJ_FROM_PTR(&state_type));

    state.base.type = (void *)&state_type;
    state_init(&state);
    for (Sprite *sprite = OAM; sprite < (OAM + SPRITE_COUNT); sprite++)
    {
        sprite->base.type = (void *)&sprite_type;
        sprite_init(sprite);
    }

    // This must be last, it restores the globals dict
    MP_DYNRUNTIME_INIT_EXIT
}
