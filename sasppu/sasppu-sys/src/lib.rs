#![feature(portable_simd)]
#![no_std]

use core::simd::prelude::*;

use seq_macro::seq;

#[derive(Debug, Clone, Copy)]
pub struct Sprite {
    pub x:          i16,
    pub y:          i16,
    pub width:      u8,
    pub height:     u8,
    pub graphics_x: u8,
    pub graphics_y: u8,
    pub flags:      u16,
}

impl Sprite {
    pub const fn new() -> Self {
        Sprite {
            x:          0,
            y:          0,
            width:      8,
            height:     8,
            graphics_x: 0,
            graphics_y: 0,
            flags:      0,
        }
    }
}

impl Default for Sprite {
    fn default() -> Self {
        Self::new()
    }
}

pub const SPR_ENABLED: u16 = 1 << 0;
pub const SPR_PRIORITY: u16 = 1 << 1;
pub const SPR_FLIP_X: u16 = 1 << 2;
pub const SPR_FLIP_Y: u16 = 1 << 3;
pub const SPR_MAIN_SCREEN: u16 = 1 << 4;
pub const SPR_SUB_SCREEN: u16 = 1 << 5;
pub const SPR_C_MATH: u16 = 1 << 6;
pub const SPR_DOUBLE: u16 = 1 << 7;
pub const SPR_MAIN_WINDOW_POW2: u16 = 8;
pub const SPR_MAIN_WINDOW_LOG1: u16 = 1 << 8;
pub const SPR_MAIN_WINDOW_LOG2: u16 = 1 << 9;
pub const SPR_MAIN_WINDOW_LOG3: u16 = 1 << 10;
pub const SPR_MAIN_WINDOW_LOG4: u16 = 1 << 11;
pub const SPR_SUB_WINDOW_POW2: u16 = 12;
pub const SPR_SUB_WINDOW_LOG1: u16 = 1 << 12;
pub const SPR_SUB_WINDOW_LOG2: u16 = 1 << 13;
pub const SPR_SUB_WINDOW_LOG3: u16 = 1 << 14;
pub const SPR_SUB_WINDOW_LOG4: u16 = 1 << 15;

pub const WINDOW_A: u16 = 0b0001;
pub const WINDOW_B: u16 = 0b0010;
pub const WINDOW_AB: u16 = 0b0100;
pub const WINDOW_X: u16 = 0b1000;

#[derive(Debug, Clone, Copy)]
pub struct Background {
    pub scroll_x:           i16,
    pub scroll_y:           i16,
    pub main_window_log:    u8,
    pub sub_window_log:     u8,
    pub cmath_enable:       bool,
    pub main_screen_enable: bool,
    pub sub_screen_enable:  bool,
    pub enable:             bool,
}

impl Background {
    pub const fn new() -> Self {
        Background {
            scroll_x:           0,
            scroll_y:           0,
            main_window_log:    0xF,
            sub_window_log:     0xF,
            cmath_enable:       false,
            main_screen_enable: false,
            sub_screen_enable:  false,
            enable:             false,
        }
    }
}

impl Default for Background {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy)]
pub struct ColorMath {
    pub screen_fade:        u8,
    pub half_main_screen:   bool,
    pub double_main_screen: bool,
    pub half_sub_screen:    bool,
    pub double_sub_screen:  bool,
    pub add_sub_screen:     bool,
    pub sub_sub_screen:     bool,
    pub fade_enable:        bool,
    pub cmath_enable:       bool,
}

impl ColorMath {
    pub const fn new() -> Self {
        ColorMath {
            screen_fade:        0,
            half_main_screen:   false,
            double_main_screen: false,
            half_sub_screen:    false,
            double_sub_screen:  false,
            add_sub_screen:     false,
            sub_sub_screen:     false,
            fade_enable:        false,
            cmath_enable:       false,
        }
    }
}

impl Default for ColorMath {
    fn default() -> Self {
        Self::new()
    }
}

#[derive(Debug, Clone, Copy)]
pub struct State {
    pub mainscreen_colour: u16,
    pub subscreen_colour:  u16,
    pub cmath_default:     bool,

    // windowing
    pub window_1_left:  u8,
    pub window_1_right: u8,
    pub window_2_left:  u8,
    pub window_2_right: u8,
}

impl State {
    pub const fn new() -> Self {
        State {
            mainscreen_colour: 0,
            subscreen_colour:  0,
            cmath_default:     false,
            // windowing
            window_1_left:     0,
            window_1_right:    255,
            window_2_left:     0,
            window_2_right:    255,
        }
    }
}

impl Default for State {
    fn default() -> Self {
        Self::new()
    }
}

pub const BG_WIDTH_POWER: usize = 8;
pub const BG_HEIGHT_POWER: usize = 8;
pub const BG_WIDTH: usize = 1 << BG_WIDTH_POWER;
pub const BG_HEIGHT: usize = 1 << BG_HEIGHT_POWER;

pub const SPRITE_COUNT: usize = 256;
pub const SPRITE_CACHE: usize = 16;

pub type SpriteCache<'a> = [Option<&'a Sprite>; SPRITE_CACHE];
pub type SpriteCaches<'a> = [SpriteCache<'a>; 2];

pub const SPR_WIDTH_POWER: usize = 8;
pub const SPR_HEIGHT_POWER: usize = 8;
pub const SPR_WIDTH: usize = 1 << SPR_WIDTH_POWER;
pub const SPR_HEIGHT: usize = 1 << SPR_HEIGHT_POWER;

pub const MAP_WIDTH_POWER: usize = 6;
pub const MAP_HEIGHT_POWER: usize = 6;
pub const MAP_WIDTH: usize = 1 << MAP_WIDTH_POWER;
pub const MAP_HEIGHT: usize = 1 << MAP_HEIGHT_POWER;

pub type GraphicsPlane = [u16x8; (BG_WIDTH / 8) * BG_HEIGHT];
pub type SpritePlane = [[u16x8; SPR_WIDTH / 8]; SPR_HEIGHT];
pub type SpriteMap = [Sprite; SPRITE_COUNT];
pub type BackgroundMap = [[u16; MAP_WIDTH]; MAP_HEIGHT];

pub struct SASPPU {
    pub main_state:  State,
    pub bg0_state:   Background,
    pub bg1_state:   Background,
    pub cmath_state: ColorMath,

    pub oam: SpriteMap,
    pub bg0: BackgroundMap,
    pub bg1: BackgroundMap,

    pub background: GraphicsPlane,
    pub sprites:    SpritePlane,
}

impl Default for SASPPU {
    fn default() -> Self {
        Self::new()
    }
}

macro_rules! window_logic_window {
    (0, $window_1:expr, $window_2:expr) => {
        mask16x8::splat(false)
    };
    (1, $window_1:expr, $window_2:expr) => {
        ($window_1 & $window_2)
    };
}
macro_rules! window_macro {
    ($a:tt, $b:tt, $c:tt, $d:tt, $window_1:ident, $window_2:ident) => {
        window_logic_window!($a, $window_1, !$window_2)
            | window_logic_window!($b, !$window_1, $window_2)
            | window_logic_window!($c, $window_1, $window_2)
            | window_logic_window!($d, !$window_1, !$window_2)
    };
}

#[inline]
fn get_window(logic: u8, window_1: mask16x8, window_2: mask16x8) -> mask16x8 {
    match logic & 0xF {
        0x0 => window_macro!(0, 0, 0, 0, window_1, window_2),
        0x1 => window_macro!(1, 0, 0, 0, window_1, window_2),
        0x2 => window_macro!(0, 1, 0, 0, window_1, window_2),
        0x3 => window_macro!(1, 1, 0, 0, window_1, window_2),
        0x4 => window_macro!(0, 0, 1, 0, window_1, window_2),
        0x5 => window_macro!(1, 0, 1, 0, window_1, window_2),
        0x6 => window_macro!(0, 1, 1, 0, window_1, window_2),
        0x7 => window_macro!(1, 1, 1, 0, window_1, window_2),
        0x8 => window_macro!(0, 0, 0, 1, window_1, window_2),
        0x9 => window_macro!(1, 0, 0, 1, window_1, window_2),
        0xA => window_macro!(0, 1, 0, 1, window_1, window_2),
        0xB => window_macro!(1, 1, 0, 1, window_1, window_2),
        0xC => window_macro!(0, 0, 1, 1, window_1, window_2),
        0xD => window_macro!(1, 0, 1, 1, window_1, window_2),
        0xE => window_macro!(0, 1, 1, 1, window_1, window_2),
        0xF => window_macro!(1, 1, 1, 1, window_1, window_2),
        _ => unreachable!(),
    }
}

#[inline]
fn swimzleoo(a: u16x8, b: u16x8, offset: usize) -> u16x8 {
    match offset {
        0 => a,
        1 => simd_swizzle!(a, b, [1, 2, 3, 4, 5, 6, 7, 8]),
        2 => simd_swizzle!(a, b, [2, 3, 4, 5, 6, 7, 8, 9]),
        3 => simd_swizzle!(a, b, [3, 4, 5, 6, 7, 8, 9, 10]),
        4 => simd_swizzle!(a, b, [4, 5, 6, 7, 8, 9, 10, 11]),
        5 => simd_swizzle!(a, b, [5, 6, 7, 8, 9, 10, 11, 12]),
        6 => simd_swizzle!(a, b, [6, 7, 8, 9, 10, 11, 12, 13]),
        7 => simd_swizzle!(a, b, [7, 8, 9, 10, 11, 12, 13, 14]),
        _ => unreachable!(),
    }
}

#[inline]
fn handle_bg<
    const CMATH_ENABLE: bool,
    const MAIN_SCREEN_ENABLE: bool,
    const SUB_SCREEN_ENABLE: bool,
    const MAIN_SCREEN_WINDOW_0: bool,
    const MAIN_SCREEN_WINDOW_15: bool,
    const SUB_SCREEN_WINDOW_0: bool,
    const SUB_SCREEN_WINDOW_15: bool,
>(
    state: &Background,  // a9
    map: &BackgroundMap, // a10
    graphics: &GraphicsPlane,
    main_col: &mut u16x8, // q0
    sub_col: &mut u16x8,  // q1
    x: i16,               // a2
    y: i16,               // a3
    window_1: mask16x8,   // q2
    window_2: mask16x8,   // q3
) {
    let y_pos = (((y + state.scroll_y) as usize) >> 3) & ((MAP_HEIGHT) - 1);
    let x_pos_1 = (((x + state.scroll_x) as usize) >> 3) & ((MAP_WIDTH) - 1);
    let x_pos_2 = (x_pos_1 + 1) & ((MAP_WIDTH) - 1);
    let offset_x = ((x + state.scroll_x) & 0x7u16 as i16) as usize;
    let offset_y = ((y + state.scroll_y) & 0x7u16 as i16) as usize;
    let bg0_1_map = map[y_pos][x_pos_1]; // -> q4
    let bg0_1 = if (bg0_1_map & 0b10) > 0 {
        graphics[(bg0_1_map >> 3) as usize + ((7 - offset_y) * (BG_WIDTH >> 3))]
    } else {
        graphics[(bg0_1_map >> 3) as usize + (offset_y * (BG_WIDTH >> 3))]
    }; // -> q4
    let bg0_1: Simd<u16, 8> = if (bg0_1_map & 0b01) > 0 {
        bg0_1.reverse()
    } else {
        bg0_1
    }; // -> q4
    let bg0_2_map = map[y_pos][x_pos_2]; // -> q5
    let bg0_2 = if (bg0_2_map & 0b10) > 0 {
        graphics[(bg0_2_map >> 3) as usize + ((7 - offset_y) * (BG_WIDTH >> 3))]
    } else {
        graphics[(bg0_2_map >> 3) as usize + (offset_y * (BG_WIDTH >> 3))]
    }; // -> q5
    let bg0_2 = if (bg0_2_map & 0b01) > 0 {
        bg0_2.reverse()
    } else {
        bg0_2
    }; // -> q5
    let mut bg0 = swimzleoo(bg0_1, bg0_2, offset_x); // q4, q5 -> q4

    if CMATH_ENABLE {
        bg0 |= u16x8::splat(0x8000); // q5; q4, q5 -> q4
    }

    let main_window = if MAIN_SCREEN_WINDOW_0 {
        // -> q5
        mask16x8::splat(false) // -> q5
    } else if MAIN_SCREEN_WINDOW_15 {
        mask16x8::splat(true) // -> q5
    } else {
        get_window(state.main_window_log, window_1, window_2) // q2, q3, q5, q6, q7 -> q5
    } & bg0.simd_ne(u16x8::splat(0)); // q6; q4, q6 -> q6; q5, q6 -> q5

    if MAIN_SCREEN_ENABLE {
        *main_col = main_window.select(bg0, *main_col); // q0, q4, q5 -> q0
    }

    let sub_window = if SUB_SCREEN_WINDOW_0 {
        // -> q5
        mask16x8::splat(false) // -> q5
    } else if SUB_SCREEN_WINDOW_15 {
        mask16x8::splat(true) // -> q5
    } else {
        get_window(state.sub_window_log, window_1, window_2) // q2, q3, q5, q6, q7 -> q5
    } & bg0.simd_ne(u16x8::splat(0)); // q6; q4, q6 -> q6; q5, q6 -> q5

    if SUB_SCREEN_ENABLE {
        *sub_col = sub_window.select(bg0, *sub_col); // q1, q4, q5 -> q1
    }
}

macro_rules! generate_handle_bgs {
    ($consts:expr) => {
        handle_bg::<
            { ($consts) & 0b1000000 > 0 },
            { ($consts) & 0b0100000 > 0 },
            { ($consts) & 0b0010000 > 0 },
            { ($consts) & 0b0001000 > 0 },
            { ($consts) & 0b0000100 > 0 },
            { ($consts) & 0b0000010 > 0 },
            { ($consts) & 0b0000001 > 0 },
        >
    };
}

type HandleBgType = fn(
    &Background,
    &BackgroundMap,
    &GraphicsPlane,
    &mut u16x8,
    &mut u16x8,
    i16,
    i16,
    mask16x8,
    mask16x8,
);

seq!(N in 0..128 {
static HANDLE_BG_LOOKUP: [HandleBgType; 128] =
    [
        #(
        generate_handle_bgs!(N),
        )*
    ];
});

#[inline]
fn select_correct_handle_bg(state: &Background) -> HandleBgType {
    let lookup = (if state.cmath_enable { 0b1000000 } else { 0 })
        | (if state.main_screen_enable {
            0b100000
        } else {
            0
        })
        | (if state.sub_screen_enable { 0b10000 } else { 0 })
        | (if state.main_window_log == 0 {
            0b1000
        } else {
            0
        })
        | (if state.main_window_log == 15 {
            0b100
        } else {
            0
        })
        | (if state.sub_window_log == 0 { 0b10 } else { 0 })
        | (if state.sub_window_log == 15 { 0b1 } else { 0 });
    HANDLE_BG_LOOKUP[lookup]
}

#[inline]
fn handle_sprite<
    const THIS_SPR_FLIP_X: bool,
    const THIS_SPR_FLIP_Y: bool,
    const THIS_SPR_MAIN_SCREEN: bool,
    const THIS_SPR_SUB_SCREEN: bool,
    const THIS_SPR_C_MATH: bool,
    const THIS_SPR_DOUBLE: bool,
>(
    sprite: &Sprite,
    graphics: &SpritePlane,
    main_col: &mut u16x8, // q0
    sub_col: &mut u16x8,  // q1
    x: i16,
    y: i16,
    this_spr_main_screen_window: u8,
    this_spr_sub_screen_window: u8,
    window_1: mask16x8, // q2
    window_2: mask16x8, // q3
) {
    let sprite_width = if THIS_SPR_DOUBLE {
        sprite.width << 1
    } else {
        sprite.width
    };
    let mut offset_x = x - sprite.x;
    if offset_x >= -7 && offset_x < sprite_width as i16 {
        if THIS_SPR_FLIP_X {
            offset_x = sprite_width as i16 - offset_x - 1;
        }
        let mut offset_y = y - sprite.y;
        if THIS_SPR_FLIP_Y {
            offset_y = sprite_width as i16 - offset_y - 1;
        }
        let mut offset_y = offset_y as usize;
        if THIS_SPR_DOUBLE {
            offset_x >>= 1;
            offset_y >>= 1;
        }
        let x_pos_1 = (offset_x
            & if THIS_SPR_DOUBLE {
                0xFFFCu16
            } else {
                0xFFF8u16
            } as i16) as isize;
        let x_pos_2 = if THIS_SPR_FLIP_X {
            x_pos_1 - 8
        } else {
            x_pos_1 + 8
        };
        let offset = ((8 - (sprite.x & 0x7i16)) % 8) as usize;
        let mut spr_1 = if x_pos_1 >= sprite.width as isize || x_pos_1 < 0 {
            // q4
            u16x8::splat(0)
        } else {
            graphics[offset_y + sprite.graphics_y as usize]
                [(x_pos_1 as usize >> 3) + sprite.graphics_x as usize]
        };
        let mut spr_2 = if x_pos_2 >= sprite.width as isize || x_pos_2 < 0 {
            // q5
            u16x8::splat(0)
        } else {
            graphics[offset_y + sprite.graphics_y as usize]
                [(x_pos_2 as usize >> 3) + sprite.graphics_x as usize]
        };
        if THIS_SPR_DOUBLE {
            if x_pos_1 & 0x4 == 0 {
                if THIS_SPR_FLIP_X {
                    spr_1 = spr_1.interleave(spr_1).0;
                    spr_2 = spr_2.interleave(spr_2).1;
                } else {
                    (spr_1, spr_2) = spr_1.interleave(spr_1);
                }
            } else if THIS_SPR_FLIP_X {
                (spr_2, spr_1) = spr_1.interleave(spr_1);
            } else {
                spr_1 = spr_1.interleave(spr_1).1;
                spr_2 = spr_2.interleave(spr_2).0;
            }
        }
        if THIS_SPR_FLIP_X {
            (spr_1, spr_2) = (spr_1.reverse(), spr_2.reverse());
        }
        let mut spr_col = swimzleoo(spr_1, spr_2, offset); // q4
        if THIS_SPR_C_MATH {
            spr_col |= u16x8::splat(0x8000);
        }
        let main_window = get_window(this_spr_main_screen_window, window_1, window_2) // q5, q6, q7 -> q5
            & spr_col.simd_ne(u16x8::splat(0));
        if THIS_SPR_MAIN_SCREEN {
            *main_col = main_window.select(spr_col, *main_col);
        }
        let sub_window = get_window(this_spr_sub_screen_window, window_1, window_2) // q5, q6, q7 -> q5
            & spr_col.simd_ne(u16x8::splat(0));
        if THIS_SPR_SUB_SCREEN {
            *sub_col = sub_window.select(spr_col, *sub_col);
        }
    }
}

macro_rules! generate_handle_sprites {
    ($consts:expr) => {
        handle_sprite::<
            { (((($consts) as u16) & 0b00000000000001) > 0) },
            { (((($consts) as u16) & 0b00000000000010) > 0) },
            { (((($consts) as u16) & 0b00000000000100) > 0) },
            { (((($consts) as u16) & 0b00000000001000) > 0) },
            { (((($consts) as u16) & 0b00000000010000) > 0) },
            { (((($consts) as u16) & 0b00000000100000) > 0) },
        >
    };
}

type HandleSpriteType =
    fn(&Sprite, &SpritePlane, &mut u16x8, &mut u16x8, i16, i16, u8, u8, mask16x8, mask16x8);

seq!(N in 0..64 {
static HANDLE_SPRITE_LOOKUP: [HandleSpriteType; 64] =
    [
        #(
        generate_handle_sprites!(N),
        )*
    ];
});

#[inline]
fn select_correct_handle_sprite(state: &Sprite) -> HandleSpriteType {
    let lookup = (state.flags >> 2) & 0x3F;
    HANDLE_SPRITE_LOOKUP[lookup as usize]
}

macro_rules! split_main {
    ($main_col:ident, $mask:ident) => {{
        let main_r = (*$main_col << 1) & $mask;
        let main_g = (*$main_col << 6) & $mask;
        let main_b = (*$main_col << 11); //& $mask;
        (main_r, main_g, main_b)
    }};
}

macro_rules! double_screen {
    ($main_r:ident, $main_g:ident, $main_b:ident) => {
        $main_r = $main_r.saturating_add($main_r);
        $main_g = $main_r.saturating_add($main_g);
        $main_b = $main_r.saturating_add($main_b);
    };
}

macro_rules! halve_screen {
    ($main_r:ident, $main_g:ident, $main_b:ident) => {
        $main_r >>= 1;
        $main_g >>= 1;
        $main_b >>= 1;
    };
}

macro_rules! add_screens {
    ($main_r:ident, $main_g:ident, $main_b:ident, $sub_r:ident, $sub_g:ident, $sub_b:ident) => {
        $main_r = $main_r.saturating_add($sub_r);
        $main_g = $main_g.saturating_add($sub_g);
        $main_b = $main_b.saturating_add($sub_b);
    };
}

macro_rules! sub_screens {
    ($main_r:ident, $main_g:ident, $main_b:ident, $sub_r:ident, $sub_g:ident, $sub_b:ident) => {
        $main_r = $main_r.saturating_sub($sub_r);
        $main_g = $main_g.saturating_sub($sub_g);
        $main_b = $main_b.saturating_sub($sub_b);
    };
}

#[inline]
fn handle_cmath<
    const HALF_MAIN_SCREEN: bool,
    const DOUBLE_MAIN_SCREEN: bool,
    const HALF_SUB_SCREEN: bool,
    const DOUBLE_SUB_SCREEN: bool,
    const ADD_SUB_SCREEN: bool,
    const SUB_SUB_SCREEN: bool,
    const FADE_ENABLE: bool,
    const CMATH_ENABLE: bool,
>(
    cmath_state: &ColorMath,
    main_col: &mut u16x8, // q0
    sub_col: &mut u16x8,  // q1
) {
    let use_cmath = mask16x8::splat(CMATH_ENABLE) & main_col.simd_ge(u16x8::splat(0x8000));
    if FADE_ENABLE || use_cmath.any() {
        let mask = u16x8::splat(0b1111100000000000);
        let (mut main_r, mut main_g, mut main_b) = split_main!(main_col, mask);
        if use_cmath.any() {
            let (mut sub_r, mut sub_g, mut sub_b) = split_main!(sub_col, mask);

            let main_r_bak = main_r;
            let main_g_bak = main_g;
            let main_b_bak = main_b;

            if DOUBLE_MAIN_SCREEN {
                double_screen!(main_r, main_g, main_b);
            }
            if HALF_MAIN_SCREEN {
                halve_screen!(main_r, main_g, main_b);
            }
            if DOUBLE_SUB_SCREEN {
                double_screen!(sub_r, sub_g, sub_b);
            }
            if HALF_SUB_SCREEN {
                halve_screen!(sub_r, sub_g, sub_b);
            }
            if ADD_SUB_SCREEN {
                add_screens!(main_r, main_g, main_b, sub_r, sub_g, sub_b);
            }
            if SUB_SUB_SCREEN {
                sub_screens!(main_r, main_g, main_b, sub_r, sub_g, sub_b);
            }

            main_r = use_cmath.select(main_r, main_r_bak);
            main_g = use_cmath.select(main_g, main_g_bak);
            main_b = use_cmath.select(main_b, main_b_bak);
        }
        if FADE_ENABLE {
            let fade = u16x8::splat(cmath_state.screen_fade as u16);
            main_r = (main_r * fade) >> 8;
            main_g = (main_g * fade) >> 8;
            main_b = (main_b * fade) >> 8;
        }
        *main_col = (main_r) | (main_g >> 5) | (main_b >> 11);
    } else {
        *main_col = ((*main_col & u16x8::splat(0b0111111111100000)) << 1)
            | (*main_col & u16x8::splat(0b00011111));
    }
}

macro_rules! generate_handle_cmaths {
    ($consts:expr) => {
        handle_cmath::<
            { ($consts) & 0b00000001 > 0 },
            { ($consts) & 0b00000010 > 0 },
            { ($consts) & 0b00000100 > 0 },
            { ($consts) & 0b00001000 > 0 },
            { ($consts) & 0b00010000 > 0 },
            { ($consts) & 0b00100000 > 0 },
            { ($consts) & 0b01000000 > 0 },
            { ($consts) & 0b10000000 > 0 },
        >
    };
}

type HandleCMathType = fn(&ColorMath, &mut u16x8, &mut u16x8);

seq!(N in 0..256 {
static HANDLE_CMATH_LOOKUP: [HandleCMathType; 256] =
    [
        #(
        generate_handle_cmaths!(N),
        )*
    ];
});

#[inline]
fn select_correct_handle_cmaths(state: &ColorMath) -> HandleCMathType {
    let lookup = (if state.cmath_enable { 0b10000000 } else { 0 })
        | (if state.fade_enable { 0b01000000 } else { 0 })
        | (if state.sub_sub_screen { 0b00100000 } else { 0 })
        | (if state.add_sub_screen { 0b00010000 } else { 0 })
        | (if state.double_sub_screen {
            0b00001000
        } else {
            0
        })
        | (if state.half_sub_screen { 0b00000100 } else { 0 })
        | (if state.double_main_screen {
            0b00000010
        } else {
            0
        })
        | (if state.half_main_screen {
            0b00000001
        } else {
            0
        });
    HANDLE_CMATH_LOOKUP[lookup as usize]
}

macro_rules! generate_per_pixels {
    ($consts:expr) => {
        SASPPU::per_pixel::<
            { ($consts) & 0b00001 > 0 },
            { ($consts) & 0b00010 > 0 },
            { ($consts) & 0b00100 > 0 },
            { ($consts) & 0b01000 > 0 },
            { ($consts) & 0b10000 > 0 },
        >
    };
}

type PerPixelType =
    fn(&SASPPU, u8, u8, &SpriteCaches, HandleBgType, HandleBgType, HandleCMathType) -> u16x8;

seq!(N in 0..32 {
static PER_PIXEL_LOOKUP: [PerPixelType; 32] =
    [
        #(
        generate_per_pixels!(N),
        )*
    ];
});

impl SASPPU {
    #[inline]
    fn per_pixel<
        const BG0_ENABLE: bool,
        const BG1_ENABLE: bool,
        const SPR0_ENABLE: bool,
        const SPR1_ENABLE: bool,
        const CMATH_ENABLE: bool,
    >(
        &self,
        x: u8,
        y: u8,
        sprite_caches: &SpriteCaches,
        handle_bg0: HandleBgType,
        handle_bg1: HandleBgType,
        handle_cmath: HandleCMathType,
    ) -> u16x8 {
        // main_col = q0
        let mut main_col = u16x8::splat(
            self.main_state.mainscreen_colour | (self.main_state.cmath_default as u16) << 15,
        );
        // sub_col = q1
        let mut sub_col = u16x8::splat(self.main_state.subscreen_colour);

        // x_window = q3
        let x_window = u16x8::from_array([0, 1, 2, 3, 4, 5, 6, 7]) + u16x8::splat(x as u16);
        // window_1 = q2
        let window_1 = (x_window.simd_gt(u16x8::splat(self.main_state.window_1_left as u16))
            | x_window.simd_eq(u16x8::splat(self.main_state.window_1_left as u16)))
            & x_window.simd_lt(u16x8::splat(self.main_state.window_1_right as u16));
        // window_2 = q3
        let window_2 = (x_window.simd_gt(u16x8::splat(self.main_state.window_2_left as u16))
            | x_window.simd_eq(u16x8::splat(self.main_state.window_2_left as u16)))
            & x_window.simd_lt(u16x8::splat(self.main_state.window_2_right as u16));

        // q0, q1, q2, q3, q4, q5, q6, q7 -> q0, q1
        if BG0_ENABLE {
            handle_bg0(
                &self.bg0_state,
                &self.bg0,
                &self.background,
                &mut main_col,
                &mut sub_col,
                x as i16,
                y as i16,
                window_1,
                window_2,
            );
        }

        if SPR0_ENABLE {
            for spr in sprite_caches[0]
                .iter()
                .take_while(|x| x.is_some())
                .map(|x| x.unwrap())
            {
                select_correct_handle_sprite(spr)(
                    spr,
                    &self.sprites,
                    &mut main_col,
                    &mut sub_col,
                    x as i16,
                    y as i16,
                    ((spr.flags >> SPR_MAIN_WINDOW_POW2) & 0xF) as u8,
                    ((spr.flags >> SPR_SUB_WINDOW_POW2) & 0xF) as u8,
                    window_1,
                    window_2,
                )
            }
        }

        if BG1_ENABLE {
            handle_bg1(
                &self.bg1_state,
                &self.bg1,
                &self.background,
                &mut main_col,
                &mut sub_col,
                x as i16,
                y as i16,
                window_1,
                window_2,
            );
        }

        if SPR1_ENABLE {
            for spr in sprite_caches[1]
                .iter()
                .take_while(|x| x.is_some())
                .map(|x| x.unwrap())
            {
                select_correct_handle_sprite(spr)(
                    spr,
                    &self.sprites,
                    &mut main_col,
                    &mut sub_col,
                    x as i16,
                    y as i16,
                    ((spr.flags >> SPR_MAIN_WINDOW_POW2) & 0xF) as u8,
                    ((spr.flags >> SPR_SUB_WINDOW_POW2) & 0xF) as u8,
                    window_1,
                    window_2,
                )
            }
        }

        if CMATH_ENABLE {
            handle_cmath(&self.cmath_state, &mut main_col, &mut sub_col);
        } else {
            main_col = ((main_col & u16x8::splat(0b0111111111100000)) << 1)
                | (main_col & u16x8::splat(0b00011111));
        }

        main_col
    }

    #[inline]
    fn select_correct_per_pixel(&self, caches: &SpriteCaches) -> PerPixelType {
        let lookup = (if self.bg0_state.enable { 0b00001 } else { 0 })
            | (if self.bg1_state.enable { 0b00010 } else { 0 })
            | (if caches[0][0].is_some() { 0b00100 } else { 0 })
            | (if caches[1][0].is_some() { 0b01000 } else { 0 })
            | (if self.cmath_state.fade_enable || self.cmath_state.cmath_enable {
                0b10000
            } else {
                0
            });
        PER_PIXEL_LOOKUP[lookup as usize]
    }

    fn per_scanline<'a>(&'a self, y: u8, sprite_caches: &mut SpriteCaches<'a>) {
        let mut sprites_indcies = [0; 2];
        for spr in self.oam.iter() {
            let flags = spr.flags;
            if flags & SPR_ENABLED == 0 {
                continue;
            }
            if (flags & SPR_PRIORITY > 0 && sprites_indcies[1] == SPRITE_CACHE)
                || (flags & SPR_PRIORITY == 0 && sprites_indcies[0] == SPRITE_CACHE)
            {
                continue;
            }
            if (((flags & SPR_MAIN_SCREEN > 0) && ((flags & (0b1111 << SPR_MAIN_WINDOW_POW2)) > 0))
                || ((flags & SPR_SUB_SCREEN > 0)
                    && ((flags & (0b1111 << SPR_SUB_WINDOW_POW2)) > 0)))
                && (y as i16 >= spr.y)
                && (((flags & SPR_DOUBLE > 0) && ((y as i16) < ((spr.height as i16) << 1) + spr.y))
                    || ((y as i16) < (spr.height as i16 + spr.y)))
                && (spr.x < 240)
                && (((flags & SPR_DOUBLE > 0) && (spr.x > -((spr.width as i16) << 1)))
                    || (spr.x > -(spr.width as i16)))
            {
                if flags & SPR_PRIORITY > 0 {
                    sprite_caches[1][sprites_indcies[1]] = Some(spr);
                    sprites_indcies[1] += 1;
                } else {
                    sprite_caches[0][sprites_indcies[0]] = Some(spr);
                    sprites_indcies[0] += 1;
                }
                if sprites_indcies.iter().all(|x| *x == SPRITE_CACHE) {
                    break;
                }
            }
        }
        for i in 0..2 {
            if sprites_indcies[i] < SPRITE_CACHE {
                sprite_caches[i][sprites_indcies[i]] = None;
            }
        }
    }

    pub fn render<'a>(
        &'a self,
        sprite_caches: &mut SpriteCaches<'a>,
        screen: &mut [[u16; 240]; 240],
    ) {
        for y in 0..240 {
            self.per_scanline(y, sprite_caches);
            let handle_bg0 = select_correct_handle_bg(&self.bg0_state);
            let handle_bg1 = select_correct_handle_bg(&self.bg1_state);
            let handle_cmath = select_correct_handle_cmaths(&self.cmath_state);
            let per_pixel = self.select_correct_per_pixel(sprite_caches);

            for x in 0..(240 / 8) {
                let col = per_pixel(
                    self,
                    x * 8,
                    y,
                    sprite_caches,
                    handle_bg0,
                    handle_bg1,
                    handle_cmath,
                );

                screen[y as usize][x as usize * 8..x as usize * 8 + 8]
                    .clone_from_slice(col.as_array())
            }
        }
    }

    pub const fn new() -> Self {
        SASPPU {
            bg0:         [[16; MAP_WIDTH]; MAP_HEIGHT],
            bg1:         [[16; MAP_WIDTH]; MAP_HEIGHT],
            main_state:  State::new(),
            bg0_state:   Background::new(),
            bg1_state:   Background::new(),
            cmath_state: ColorMath::new(),
            oam:         [Sprite::new(); SPRITE_COUNT],
            background:  [u16x8::from_array([0; 8]); (BG_WIDTH / 8) * BG_HEIGHT],
            sprites:     [[u16x8::from_array([0; 8]); SPR_WIDTH / 8]; SPR_HEIGHT],
        }
    }
}
