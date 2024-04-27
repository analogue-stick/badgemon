#![feature(portable_simd)]
use std::simd::prelude::*;

struct Sprite {
    x: i16,
    y: i16,
    width: u8,
    height: u8,
    graphics_x: u8,
    graphics_y: u8,
    flags: u16,
}

const SPR_ENABLED: u16 = (1 << 0);
const SPR_FLIP_X: u16 = (1 << 1);
const SPR_FLIP_Y: u16 = (1 << 2);
const SPR_MAIN_SCREEN: u16 = (1 << 3);
const SPR_SUB_SCREEN: u16 = (1 << 4);
const SPR_C_MATH: u16 = (1 << 5);
// const SPR_PRIORITY: u16 = (1 << 6);
const SPR_DOUBLE: u16 = (1 << 7);
const SPR_MAIN_IN_WINDOW: u16 = (1 << 8);
const SPR_MAIN_OUT_WINDOW: u16 = (1 << 9);
const SPR_MAIN_WINDOW_LOG2_LOG2: usize = (10);
const SPR_MAIN_WINDOW_LOG1: u16 = (1 << 10);
const SPR_MAIN_WINDOW_LOG2: u16 = (1 << 11);
// #define SPR_SUB_IN_WINDOW (1 << 12)
// #define SPR_SUB_OUT_WINDOW (1 << 13)
// #define SPR_SUB_WINDOW_LOG2_LOG2 (14)
// #define SPR_SUB_WINDOW_LOG1 (1 << 14)
// #define SPR_SUB_WINDOW_LOG2 (1 << 15)

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
const BG0_WIDTH: usize = (1 << BG0_WIDTH_POWER);
const BG0_HEIGHT: usize = (1 << BG0_HEIGHT_POWER);

const SPRITE_COUNT: usize = 256;

const SPR_WIDTH_POWER: usize = 8;
const SPR_HEIGHT_POWER: usize = 8;
const SPR_WIDTH: usize = (1 << SPR_WIDTH_POWER);
const SPR_HEIGHT: usize = (1 << SPR_HEIGHT_POWER);

struct SASPPU<'a> {
    screen: [[u16; 240]; 240],

    BG0: [[u16x8; BG0_WIDTH / 8]; BG0_HEIGHT],
    sprites: [[u16x8; SPR_WIDTH / 8]; SPR_HEIGHT],

    state: State,
    OAM: [Sprite; SPRITE_COUNT],

    sprite_cache: [&'a Sprite; 16],
}

fn get_window(
    logic: u8,
    window_1: u16x8,
    window_2: u16x8,
    in_window: bool,
    out_window: bool,
) -> u16x8 {
    if in_window && out_window {
        return u16x8::splat(0xffff);
    }
    if !(in_window | out_window) {
        return u16x8::splat(0x0000);
    }
    let window = match logic {
        0 => !(window_1 ^ window_2),
        1 => window_1 ^ window_2,
        2 => window_1 & window_2,
        3 => window_1 | window_2,
        _ => unreachable!(),
    };
    if out_window {
        return !window;
    }
    return window;
}

impl SASPPU<'_> {
    fn handle_bg0(
        &self,
        main_col: &mut u16x8,
        sub_col: &mut u16x8,
        c_math: &mut u16x8,
        x: i16,
        y: i16,
        window_1: u16x8,
        window_2: u16x8,
    ) {
        if self.state.enable_bg0 {
            let bg0 = self.BG0[(y + self.state.bg0scrollv) as usize & (BG0_HEIGHT - 1)]
                [(x + (self.state.bg0scrollh & 0xFFF0u16 as i16)) as usize & (BG0_WIDTH - 1)];
        }
    }
}

fn main() {}
