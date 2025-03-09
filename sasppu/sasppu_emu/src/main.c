#include <stdint.h>
#include <stdbool.h>

typedef uint16_t uint16x8_t __attribute__((vector_size(16)));
typedef int16_t int16x8_t __attribute__((vector_size(16)));
typedef int16_t mask16x8_t __attribute__((vector_size(16)));

struct Sprite
{
    int16_t x;
    int16_t y;
    uint8_t width;
    uint8_t height;
    uint8_t graphics_x;
    uint8_t graphics_y;
    uint16_t flags;
};

#define SPR_PRIORITY (1 << 0)
#define SPR_FLIP_X (1 << 1)
#define SPR_FLIP_Y (1 << 2)
#define SPR_MAIN_SCREEN (1 << 3)
#define SPR_SUB_SCREEN (1 << 4)
#define SPR_C_MATH (1 << 5)
#define SPR_DOUBL (1 << 6)
#define SPR_MAIN_WINDOW_POW2 (7)
#define SPR_MAIN_WINDOW_LOG1 (1 << 7)
#define SPR_MAIN_WINDOW_LOG2 (1 << 8)
#define SPR_MAIN_WINDOW_LOG3 (1 << 9)
#define SPR_MAIN_WINDOW_LOG4 (1 << 10)
#define SPR_SUB_WINDOW_POW2 (11)
#define SPR_SUB_WINDOW_LOG1 (1 << 11)
#define SPR_SUB_WINDOW_LOG2 (1 << 12)
#define SPR_SUB_WINDOW_LOG3 (1 << 13)
#define SPR_SUB_WINDOW_LOG4 (1 << 14)
#define SPR_ENABLED (1 << 15)

#define WINDOW_A (0b0001)
#define WINDOW_B (0b0010)
#define WINDOW_AB (0b0100)
#define WINDOW_X (0b1000)

struct Background
{
    int16_t scroll_x;
    int16_t scroll_y;
    uint8_t windows;
    uint8_t flags;
};

#define BG_MAIN_SCREEN (1 << 0)
#define BG_SUB_SCREEN (1 << 1)
#define BG_C_MATH (1 << 2)
#define BG_ENABLED (1 << 7)

#define CM_HALF_MAIN_SCREEN (1 << 0)
#define CM_DOUBLE_MAIN_SCREEN (1 << 1)
#define CM_HALF_SUB_SCREEN (1 << 2)
#define CM_DOUBLE_SUB_SCREEN (1 << 3)
#define CM_ADD_SUB_SCREEN (1 << 4)
#define CM_SUB_SUB_SCREEN (1 << 5)
#define CM_FADE (1 << 6)
#define CM_ENABLED (1 << 7)

#define STATE_CM_DEFAULT (1 << 0)

#define BG_WIDTH_POWER (8)
#define BG_HEIGHT_POWER (8)
#define BG_WIDTH (1 << BG_WIDTH_POWER)
#define BG_HEIGHT (1 << BG_HEIGHT_POWER)

#define SPRITE_COUNT (256)
#define SPRITE_CACHE (16)

typedef struct Sprite *SpriteCache[SPRITE_CACHE];
typedef SpriteCache SpriteCaches[2];

#define SPR_WIDTH_POWER (8)
#define SPR_HEIGHT_POWER (8)
#define SPR_WIDTH (1 << SPR_WIDTH_POWER)
#define SPR_HEIGHT (1 << SPR_HEIGHT_POWER)

#define MAP_WIDTH_POWER (6)
#define MAP_HEIGHT_POWER (6)
#define MAP_WIDTH (1 << MAP_WIDTH_POWER)
#define MAP_HEIGHT (1 << MAP_HEIGHT_POWER)

typedef uint16x8_t GraphicsPlane[(BG_WIDTH / 8) * BG_HEIGHT];
typedef uint16x8_t SpritePlane[SPR_HEIGHT][SPR_WIDTH / 8];
typedef struct Sprite SpriteMap[SPRITE_COUNT];
typedef uint16_t BackgroundMap[MAP_HEIGHT][MAP_WIDTH];

volatile uint16_t main_state_mainscreen_colour;
volatile uint16_t main_state_subscreen_colour;
volatile uint8_t main_state_window_1_left;
volatile uint8_t main_state_window_1_right;
volatile uint8_t main_state_window_2_left;
volatile uint8_t main_state_window_2_right;
volatile uint8_t main_state_flags;

volatile struct Background bg0_state;
volatile struct Background bg1_state;

volatile uint8_t cmath_state_screen_fade;
volatile uint8_t cmath_state_flags;

volatile GraphicsPlane background;
volatile SpritePlane sprites;

volatile SpriteMap oam;
volatile BackgroundMap bg0;
volatile BackgroundMap bg1;

typedef void(HandleBgType)(
    struct Background *,
    BackgroundMap *,
    uint16x8_t *,
    uint16x8_t *,
    int16_t,
    int16_t,
    mask16x8_t,
    mask16x8_t);

typedef void(HandleSpriteType)(struct Sprite *, uint16x8_t *, uint16x8_t *, int16_t, int16_t, uint8_t, uint8_t, mask16x8_t, mask16x8_t);

typedef void(HandleCMathType)(uint16x8_t *, uint16x8_t *);

typedef uint16x8_t *(PerPixelType)(uint8_t, uint8_t, SpriteCaches *, HandleBgType *, HandleBgType *, HandleCMathType *);

struct pair
{
    uint16_t a;
    uint16_t d;
    uint16_t e;
    uint16_t b;
};

struct pair handle_bg(
    struct Background *state, // a9
    BackgroundMap *map,       // a10
    uint16x8_t *main_col,     // q0
    uint16x8_t *sub_col,      // q1
    int16_t x,                // a2
    int16_t y,                // a3
    mask16x8_t window_1,      // q2
    mask16x8_t window_2       // q3
)
{
    uintptr_t y_pos = (((uintptr_t)(y + (*state).scroll_y)) >> 3) & ((MAP_HEIGHT)-1);
    uintptr_t x_pos_1 = (((uintptr_t)(x + (*state).scroll_x)) >> 3) & ((MAP_WIDTH)-1);
    uintptr_t x_pos_2 = (x_pos_1 + 1) & ((MAP_WIDTH)-1);
    uintptr_t offset_x = (uintptr_t)((*state).scroll_x & 0x7);
    uintptr_t offset_y = (uintptr_t)((*state).scroll_y & 0x7);
    uint16_t bg0_1_map = map[y_pos][x_pos_1];
    uint16_t bg0_2_map = map[y_pos][x_pos_2];
    struct pair p;
    p.a = bg0_1_map;
    p.b = bg0_2_map;
    return p;
}

#define BG0_ENABLE (1)
#define BG1_ENABLE (1)
#define SPR0_ENABLE (1)
#define SPR1_ENABLE (1)
#define CMATH_ENABLE (1)

static const uint16x8_t incr = {0, 1, 2, 3, 4, 5, 6, 7};

static const uint16_t thing00;
static const uint16_t thing01;
static const uint16_t thing02;
static const uint16_t thing03;
static const uint16_t thing04;
static const uint16_t thing05;
static const uint16_t thing06;
static const uint16_t thing07;
uint16_t *things[8];

uint32_t
large()
{
    things[0] = &thing00;
    things[1] = &thing01;
    things[2] = &thing02;
    things[3] = &thing03;
    things[4] = &thing04;
    things[5] = &thing05;
    things[6] = &thing06;
    things[7] = &thing07;
    return 123758349;
}

uint16x8_t *per_pixel(
    uint8_t x,
    uint8_t y,
    SpriteCaches *sprite_caches,
    HandleBgType *handle_bg0,
    HandleBgType *handle_bg1,
    HandleCMathType *handle_cmath)
{
    // main_col = q0
    uint16_t main_col =
        main_state_mainscreen_colour;
    // sub_col = q1
    uint16_t sub_col = main_state_subscreen_colour;

    // x_window = q3
    uint16x8_t x_window = incr + x;
    // window_1 = q2
    mask16x8_t window_1 = (x_window >= (uint16_t)main_state_window_1_left) & (x_window <= (uint16_t)main_state_window_1_right);
    // window_2 = q3
    mask16x8_t window_2 = (x_window >= (uint16_t)main_state_window_2_left) & (x_window <= (uint16_t)main_state_window_2_right);

    // q0, q1, q2, q3, q4, q5, q6, q7 -> q0, q1
    if BG0_ENABLE
    {
        handle_bg0(
            &bg0_state,
            &bg0,
            &main_col,
            &sub_col,
            (int16_t)x,
            (int16_t)y,
            window_1,
            window_2);
    }

    if SPR0_ENABLE
    {
        for (struct Sprite **spr = sprite_caches[0]; spr < sprite_caches[0][SPRITE_CACHE] && ((*spr) != 0); spr++)
        {
            spr;
        }
    }

    if BG1_ENABLE
    {
        handle_bg1(
            &bg1_state,
            &bg1,
            &main_col,
            &sub_col,
            (int16_t)x,
            (int16_t)y,
            window_1,
            window_2);
    }

    if SPR1_ENABLE
    {
        for (struct Sprite **spr = sprite_caches[1]; spr < sprite_caches[1][SPRITE_CACHE] && ((*spr) != 0); spr++)
        {
            spr;
        }
    }

    if CMATH_ENABLE
    {
        handle_cmath(&main_col, &sub_col);
    }
    else
    {
        // main_col = ((main_col & u16x8::splat(0b0111111111100000)) << 1) | (main_col & u16x8::splat(0b00011111));
    }

    return main_col;
}