use minifb::{Key, Window, WindowOptions};
use std::{
    fs::File,
    io::{Read, Seek},
};

fn main() {
    let width = 240;
    let height = 240;

    let mut window = Window::new(
        "SASPPU VIEW - Press ESC to exit",
        width,
        height,
        WindowOptions::default(),
    )
    .expect("Unable to create the window");

    let mut file = File::open("../test.hex").unwrap();
    let mut before_buf = vec![];
    let mut buffer = [0u32; 240 * 240];
    while window.is_open() && !window.is_key_down(Key::Escape) {
        file.seek(std::io::SeekFrom::Start(0)).unwrap();
        file.read_to_end(&mut before_buf).unwrap();
        for (i, x) in buffer.iter_mut().enumerate() {
            let col: u16 = (before_buf[i * 2] as u16) << 8 | before_buf[i * 2 + 1] as u16;
            *x = ((((col >> 11) & 0x1F) as u32) << (16 + 3))
                | ((((col >> 5) & 0x3F) as u32) << (8 + 2))
                | ((((col >> 0) & 0x1F) as u32) << (0 + 3));
        }
        window.update_with_buffer(&buffer, width, height).unwrap();
    }
}
