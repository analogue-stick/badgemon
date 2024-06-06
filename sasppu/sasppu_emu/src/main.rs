#![feature(portable_simd)]
#![feature(array_chunks)]
use std::{
    simd::prelude::*,
    time::{Instant, SystemTime, UNIX_EPOCH},
};

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
const SPR_FLIP_X: u16 = 1 << 1;
const SPR_FLIP_Y: u16 = 1 << 2;
const SPR_MAIN_SCREEN: u16 = 1 << 3;
const SPR_SUB_SCREEN: u16 = 1 << 4;
const SPR_C_MATH: u16 = 1 << 5;
// const SPR_PRIORITY: u16 = (1 << 6);
const SPR_DOUBLE: u16 = 1 << 7;
const SPR_MAIN_IN_WINDOW: u16 = 1 << 8;
const SPR_MAIN_OUT_WINDOW: u16 = 1 << 9;
const SPR_MAIN_WINDOW_LOG2_LOG2: usize = 10;
const SPR_MAIN_WINDOW_LOG1: u16 = 1 << 10;
const SPR_MAIN_WINDOW_LOG2: u16 = 1 << 11;
// #define SPR_SUB_IN_WINDOW (1 << 12)
// #define SPR_SUB_OUT_WINDOW (1 << 13)
// #define SPR_SUB_WINDOW_LOG2_LOG2 (14)
// #define SPR_SUB_WINDOW_LOG1 (1 << 14)
// #define SPR_SUB_WINDOW_LOG2 (1 << 15)

#[derive(Debug, Clone, Copy, Default)]
struct State {
    mainscreen_colour: u16,
    subscreen_colour: u16,

    enable_bg0: bool,

    bg0scrollh: i16,
    bg0scrollv: i16,

    // color math
    bg0_cmath_enable: bool,
    bg0_main_screen_enable: bool,
    bg0_sub_screen_enable: bool,
    half_main_screen: bool,
    double_main_screen: bool,
    half_sub_screen: bool,
    double_sub_screen: bool,
    add_sub_screen: bool,
    sub_sub_screen: bool,
    fade_enable: bool,
    screen_fade: u8,
    cmath_enable: bool,
    cmath_default: bool,

    // windowing
    bg0_main_in_window: bool,
    bg0_main_out_window: bool,
    bg0_main_window_log: u8,

    window_1_left: u8,
    window_1_right: u8,
    window_2_left: u8,
    window_2_right: u8,
}

const BG0_WIDTH_POWER: usize = 9;
const BG0_HEIGHT_POWER: usize = 9;
const BG0_WIDTH: usize = 1 << BG0_WIDTH_POWER;
const BG0_HEIGHT: usize = 1 << BG0_HEIGHT_POWER;

const SPRITE_COUNT: usize = 256;
const SPRITE_CACHE: usize = 16;

const SPR_WIDTH_POWER: usize = 8;
const SPR_HEIGHT_POWER: usize = 8;
const SPR_WIDTH: usize = 1 << SPR_WIDTH_POWER;
const SPR_HEIGHT: usize = 1 << SPR_HEIGHT_POWER;

const BG0_DEFAULT: &[u8; 512 * 512 * 2] = include_bytes!("../assets/kodim05.png.bgraw");
const SPR_DEFAULT: &[u8; 256 * 32 * 2] = include_bytes!("../assets/sprites.png.bgraw");

struct SASPPU {
    bg0: [[u16x8; BG0_WIDTH / 8]; BG0_HEIGHT],
    sprites: [[u16x8; SPR_WIDTH / 8]; SPR_HEIGHT],

    state: State,
    oam: [Sprite; SPRITE_COUNT],
}

#[inline]
fn get_window(
    logic: u8,
    window_1: mask16x8,
    window_2: mask16x8,
    in_window: bool,
    out_window: bool,
) -> mask16x8 {
    if in_window && out_window {
        return mask16x8::splat(true);
    }
    if !(in_window | out_window) {
        return mask16x8::splat(false);
    }
    let window = match logic {
        0 => window_1 | window_2,
        1 => window_1 & window_2,
        2 => window_1 ^ window_2,
        3 => !(window_1 ^ window_2),
        _ => unreachable!(),
    };
    if out_window {
        return !window;
    }
    return window;
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

impl SASPPU {
    #[inline]
    fn handle_bg0(
        &self,
        main_col: &mut u16x8,
        sub_col: &mut u16x8,
        x: i16,
        y: i16,
        window_1: mask16x8,
        window_2: mask16x8,
    ) {
        if self.state.enable_bg0 {
            let y_pos = (y + self.state.bg0scrollv) as usize & (BG0_HEIGHT - 1);
            let x_pos_1 =
                (x + (self.state.bg0scrollh & 0xFFF8u16 as i16)) as usize & (BG0_WIDTH - 1);
            let x_pos_2 = (x_pos_1 + 8) as usize & (BG0_WIDTH - 1);
            let offset = (self.state.bg0scrollh & 0x7u16 as i16) as usize;
            let bg0_1 = self.bg0[y_pos][x_pos_1 >> 3];
            let bg0_2 = self.bg0[y_pos][x_pos_2 >> 3];
            let mut bg0 = swimzleoo(bg0_1, bg0_2, offset);
            let window = get_window(
                self.state.bg0_main_window_log,
                window_1,
                window_2,
                self.state.bg0_main_in_window,
                self.state.bg0_main_out_window,
            ) & bg0.simd_ne(u16x8::splat(0));
            if self.state.bg0_cmath_enable {
                bg0 |= u16x8::splat(0x8000);
            }
            if self.state.bg0_main_screen_enable {
                *main_col = window.select(bg0, *main_col);
            }
            if self.state.bg0_sub_screen_enable {
                *sub_col = window.select(bg0, *sub_col);
            }
        }
    }

    fn handle_sprite(
        &self,
        sprite: &Sprite,
        main_col: &mut u16x8,
        sub_col: &mut u16x8,
        x: i16,
        y: i16,
        window_1: mask16x8,
        window_2: mask16x8,
    ) {
        let flags = sprite.flags;
        let double_sprite = flags & SPR_DOUBLE > 0;
        let sprite_width = if double_sprite {
            sprite.width << 1
        } else {
            sprite.width
        };
        let mut offset_x = x - sprite.x;
        if offset_x >= -7 && offset_x < sprite_width as i16 {
            if flags & SPR_FLIP_X > 0 {
                offset_x = sprite_width as i16 - offset_x - 1;
            }
            let mut offset_y = y - sprite.y;
            if flags & SPR_FLIP_Y > 0 {
                offset_y = sprite_width as i16 - offset_y - 1;
            }
            let mut offset_y = offset_y as usize;
            if double_sprite {
                offset_x >>= 1;
                offset_y >>= 1;
            }
            let x_pos_1 =
                (offset_x & if double_sprite { 0xFFFCu16 } else { 0xFFF8u16 } as i16) as isize;
            let x_pos_2 = if flags & SPR_FLIP_X > 0 {
                x_pos_1 - 8
            } else {
                x_pos_1 + 8
            };
            let offset = ((8 - (sprite.x & 0x7i16)) % 8) as usize;
            let mut spr_1 = if x_pos_1 >= sprite.width as isize || x_pos_1 < 0 {
                u16x8::splat(0)
            } else {
                self.sprites[offset_y + sprite.graphics_y as usize]
                    [(x_pos_1 as usize >> 3) + sprite.graphics_x as usize]
            };
            let mut spr_2 = if x_pos_2 >= sprite.width as isize || x_pos_2 < 0 {
                u16x8::splat(0)
            } else {
                self.sprites[offset_y + sprite.graphics_y as usize]
                    [(x_pos_2 as usize >> 3) + sprite.graphics_x as usize]
            };
            if double_sprite {
                if x_pos_1 & 0x4 == 0 {
                    if flags & SPR_FLIP_X > 0 {
                        spr_1 = spr_1.interleave(spr_1).0;
                        spr_2 = spr_2.interleave(spr_2).1;
                    } else {
                        (spr_1, spr_2) = spr_1.interleave(spr_1);
                    }
                } else {
                    if flags & SPR_FLIP_X > 0 {
                        (spr_2, spr_1) = spr_1.interleave(spr_1);
                    } else {
                        spr_1 = spr_1.interleave(spr_1).1;
                        spr_2 = spr_2.interleave(spr_2).0;
                    }
                }
            }
            if flags & SPR_FLIP_X > 0 {
                (spr_1, spr_2) = (spr_1.reverse(), spr_2.reverse());
            }
            let mut spr_col = swimzleoo(spr_1, spr_2, offset);
            //if x_pos_1 & 0x4 > 0 {
            //    spr_col = u16x8::splat(0);
            //}
            let window = get_window(
                (flags & (SPR_MAIN_WINDOW_LOG1 | SPR_MAIN_WINDOW_LOG2) >> SPR_MAIN_WINDOW_LOG2_LOG2)
                    as u8,
                window_1,
                window_2,
                flags & SPR_MAIN_IN_WINDOW > 0,
                flags & SPR_MAIN_OUT_WINDOW > 0,
            ) & spr_col.simd_ne(u16x8::splat(0));
            if flags & SPR_C_MATH > 0 {
                spr_col |= u16x8::splat(0x8000);
            }
            if flags & SPR_MAIN_SCREEN > 0 {
                *main_col = window.select(spr_col, *main_col);
            }
            if flags & SPR_SUB_SCREEN > 0 {
                *sub_col = window.select(spr_col, *sub_col);
            }
        }
    }

    #[inline]
    fn per_pixel(&self, x: u8, y: u8, sprite_cache: &[Option<&Sprite>; SPRITE_CACHE]) -> u16x8 {
        let mut main_col =
            u16x8::splat(self.state.mainscreen_colour | (self.state.cmath_default as u16) << 15);
        let mut sub_col = u16x8::splat(self.state.subscreen_colour);

        let x_window = u16x8::from_array([0, 1, 2, 3, 4, 5, 6, 7]) + u16x8::splat(x as u16);
        let window_1 = x_window.simd_ge(u16x8::splat(self.state.window_1_left as u16))
            & x_window.simd_le(u16x8::splat(self.state.window_1_right as u16));
        let window_2 = x_window.simd_ge(u16x8::splat(self.state.window_2_left as u16))
            & x_window.simd_le(u16x8::splat(self.state.window_2_right as u16));

        self.handle_bg0(
            &mut main_col,
            &mut sub_col,
            x as i16,
            y as i16,
            window_1,
            window_2,
        );

        for spr in sprite_cache
            .iter()
            .take_while(|x| x.is_some())
            .map(|x| x.unwrap())
        {
            self.handle_sprite(
                spr,
                &mut main_col,
                &mut sub_col,
                x as i16,
                y as i16,
                window_1,
                window_2,
            )
        }

        let use_cmath =
            mask16x8::splat(self.state.cmath_enable) & main_col.simd_ge(u16x8::splat(0x8000));
        if self.state.fade_enable || use_cmath.any() {
            let mask = u16x8::splat(0b00011111);
            let mut main_r = (main_col >> 10) & mask;
            let mut main_g = (main_col >> 5) & mask;
            let mut main_b = (main_col >> 0) & mask;
            if use_cmath.any() {
                let mut sub_r = (sub_col >> 10) & mask;
                let mut sub_g = (sub_col >> 5) & mask;
                let mut sub_b = (sub_col >> 0) & mask;

                let main_r_bak = main_r;
                let main_g_bak = main_g;
                let main_b_bak = main_b;

                if self.state.double_main_screen {
                    main_r = (main_r << 1) & mask;
                    main_g = (main_g << 1) & mask;
                    main_b = (main_b << 1) & mask;
                }
                if self.state.half_main_screen {
                    main_r = main_r >> 1;
                    main_g = main_g >> 1;
                    main_b = main_b >> 1;
                }
                if self.state.double_sub_screen {
                    sub_r = (sub_r << 1) & mask;
                    sub_g = (sub_g << 1) & mask;
                    sub_b = (sub_b << 1) & mask;
                }
                if self.state.half_sub_screen {
                    sub_r = sub_r >> 1;
                    sub_g = sub_g >> 1;
                    sub_b = sub_b >> 1;
                }
                if self.state.add_sub_screen {
                    main_r = (main_r + sub_r).simd_min(mask);
                    main_g = (main_g + sub_g).simd_min(mask);
                    main_b = (main_b + sub_b).simd_min(mask);
                }
                if self.state.sub_sub_screen {
                    main_r = main_r.saturating_sub(sub_r);
                    main_g = main_g.saturating_sub(sub_g);
                    main_b = main_b.saturating_sub(sub_b);
                }

                main_r = use_cmath.select(main_r, main_r_bak);
                main_g = use_cmath.select(main_g, main_g_bak);
                main_b = use_cmath.select(main_b, main_b_bak);
            }
            if self.state.fade_enable {
                let fade = u16x8::splat(self.state.screen_fade as u16);
                main_r = ((main_r * fade) >> 8) & mask;
                main_g = ((main_g * fade) >> 8) & mask;
                main_b = ((main_b * fade) >> 8) & mask;
            }
            return (main_r << 11) | (main_g << 6) | (main_b);
        }
        return ((main_col & u16x8::splat(0b0111111111100000)) << 1)
            | (main_col & u16x8::splat(0b00011111));
    }

    fn per_scanline<'a>(&'a self, y: u8, sprite_cache: &mut [Option<&'a Sprite>; SPRITE_CACHE]) {
        let mut sprites_index = 0;
        for spr in self.oam.iter() {
            let flags = spr.flags;
            if (flags & SPR_ENABLED > 0)
                && (((flags & SPR_MAIN_SCREEN > 0) || (flags & SPR_SUB_SCREEN > 0))
                    && ((flags & SPR_MAIN_IN_WINDOW > 0) || (flags & SPR_MAIN_OUT_WINDOW > 0)))
                && (y as i16 >= spr.y)
                && (((flags & SPR_DOUBLE > 0) && ((y as i16) < ((spr.height as i16) << 1) + spr.y))
                    || ((y as i16) < (spr.height as i16 + spr.y)))
                && ((spr.x as i16) < 240)
                && (((flags & SPR_DOUBLE > 0) && (spr.x > -((spr.width as i16) << 1)))
                    || (spr.x > -(spr.width as i16)))
            {
                sprite_cache[sprites_index] = Some(spr);
                sprites_index += 1;
            }
            if sprites_index == SPRITE_CACHE {
                break;
            }
        }
        if sprites_index < SPRITE_CACHE {
            sprite_cache[sprites_index] = None;
        }
    }

    fn render<'a>(
        &'a self,
        sprite_cache: &mut [Option<&'a Sprite>; SPRITE_CACHE],
        screen: &mut [[u16; 240]; 240],
    ) {
        for y in 0..240 {
            self.per_scanline(y, sprite_cache);
            for x in 0..(240 / 8) {
                let col = self.per_pixel(x * 8, y, sprite_cache);

                screen[y as usize][x as usize * 8..x as usize * 8 + 8]
                    .clone_from_slice(col.as_array())
            }
        }
    }

    fn new() -> Self {
        SASPPU {
            bg0: [[u16x8::splat(0); BG0_WIDTH / 8]; BG0_HEIGHT],
            sprites: [[u16x8::splat(0); SPR_WIDTH / 8]; SPR_HEIGHT],
            state: State::default(),
            oam: [Sprite::default(); SPRITE_COUNT],
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
        "SASPPU VIEW - Press ESC to exit",
        width,
        height,
        WindowOptions::default(),
    )
    .expect("Unable to create the window");

    const TEST_SPR_COUNT: usize = 32;

    let mut before_buf = [[0u16; 240]; 240];
    let mut buffer = [0u32; 960 * 960];
    let mut ppu: SASPPU = SASPPU::new();
    ppu.state.mainscreen_colour = colour!(31, 0, 0);
    ppu.state.subscreen_colour = colour!(0, 0, 0);
    ppu.state.bg0_main_screen_enable = true;
    ppu.state.bg0_main_in_window = true;
    //ppu.state.bg0_main_out_window = true;
    ppu.state.window_1_left = 30;
    ppu.state.window_1_right = 160;
    ppu.state.window_2_left = 80;
    ppu.state.window_2_right = 210;
    ppu.state.enable_bg0 = true;
    ppu.state.bg0_cmath_enable = true;
    ppu.state.cmath_enable = true;
    ppu.state.sub_sub_screen = true;
    for (i, spr) in ppu.oam.iter_mut().take(TEST_SPR_COUNT).enumerate() {
        spr.flags |= SPR_ENABLED;
        if i & 1 > 0 {
            spr.flags |= SPR_SUB_SCREEN;
            spr.flags |= SPR_MAIN_IN_WINDOW;
        } else {
            spr.flags |= SPR_MAIN_SCREEN;
            spr.flags |= SPR_MAIN_OUT_WINDOW;
        }
        spr.flags |= 2 << SPR_MAIN_WINDOW_LOG2_LOG2;
        //spr.flags |= SPR_FLIP_X;
        //spr.flags |= SPR_FLIP_Y;
        //spr.flags |= SPR_DOUBLE;
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
            //buffer[(y * 960) + (x * 2)] = val;
            //buffer[(y * 960 + 480) + (x * 2)] = val;
            //buffer[(y * 960 + 480) + (x * 2 + 1)] = val;
            //buffer[(y * 960) + (x * 2 + 1)] = val;
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
    while window.is_open() && !window.is_key_down(Key::Escape) {
        {
            let mut sprite_cache = [None; SPRITE_CACHE];
            let now = Instant::now();
            let epoch = SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos() as f64
                / 10000000000.0;
            ppu.state.bg0scrollh = ((epoch * 2.0).sin() * 256.0 + 256.0) as i16;
            ppu.state.bg0scrollv = ((epoch * 3.0).cos() * 256.0 + 256.0) as i16;
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

            let elapsed_time = now.elapsed();
            println!("Frame:{:.4}ms.", elapsed_time.as_nanos() as f64 / 1000000.0);
            window.update_with_buffer(&buffer, width, height).unwrap();
        }
    }
}
