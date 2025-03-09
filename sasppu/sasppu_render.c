#include "sasppu_fast.h"
#include "stdint.h"
#include "stddef.h"
#include "stdbool.h"

void SASPPU_per_scanline(
    uint8_t x,
    uint8_t y)
{
    uint32_t sprites_indcies[2] = {0, 0};
    for (int i = SPRITE_COUNT - 1; i >= 0; i--)
    {
        Sprite *spr = &SASPPU_oam[i];
        uint8_t flags = spr->flags;
        uint8_t windows = spr->windows;
        int16_t iy = (int16_t)y;

        int16_t spr_height = (int16_t)(spr->height);
        int16_t spr_width = (int16_t)(spr->width);

        bool main_screen_enable = (windows & 0x0F) > 0;
        bool sub_screen_enable = (windows & 0xF0) > 0;

        bool enabled = (flags & SPR_ENABLED) > 0;
        bool priority = (flags & SPR_PRIORITY) > 0;
        // bool flip_x = (flags & SPR_FLIP_X) > 0;
        // bool flip_y = (flags & SPR_FLIP_Y) > 0;
        // bool cmath_enabled = (flags & SPR_C_MATH) > 0;
        bool double_enabled = (flags & SPR_DOUBLE) > 0;

        // If not enabled, skip
        if (!enabled)
        {
            continue;
        }

        // If we've hit the limit, skip
        if ((priority && (sprites_indcies[1] == SPRITE_CACHE)) || (!priority && (sprites_indcies[0] == SPRITE_CACHE)))
        {
            continue;
        }

        bool window_enabled = (main_screen_enable) || (sub_screen_enable);
        bool top_border = spr->y <= iy;
        bool bottom_border = double_enabled ? (spr->y > (iy - (spr_height << 1))) : (spr->y > (iy - (spr_height)));
        bool right_border = spr->x < 240;
        bool left_border = double_enabled ? (spr->x > -(spr_width << 1)) : (spr->x > -(spr_width));

        if (window_enabled && top_border && bottom_border && right_border && left_border)
        {
            if (priority)
            {
                SASPPU_sprite_cache[1][sprites_indcies[1]] = spr;
                sprites_indcies[1] += 1;
            }
            else
            {
                SASPPU_sprite_cache[0][sprites_indcies[0]] = spr;
                sprites_indcies[0] += 1;
            }

            if ((sprites_indcies[1] == SPRITE_CACHE) && (sprites_indcies[0] == SPRITE_CACHE))
            {
                break;
            }
        }
    }
    for (int i = 1; i >= 0; i--)
    {
        if (sprites_indcies[i] < SPRITE_CACHE)
        {
            SASPPU_sprite_cache[i][sprites_indcies[i]] = NULL;
        }
    }
}

void SASPPU_render()
{
    for (int y = 239; y >= 0; y--)
    {
        SASPPU_render_scanline(0, y);
    }
}