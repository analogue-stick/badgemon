#![feature(portable_simd)]
#![feature(array_chunks)]
#![allow(static_mut_refs)]
use std::{
    collections::VecDeque,
    time::{Duration, Instant, SystemTime, UNIX_EPOCH},
};

pub const BG_DEFAULT: &[u8; 256 * 256 * 2] = include_bytes!("../assets/kodim05.png.bgraw");
pub const SPR_DEFAULT: &[u8; 256 * 32 * 2] = include_bytes!("../assets/sprites.png.bgraw");

pub static mut GLOBAL_STATE: SASPPU = SASPPU::new();

use minifb::{Key, Window, WindowOptions};
use sasppu_sys::*;

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
    let ppu: &mut SASPPU = unsafe { &mut GLOBAL_STATE };
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
        if i & 2 > 0 {
            spr.flags |= SPR_FLIP_X;
        }
        if i & 3 > 0 {
            spr.flags |= SPR_FLIP_Y;
        }
        if i & 4 > 0 {
            spr.flags |= SPR_DOUBLE;
        }
        spr.width = 32;
        spr.height = 32;
        spr.x = 0;
        spr.graphics_x = ((i as u8 >> 1) % 8) * 4;
    }

    for val in ppu
        .background
        .iter_mut()
        .zip(BG_DEFAULT.array_chunks::<16>())
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

    for y in 0..MAP_HEIGHT {
        let (ypos, flipy) = if y >= MAP_HEIGHT / 2 {
            (MAP_HEIGHT - y - 1, true)
        } else {
            (y, false)
        };
        for x in 0..MAP_WIDTH {
            let (xpos, flipx) = if x >= MAP_WIDTH / 2 {
                (MAP_WIDTH - x - 1, true)
            } else {
                (x, false)
            };
            ppu.bg0[y][x] =
                ((xpos + (ypos * BG_WIDTH)) * 8) as u16 | ((flipy as u16) << 1) | (flipx as u16);
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
            ppu.bg0_state.scroll_x = ((epoch * 2.0).sin() * 256.0 + 256.0) as i16;
            ppu.bg0_state.scroll_y = ((epoch * 3.0).cos() * 256.0 + 256.0) as i16;
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
                    | (((*col & 0x1F) as u32) << 3);
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
                    current_time.as_secs_f64() * 1000.0,
                    elapsed_time * 1000.0,
                    1.0f64 / elapsed_time
                );
            }
            i = i.wrapping_add(1);
            window.update_with_buffer(&buffer, width, height).unwrap();
        }
    }
}
