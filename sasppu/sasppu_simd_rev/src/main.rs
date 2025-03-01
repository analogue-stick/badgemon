use std::{fs::File, io::Write};

fn shift_right(low: [u16; 8], high: [u16; 8], shift_amount: u8) -> ([u16; 8], [u16; 8]) {
    match shift_amount {
        0 => (low, high),
        1 => (
            [
                low[1], low[2], low[3], low[4], low[5], low[6], low[7], high[0],
            ],
            [
                high[1], high[2], high[3], high[4], high[5], high[6], high[7], 0,
            ],
        ),
        2 => (
            [
                low[2], low[3], low[4], low[5], low[6], low[7], high[0], high[1],
            ],
            [high[2], high[3], high[4], high[5], high[6], high[7], 0, 0],
        ),
        3 => (
            [
                low[3], low[4], low[5], low[6], low[7], high[0], high[1], high[2],
            ],
            [high[3], high[4], high[5], high[6], high[7], 0, 0, 0],
        ),
        4 => (
            [
                low[4], low[5], low[6], low[7], high[0], high[1], high[2], high[3],
            ],
            [high[4], high[5], high[6], high[7], 0, 0, 0, 0],
        ),
        5 => (
            [
                low[5], low[6], low[7], high[0], high[1], high[2], high[3], high[4],
            ],
            [high[5], high[6], high[7], 0, 0, 0, 0, 0],
        ),
        6 => (
            [
                low[6], low[7], high[0], high[1], high[2], high[3], high[4], high[5],
            ],
            [high[6], high[7], 0, 0, 0, 0, 0, 0],
        ),
        7 => (
            [
                low[7], high[0], high[1], high[2], high[3], high[4], high[5], high[6],
            ],
            [high[7], 0, 0, 0, 0, 0, 0, 0],
        ),
        8 => (
            [
                high[0], high[1], high[2], high[3], high[4], high[5], high[6], high[7],
            ],
            [0; 8],
        ),
        9 => (
            [
                high[1], high[2], high[3], high[4], high[5], high[6], high[7], 0,
            ],
            [0; 8],
        ),
        10 => (
            [high[2], high[3], high[4], high[5], high[6], high[7], 0, 0],
            [0; 8],
        ),
        11 => (
            [high[3], high[4], high[5], high[6], high[7], 0, 0, 0],
            [0; 8],
        ),
        12 => ([high[4], high[5], high[6], high[7], 0, 0, 0, 0], [0; 8]),
        13 => ([high[5], high[6], high[7], 0, 0, 0, 0, 0], [0; 8]),
        14 => ([high[6], high[7], 0, 0, 0, 0, 0, 0], [0; 8]),
        15 => ([high[7], 0, 0, 0, 0, 0, 0, 0], [0; 8]),
        _ => ([0; 8], [0; 8]),
    }
}

fn shift_left(low: [u16; 8], high: [u16; 8], shift_amount: u8) -> ([u16; 8], [u16; 8]) {
    match shift_amount {
        0 => (low, high),
        1 => (
            [0, low[0], low[1], low[2], low[3], low[4], low[5], low[6]],
            [
                low[7], high[0], high[1], high[2], high[3], high[4], high[5], high[6],
            ],
        ),
        2 => (
            [0, 0, low[0], low[1], low[2], low[3], low[4], low[5]],
            [
                low[6], low[7], high[0], high[1], high[2], high[3], high[4], high[5],
            ],
        ),
        3 => (
            [0, 0, 0, low[0], low[1], low[2], low[3], low[4]],
            [
                low[5], low[6], low[7], high[0], high[1], high[2], high[3], high[4],
            ],
        ),
        4 => (
            [0, 0, 0, 0, low[0], low[1], low[2], low[3]],
            [
                low[4], low[5], low[6], low[7], high[0], high[1], high[2], high[3],
            ],
        ),
        5 => (
            [0, 0, 0, 0, 0, low[0], low[1], low[2]],
            [
                low[3], low[4], low[5], low[6], low[7], high[0], high[1], high[2],
            ],
        ),
        6 => (
            [0, 0, 0, 0, 0, 0, low[0], low[1]],
            [
                low[2], low[3], low[4], low[5], low[6], low[7], high[0], high[1],
            ],
        ),
        7 => (
            [0, 0, 0, 0, 0, 0, 0, low[0]],
            [
                low[1], low[2], low[3], low[4], low[5], low[6], low[7], high[0],
            ],
        ),
        8 => (
            [0; 8],
            [
                low[0], low[1], low[2], low[3], low[4], low[5], low[6], low[7],
            ],
        ),
        9 => (
            [0; 8],
            [0, low[0], low[1], low[2], low[3], low[4], low[5], low[6]],
        ),
        10 => (
            [0; 8],
            [0, 0, low[0], low[1], low[2], low[3], low[4], low[5]],
        ),
        11 => ([0; 8], [0, 0, 0, low[0], low[1], low[2], low[3], low[4]]),
        12 => ([0; 8], [0, 0, 0, 0, low[0], low[1], low[2], low[3]]),
        13 => ([0; 8], [0, 0, 0, 0, 0, low[0], low[1], low[2]]),
        14 => ([0; 8], [0, 0, 0, 0, 0, 0, low[0], low[1]]),
        15 => ([0; 8], [0, 0, 0, 0, 0, 0, 0, low[0]]),
        _ => ([0; 8], [0; 8]),
    }
}

fn zip16(low: [u16; 8], high: [u16; 8]) -> ([u16; 8], [u16; 8]) {
    (
        [
            low[0], high[0], low[1], high[1], low[2], high[2], low[3], high[3],
        ],
        [
            low[4], high[4], low[5], high[5], low[6], high[6], low[7], high[7],
        ],
    )
}

fn unzip16(low: [u16; 8], high: [u16; 8]) -> ([u16; 8], [u16; 8]) {
    (
        [
            low[0], low[2], low[4], low[6], high[0], high[2], high[4], high[6],
        ],
        [
            low[1], low[3], low[5], low[7], high[1], high[3], high[5], high[7],
        ],
    )
}

fn zip32(low: [u16; 8], high: [u16; 8]) -> ([u16; 8], [u16; 8]) {
    (
        [
            low[0], low[1], high[0], high[1], low[2], low[3], high[2], high[3],
        ],
        [
            low[4], low[5], high[4], high[5], low[6], low[7], high[6], high[7],
        ],
    )
}

fn unzip32(low: [u16; 8], high: [u16; 8]) -> ([u16; 8], [u16; 8]) {
    (
        [
            low[0], low[1], low[4], low[5], high[0], high[1], high[4], high[5],
        ],
        [
            low[2], low[3], low[6], low[7], high[2], high[3], high[6], high[7],
        ],
    )
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum Opcode {
    ShiftLeft(u8),
    ShiftRight(u8),
    Zip16,
    UnZip16,
    Zip32,
    UnZip32,
}

fn main() {
    const LOW: [u16; 8] = [1, 2, 3, 4, 5, 6, 7, 8];
    const HIGH: [u16; 8] = [9, 10, 11, 12, 13, 14, 15, 16];
    for i in 0..=16 {
        println!("SHIFT LEFT {}: {:?}", i, shift_left(LOW, HIGH, i));
    }
    for i in 0..=16 {
        println!("SHIFT RIGHT {}: {:?}", i, shift_right(LOW, HIGH, i));
    }
    println!("ZIP16: {:?}", zip16(LOW, HIGH));
    println!("UNZIP16: {:?}", unzip16(LOW, HIGH));
    println!("ZIP32: {:?}", zip32(LOW, HIGH));
    println!("UNZIP32: {:?}", unzip32(LOW, HIGH));

    const TARGET: [u16; 8] = [8, 7, 6, 5, 4, 3, 2, 1];

    const MAX_OPCODE: u16 = 16 + 16 + 4;

    let mut w = File::create("result.txt").unwrap();

    let valid = (0..MAX_OPCODE)
        .into_iter()
        .flat_map(|i| {
            let mut valid: Vec<([Opcode; 6], [[usize; 2]; 6])> = vec![];
            let mut registers = [[0u16; 8]; 4];
            registers[0] = LOW;
            let mut instructions = [Opcode::Zip16; 6];
            let mut instruction_index = [0u16; 6];
            instruction_index[5] = i;
            let mut end = false;
            while !end {
                for i in 0..instructions.len() {
                    instructions[i] = match instruction_index[i] {
                        0..16 => Opcode::ShiftLeft(instruction_index[i] as u8),
                        16..32 => Opcode::ShiftRight(instruction_index[i] as u8 - 16),
                        32 => Opcode::Zip16,
                        33 => Opcode::UnZip16,
                        34 => Opcode::Zip32,
                        35 => Opcode::UnZip32,
                        _ => Opcode::Zip32,
                    }
                }

                let mut reg_index = [[0usize; 2]; 6];

                let mut continue_instruction = false;

                while !continue_instruction {
                    for i in 0.. {
                        reg_index[i / 2][i % 2] += 1;
                        if reg_index[i / 2][i % 2] == registers.len() {
                            reg_index[i / 2][i % 2] = 0;
                            if i == (reg_index.len() * 2) - 1 {
                                continue_instruction = true;
                                break;
                            }
                        } else {
                            break;
                        }
                    }
                }

                for (inst, reg) in instructions.iter().zip(reg_index) {
                    match inst {
                        Opcode::ShiftLeft(s) => {
                            (registers[reg[0]], registers[reg[1]]) =
                                shift_left(registers[reg[0]], registers[reg[1]], *s);
                        },
                        Opcode::ShiftRight(s) => {
                            (registers[reg[0]], registers[reg[1]]) =
                                shift_right(registers[reg[0]], registers[reg[1]], *s);
                        },
                        Opcode::Zip16 => {
                            (registers[reg[0]], registers[reg[1]]) =
                                zip16(registers[reg[0]], registers[reg[1]]);
                        },
                        Opcode::UnZip16 => {
                            (registers[reg[0]], registers[reg[1]]) =
                                unzip16(registers[reg[0]], registers[reg[1]]);
                        },
                        Opcode::Zip32 => {
                            (registers[reg[0]], registers[reg[1]]) =
                                zip32(registers[reg[0]], registers[reg[1]]);
                        },
                        Opcode::UnZip32 => {
                            (registers[reg[0]], registers[reg[1]]) =
                                unzip32(registers[reg[0]], registers[reg[1]]);
                        },
                    }

                    if registers.iter().any(|&r| r == TARGET) {
                        valid.push((instructions, reg_index));
                        println!("VAILD: {:?}", (instructions, reg_index));
                        writeln!(&mut w, "{:?}", (instructions, reg_index)).unwrap();
                        break;
                    }
                }

                for i in 0.. {
                    instruction_index[i] += 1;
                    if i == instruction_index.len() - 4 {
                        println!("AT {}/{}", instruction_index[i], MAX_OPCODE)
                    }
                    if instruction_index[i] == MAX_OPCODE {
                        instruction_index[i] = 0;
                        if i == instruction_index.len() - 2 {
                            end = true;
                            break;
                        }
                    } else {
                        break;
                    }
                }
            }
            valid
        })
        .collect::<Vec<_>>();

    println!("ALL VAILD: {:?}", valid);

    writeln!(&mut w, "{:?}", valid).unwrap();
}
