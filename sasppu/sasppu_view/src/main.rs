use minifb::{Key, Window, WindowOptions};
use std::{
    io::{self, BufWriter, Cursor},
    net::TcpListener,
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

    let mut before_buf = [0u8; 240 * 240 * 2];
    let mut buffer = [0u32; 240 * 240];
    let socket = TcpListener::bind("0.0.0.0:1234").unwrap();
    socket.set_nonblocking(true).unwrap();
    while window.is_open() && !window.is_key_down(Key::Escape) {
        {
            if let Ok((mut stream, _)) = socket.accept() {
                let mut c = Cursor::new(before_buf);
                io::copy(&mut stream, &mut c).unwrap();
                before_buf = c.into_inner();
                for (i, x) in buffer.iter_mut().enumerate() {
                    let col: u16 = (before_buf[i * 2] as u16) << 8 | before_buf[i * 2 + 1] as u16;
                    *x = ((((col >> 11) & 0x1F) as u32) << (16 + 3))
                        | ((((col >> 5) & 0x3F) as u32) << (8 + 2))
                        | ((((col >> 0) & 0x1F) as u32) << (0 + 3));
                }
            }
            window.update_with_buffer(&buffer, width, height).unwrap();
        }
    }
}
