#![feature(portable_simd)]
#![feature(generic_const_exprs)]
#![feature(array_chunks)]
use seq_macro::seq;
use std::{
    collections::VecDeque,
    simd::prelude::*,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

mod simd;

#[derive(Debug, Clone, Copy, Default)]
struct Sprite {
    x: i16,
    y: i16,
    width: u8,
    height: u8,
    graphics_x: u8,
    graphics_y: u8,
    flags: u16,
}

const SPR_ENABLED: u16 = 1 << 0;
const SPR_PRIORITY: u16 = 1 << 1;
const SPR_FLIP_X: u16 = 1 << 2;
const SPR_FLIP_Y: u16 = 1 << 3;
const SPR_MAIN_SCREEN: u16 = 1 << 4;
const SPR_SUB_SCREEN: u16 = 1 << 5;
const SPR_C_MATH: u16 = 1 << 6;
const SPR_DOUBLE: u16 = 1 << 7;
const SPR_MAIN_WINDOW_POW2: u16 = 8;
const SPR_MAIN_WINDOW_LOG1: u16 = 1 << 8;
const SPR_MAIN_WINDOW_LOG2: u16 = 1 << 9;
const SPR_MAIN_WINDOW_LOG3: u16 = 1 << 10;
const SPR_MAIN_WINDOW_LOG4: u16 = 1 << 11;
const SPR_SUB_WINDOW_POW2: u16 = 12;
const SPR_SUB_WINDOW_LOG1: u16 = 1 << 12;
const SPR_SUB_WINDOW_LOG2: u16 = 1 << 13;
const SPR_SUB_WINDOW_LOG3: u16 = 1 << 14;
const SPR_SUB_WINDOW_LOG4: u16 = 1 << 15;

const WINDOW_A: u16 = 0b0001;
const WINDOW_B: u16 = 0b0010;
const WINDOW_AB: u16 = 0b0100;
const WINDOW_X: u16 = 0b1000;

#[derive(Debug, Clone, Copy, Default)]
struct Background {
    enable: bool,
    scroll_h: i16,
    scroll_v: i16,
    cmath_enable: bool,
    main_screen_enable: bool,
    sub_screen_enable: bool,
    main_window_log: u8,
    sub_window_log: u8,
}
#[derive(Debug, Clone, Copy, Default)]
struct ColorMath {
    half_main_screen: bool,
    double_main_screen: bool,
    half_sub_screen: bool,
    double_sub_screen: bool,
    add_sub_screen: bool,
    sub_sub_screen: bool,
    fade_enable: bool,
    screen_fade: u8,
    cmath_enable: bool,
}
#[derive(Debug, Clone, Copy, Default)]
struct State {
    mainscreen_colour: u16,
    subscreen_colour: u16,
    cmath_default: bool,

    // windowing
    window_1_left: u8,
    window_1_right: u8,
    window_2_left: u8,
    window_2_right: u8,
}

const BG_WIDTH_POWER: usize = 9;
const BG_HEIGHT_POWER: usize = 9;
const BG_WIDTH: usize = 1 << BG_WIDTH_POWER;
const BG_HEIGHT: usize = 1 << BG_HEIGHT_POWER;

const SPRITE_COUNT: usize = 256;
const SPRITE_CACHE: usize = 16;

type SpriteCache<'a> = [Option<&'a Sprite>; SPRITE_CACHE];
type SpriteCaches<'a> = [SpriteCache<'a>; 2];

const SPR_WIDTH_POWER: usize = 8;
const SPR_HEIGHT_POWER: usize = 8;
const SPR_WIDTH: usize = 1 << SPR_WIDTH_POWER;
const SPR_HEIGHT: usize = 1 << SPR_HEIGHT_POWER;

const BG0_DEFAULT: &[u8; 512 * 512 * 2] = include_bytes!("../assets/kodim05.png.bgraw");
const SPR_DEFAULT: &[u8; 256 * 32 * 2] = include_bytes!("../assets/sprites.png.bgraw");

type GraphicsPlane = Box<[[u16x8; BG_WIDTH / 8]; BG_HEIGHT]>;
type SpritePlane = Box<[[u16x8; SPR_WIDTH / 8]; SPR_WIDTH]>;

struct SASPPU {
    main_state: State,
    bg0_state: Background,
    bg1_state: Background,
    oam: Box<[Sprite; SPRITE_COUNT]>,

    bg0: GraphicsPlane,
    bg1: GraphicsPlane,
    sprites: SpritePlane,
    cmath_state: ColorMath,
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
    state: &Background,
    graphics: &GraphicsPlane,
    main_col: &mut u16x8,
    sub_col: &mut u16x8,
    x: i16,
    y: i16,
    window_1: mask16x8,
    window_2: mask16x8,
) {
    let y_pos = (y + state.scroll_v) as usize & (BG_HEIGHT - 1);
    let x_pos_1 = (x + (state.scroll_h & 0xFFF8u16 as i16)) as usize & (BG_WIDTH - 1);
    let x_pos_2 = (x_pos_1 + 8) as usize & (BG_WIDTH - 1);
    let offset = (state.scroll_h & 0x7u16 as i16) as usize;
    let bg0_1 = graphics[y_pos][x_pos_1 >> 3];
    let bg0_2 = graphics[y_pos][x_pos_2 >> 3];
    let mut bg0 = swimzleoo(bg0_1, bg0_2, offset);
    let main_window = if MAIN_SCREEN_WINDOW_0 {
        mask16x8::splat(false)
    } else if SUB_SCREEN_WINDOW_15 {
        mask16x8::splat(true)
    } else {
        get_window(state.main_window_log, window_1, window_2)
    } & bg0.simd_ne(u16x8::splat(0));
    let sub_window = if SUB_SCREEN_WINDOW_0 {
        mask16x8::splat(false)
    } else if SUB_SCREEN_WINDOW_15 {
        mask16x8::splat(true)
    } else {
        get_window(state.sub_window_log, window_1, window_2)
    } & bg0.simd_ne(u16x8::splat(0));
    if CMATH_ENABLE {
        bg0 |= u16x8::splat(0x8000);
    }
    if MAIN_SCREEN_ENABLE {
        *main_col = main_window.select(bg0, *main_col);
    }
    if SUB_SCREEN_ENABLE {
        *sub_col = sub_window.select(bg0, *sub_col);
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

type HandleBgType =
    fn(&Background, &GraphicsPlane, &mut u16x8, &mut u16x8, i16, i16, mask16x8, mask16x8);

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
    return HANDLE_BG_LOOKUP[lookup];
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
    main_col: &mut u16x8,
    sub_col: &mut u16x8,
    x: i16,
    y: i16,
    this_spr_main_screen_window: u8,
    this_spr_sub_screen_window: u8,
    window_1: mask16x8,
    window_2: mask16x8,
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
            u16x8::splat(0)
        } else {
            graphics[offset_y + sprite.graphics_y as usize]
                [(x_pos_1 as usize >> 3) + sprite.graphics_x as usize]
        };
        let mut spr_2 = if x_pos_2 >= sprite.width as isize || x_pos_2 < 0 {
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
            } else {
                if THIS_SPR_FLIP_X {
                    (spr_2, spr_1) = spr_1.interleave(spr_1);
                } else {
                    spr_1 = spr_1.interleave(spr_1).1;
                    spr_2 = spr_2.interleave(spr_2).0;
                }
            }
        }
        if THIS_SPR_FLIP_X {
            (spr_1, spr_2) = (spr_1.reverse(), spr_2.reverse());
        }
        let mut spr_col = swimzleoo(spr_1, spr_2, offset);
        let main_window = get_window(this_spr_main_screen_window, window_1, window_2)
            & spr_col.simd_ne(u16x8::splat(0));
        let sub_window = get_window(this_spr_sub_screen_window, window_1, window_2)
            & spr_col.simd_ne(u16x8::splat(0));
        if THIS_SPR_C_MATH {
            spr_col |= u16x8::splat(0x8000);
        }
        if THIS_SPR_MAIN_SCREEN {
            *main_col = main_window.select(spr_col, *main_col);
        }
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
    return HANDLE_SPRITE_LOOKUP[lookup as usize];
}

macro_rules! split_main {
    ($main_col:ident, $mask:ident) => {{
        let main_r = (*$main_col >> 10) & $mask;
        let main_g = (*$main_col >> 5) & $mask;
        let main_b = (*$main_col >> 0) & $mask;
        (main_r, main_g, main_b)
    }};
}

macro_rules! double_screen {
    ($main_r:ident, $main_g:ident, $main_b:ident, $mask:ident) => {
        $main_r = ($main_r << 1) & $mask;
        $main_g = ($main_g << 1) & $mask;
        $main_b = ($main_b << 1) & $mask;
    };
}

macro_rules! halve_screen {
    ($main_r:ident, $main_g:ident, $main_b:ident, $mask:ident) => {
        $main_r = $main_r >> 1;
        $main_g = $main_g >> 1;
        $main_b = $main_b >> 1;
    };
}

macro_rules! add_screens {
    ($main_r:ident, $main_g:ident, $main_b:ident, $sub_r:ident, $sub_g:ident, $sub_b:ident, $mask:ident) => {
        $main_r = ($main_r + $sub_r).simd_min($mask);
        $main_g = ($main_g + $sub_g).simd_min($mask);
        $main_b = ($main_b + $sub_b).simd_min($mask);
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
    main_col: &mut u16x8,
    sub_col: &mut u16x8,
) {
    let use_cmath = mask16x8::splat(CMATH_ENABLE) & main_col.simd_ge(u16x8::splat(0x8000));
    if FADE_ENABLE || use_cmath.any() {
        let mask = u16x8::splat(0b00011111);
        let (mut main_r, mut main_g, mut main_b) = split_main!(main_col, mask);
        if use_cmath.any() {
            let (mut sub_r, mut sub_g, mut sub_b) = split_main!(sub_col, mask);

            let main_r_bak = main_r;
            let main_g_bak = main_g;
            let main_b_bak = main_b;

            if DOUBLE_MAIN_SCREEN {
                double_screen!(main_r, main_g, main_b, mask);
            }
            if HALF_MAIN_SCREEN {
                halve_screen!(main_r, main_g, main_b, mask);
            }
            if DOUBLE_SUB_SCREEN {
                double_screen!(sub_r, sub_g, sub_b, mask);
            }
            if HALF_SUB_SCREEN {
                halve_screen!(sub_r, sub_g, sub_b, mask);
            }
            if ADD_SUB_SCREEN {
                add_screens!(main_r, main_g, main_b, sub_r, sub_g, sub_b, mask);
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
            main_r = ((main_r * fade) >> 8) & mask;
            main_g = ((main_g * fade) >> 8) & mask;
            main_b = ((main_b * fade) >> 8) & mask;
        }
        *main_col = (main_r << 11) | (main_g << 6) | (main_b);
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
    return HANDLE_CMATH_LOOKUP[lookup as usize];
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
        let mut main_col = u16x8::splat(
            self.main_state.mainscreen_colour | (self.main_state.cmath_default as u16) << 15,
        );
        let mut sub_col = u16x8::splat(self.main_state.subscreen_colour);

        let x_window = u16x8::from_array([0, 1, 2, 3, 4, 5, 6, 7]) + u16x8::splat(x as u16);
        let window_1 = x_window.simd_ge(u16x8::splat(self.main_state.window_1_left as u16))
            & x_window.simd_le(u16x8::splat(self.main_state.window_1_right as u16));
        let window_2 = x_window.simd_ge(u16x8::splat(self.main_state.window_2_left as u16))
            & x_window.simd_le(u16x8::splat(self.main_state.window_2_right as u16));

        if BG0_ENABLE {
            handle_bg0(
                &self.bg0_state,
                &self.bg0,
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

        return main_col;
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
        return PER_PIXEL_LOOKUP[lookup as usize];
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
                && ((spr.x as i16) < 240)
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

    fn render<'a>(&'a self, sprite_caches: &mut SpriteCaches<'a>, screen: &mut [[u16; 240]; 240]) {
        for y in 0..240 {
            self.per_scanline(y, sprite_caches);
            let handle_bg0 = select_correct_handle_bg(&self.bg0_state);
            let handle_bg1 = select_correct_handle_bg(&self.bg1_state);
            let handle_cmath = select_correct_handle_cmaths(&self.cmath_state);
            let per_pixel = self.select_correct_per_pixel(sprite_caches);

            for x in 0..(240 / 8) {
                let col = per_pixel(
                    &self,
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

    fn new() -> Self {
        SASPPU {
            bg0: Box::new([[u16x8::splat(0); BG_WIDTH / 8]; BG_HEIGHT]),
            bg1: Box::new([[u16x8::splat(0); BG_WIDTH / 8]; BG_HEIGHT]),
            sprites: Box::new([[u16x8::splat(0); SPR_WIDTH / 8]; SPR_HEIGHT]),
            main_state: State::default(),
            bg0_state: Background::default(),
            bg1_state: Background::default(),
            cmath_state: ColorMath::default(),
            oam: Box::new([Sprite::default(); SPRITE_COUNT]),
        }
    }
}

use minifb::{Key, Window, WindowOptions};

macro_rules! colour {
    ($r:expr, $g:expr, $b:expr) => {
        ($r << 10) | ($g << 5) | ($b)
    };
}

fn main() {
    let width = 960;
    let height = 960;

    let mut window = Window::new(
        "SASPPU EMU - Press ESC to exit",
        width,
        height,
        WindowOptions::default(),
    )
    .expect("Unable to create the window");

    window.set_target_fps(0);

    const TEST_SPR_COUNT: usize = 32;

    let mut before_buf = [[0u16; 240]; 240];
    let mut buffer = [0u32; 960 * 960];
    let mut ppu: SASPPU = SASPPU::new();
    ppu.main_state.mainscreen_colour = colour!(31, 0, 0);
    ppu.main_state.subscreen_colour = colour!(0, 0, 0);
    ppu.bg0_state.main_screen_enable = true;
    ppu.main_state.window_1_left = 30;
    ppu.main_state.window_1_right = 160;
    ppu.main_state.window_2_left = 80;
    ppu.main_state.window_2_right = 210;
    ppu.bg0_state.enable = true;
    ppu.bg0_state.main_window_log = (WINDOW_A | WINDOW_AB | WINDOW_B) as u8;
    ppu.bg0_state.cmath_enable = true;
    ppu.cmath_state.cmath_enable = true;
    ppu.cmath_state.sub_sub_screen = true;
    for (i, spr) in ppu.oam.iter_mut().take(TEST_SPR_COUNT).enumerate() {
        spr.flags |= SPR_ENABLED;
        if i & 1 > 0 {
            spr.flags |= SPR_SUB_SCREEN;
            spr.flags |= WINDOW_AB << SPR_SUB_WINDOW_POW2;
        } else {
            spr.flags |= SPR_MAIN_SCREEN;
            spr.flags |= (WINDOW_X | WINDOW_A | WINDOW_B) << SPR_MAIN_WINDOW_POW2;
        }
        spr.width = 32;
        spr.height = 32;
        spr.x = 0;
        spr.graphics_x = ((i as u8 >> 1) % 8) * 4;
    }

    for val in ppu
        .bg0
        .iter_mut()
        .flatten()
        .zip(BG0_DEFAULT.array_chunks::<16>())
    {
        for v in val
            .0
            .as_mut_array()
            .iter_mut()
            .zip(val.1.array_chunks::<2>())
        {
            *v.0 = u16::from_le_bytes(*v.1);
        }
    }

    for val in ppu
        .sprites
        .iter_mut()
        .flatten()
        .zip(SPR_DEFAULT.array_chunks::<16>())
    {
        for v in val
            .0
            .as_mut_array()
            .iter_mut()
            .zip(val.1.array_chunks::<2>())
        {
            *v.0 = u16::from_le_bytes(*v.1);
        }
    }
    let mut i = 0usize;
    let mut times = VecDeque::new();
    while window.is_open() && !window.is_key_down(Key::Escape) {
        {
            let mut sprite_cache = [[None; SPRITE_CACHE]; 2];
            let now = Instant::now();
            let epoch = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos() as f64
                / 10000000000.0;
            ppu.bg0_state.scroll_h = ((epoch * 2.0).sin() * 256.0 + 256.0) as i16;
            ppu.bg0_state.scroll_v = ((epoch * 3.0).cos() * 256.0 + 256.0) as i16;
            for (i, spr) in ppu.oam.iter_mut().take(TEST_SPR_COUNT).enumerate() {
                spr.x = ((epoch * (5.0 + (0.3 * (i >> 1) as f64))).sin() * (120.0 - 16.0)
                    + (120.0 - 16.0)) as i16;
                spr.y = ((epoch * (7.0 + (0.2 * (i >> 1) as f64))).cos() * (120.0 - 16.0)
                    + (120.0 - 16.0)) as i16;
            }
            ppu.render(&mut sprite_cache, &mut before_buf);
            for (x, col) in buffer.iter_mut().zip(before_buf.iter().flatten()) {
                *x = ((((col >> 11) & 0x1F) as u32) << (16 + 3))
                    | ((((col >> 5) & 0x3F) as u32) << (8 + 2))
                    | ((((col >> 0) & 0x1F) as u32) << (0 + 3));
            }
            for y in (0..240).rev() {
                for x in (0..240).rev() {
                    let val = buffer[(y * 240) + x];
                    for xx in 0..4 {
                        for yy in 0..4 {
                            buffer[(y * 960 * 4 + (960 * yy)) + (x * 4) + (xx)] = val;
                        }
                    }
                }
            }
            let current_time = now.elapsed();
            times.push_back(current_time);
            if times.len() > 100 {
                times.pop_front();
            }
            let elapsed_time: f64 =
                times.iter().sum::<Duration>().as_secs_f64() / times.len() as f64;
            if i & 0xF == 0 {
                println!(
                    "Frame: {:.4}ms, Avg: {:.4}, Avg. FPS: {:.4}",
                    current_time.as_secs_f64() as f64 * 1000.0,
                    elapsed_time as f64 * 1000.0,
                    1.0f64 / (elapsed_time as f64)
                );
            }
            i = i.wrapping_add(1);
            window.update_with_buffer(&buffer, width, height).unwrap();
        }
    }
}
