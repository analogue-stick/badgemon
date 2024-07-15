//Library to make rust functions of the ESP32S3's SIMD instructions.v
use log::{debug, warn};
use std::simd::{prelude::*, ToBytes};

pub struct ESP32S3 {
    areg: [u32; 16],
    freg: [f32; 16],
    // only 8 of these really exist. the rest are for debug
    qreg: [u16x8; 16],
    sar: u8,
    sar_byte: u8,
    accx: u64,
    qacc: u64x8,
    fft_bit_width: u8,
    ua_state: u128,
}

type Reg = usize;

fn validate_areg(reg: Reg) {
    if reg >= 16 {
        panic!("AREG {} DOES NOT EXIST", reg);
    }
}

fn validate_freg(reg: Reg) {
    if reg >= 16 {
        panic!("FREG {} DOES NOT EXIST", reg);
    }
}

fn validate_sel(sel: u8, sel_size: u8) {
    if sel >= sel_size {
        panic!("SEL {} TOO HIGH", sel);
    }
}

fn validate_qreg(reg: Reg) {
    if reg >= 16 {
        panic!("QREG {} DOES NOT EXIST", reg);
    }
    if reg >= 8 {
        #[cfg(feature = "panic_on_exqreg")]
        {
            panic!("EXQREG {} IS NOT ALLOWED", reg);
        }
        #[cfg(not(feature = "panic_on_exqreg"))]
        {
            warn!("EXQREG {} used", reg)
        }
    }
}

fn validate_register_share(reg: Reg, others: &[Reg]) {
    if others.contains(&reg) {
        warn!("Register {} is used during two parallel operations", reg)
    }
}

fn validate_signed_immediate(imm: i32, max: i32, min: i32) {
    if imm < min {
        warn!("Immediate {} is less than the minimum ({})", imm, min)
    }
    #[cfg(debug_assertions)]
    if imm > max {
        warn!("Immediate {} is more than the maximum ({})", imm, max)
    }
}

fn validate_signed_immediate_by_bits(imm: i32, bitwidth: usize) {
    validate_signed_immediate(imm, (1 << (bitwidth - 1)) - 1, -(1 << (bitwidth - 1)))
}

fn validate_signed_mask(imm: i32, mask: i32) {
    if imm & mask != imm {
        warn!("Immediate {} does not conform to mask ({})", imm, mask)
    }
}

fn validate_unsigned_immediate(imm: u32, max: u32, min: u32) {
    if imm < min {
        warn!("Immediate {} is less than the minimum ({})", imm, min)
    }
    if imm > max {
        warn!("Immediate {} is more than the maximum ({})", imm, max)
    }
}

fn validate_unsigned_immediate_by_bits(imm: u32, bitwidth: usize) {
    validate_unsigned_immediate(imm, (1 << bitwidth) - 1, 0)
}

fn validate_unsigned_mask(imm: u32, mask: u32) {
    if imm & mask != imm {
        warn!("Immediate {} does not conform to mask ({})", imm, mask)
    }
}

fn load128(buf: &[u16x8], ac: usize) -> u16x8 {
    debug!("load128 a{}", ac);
    if let Some(val) = buf.get(ac >> 4) {
        debug!("loaded {:?}", val);
        *val
    } else {
        panic!(
            "OUT OF BOUNDS: tried load128 from address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn store128(buf: &mut [u16x8], val: u16x8, ac: usize) {
    debug!("store128 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        *n_val = val;
        debug!("stored {:?}", val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store128 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn load64(buf: &[u16x8], ac: usize) -> u16x4 {
    debug!("load64 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let res = if ac & 0b100 > 0 {
            val.rotate_elements_right::<4>()
        } else {
            val
        }
        .resize::<4>(0);
        debug!("loaded {:?}", res);
        res
    } else {
        panic!(
            "OUT OF BOUNDS: tried load64 from address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn store64(buf: &mut [u16x8], val: u16x4, ac: usize) {
    debug!("store64 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        let large = val.resize::<8>(0);
        if ac & 0b100 > 0 {
            *n_val = simd_swizzle!(*n_val, large, [0, 1, 2, 3, 8, 9, 10, 11]);
        } else {
            *n_val = simd_swizzle!(*n_val, large, [8, 9, 10, 11, 4, 5, 6, 7]);
        }
        debug!("stored {:?}", *n_val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store64 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn load32(buf: &[u16x8], ac: usize) -> u16x2 {
    debug!("load32 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let mut val = val;
        for _ in 0..((ac & 0b110) >> 1)
        {
            val = val.rotate_elements_right::<2>()
        }
        let res = val.resize::<2>(0);
        debug!("loaded {:?}", res);
        res
    } else {
        panic!(
            "OUT OF BOUNDS: tried load32 from address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn store32(buf: &mut [u16x8], val: u16x4, ac: usize) {
    debug!("store32 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        let large = val.resize::<8>(0);
        match ac & 0b110 {
            2 => *n_val = simd_swizzle!(*n_val, large, [0, 1, 2, 3, 8, 9, 10, 11]);
            4 => *n_val = simd_swizzle!(*n_val, large, [8, 9, 10, 11, 4, 5, 6, 7]);
        }
        debug!("stored {:?}", *n_val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store32 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

impl ESP32S3 {
    fn load128(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        debug!("load128 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load128(buf, self.areg[ac] as usize)
    }

    fn load128incp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        debug!("load128incp q{}, a{}", qu, ac);
        self.load128(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(16);
    }

    fn store128(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        debug!("store128 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store128(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store128incp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        debug!("store128incp q{}, a{}", qv, ac);
        self.store128(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(16);
    }

    pub fn andq(&mut self, qa: Reg, qx: Reg, qy: Reg) {
        debug!("EE.ANDQ q{}, q{}, q{}", qa, qx, qy);
        validate_qreg(qa);
        validate_qreg(qx);
        validate_qreg(qy);
        self.qreg[qa] = self.qreg[qx] & self.qreg[qy];
    }

    pub fn bitrev(&mut self, qa: Reg, ac: Reg) {
        debug!("EE.BITREV q{}, a{}", qa, ac);
        validate_qreg(qa);
        validate_areg(ac);
        let mut temp =
            u16x8::from_array([0, 1, 2, 3, 4, 5, 6, 7]) + u16x8::splat(self.areg[ac] as u16);
        temp &= u16x8::splat((1 << self.fft_bit_width) - 1);
        self.qreg[qa] =
            temp.simd_max(temp.reverse_bits() >> u16x8::splat(16 - self.fft_bit_width as u16));
        self.areg[ac] = self.areg[ac].wrapping_add(8);
    }

    pub fn cmul_s16(&mut self, qz: Reg, qx: Reg, qy: Reg, sel4: u8) {
        debug!("EE.CMUL.S16 q{}, q{}, q{}, sel{}", qz, qx, qy, sel4);
        validate_sel(sel4, 4);
        validate_qreg(qz);
        validate_qreg(qx);
        validate_qreg(qy);
        let a = simd_swizzle!(self.qreg[qx], [0, 0, 2, 2, 4, 4, 6, 6]).cast() as i16x8;
        let b = simd_swizzle!(self.qreg[qy], [0, 1, 2, 3, 4, 5, 6, 7]).cast() as i16x8;
        let mut c = simd_swizzle!(self.qreg[qx], [1, 1, 3, 3, 5, 5, 7, 7]).cast() as i16x8;
        let d = simd_swizzle!(self.qreg[qy], [1, 0, 3, 2, 5, 4, 7, 6]).cast() as i16x8;
        if sel4 >> 1 == 0 {
            c = c * i16x8::from_array([-1, 1, -1, 1, -1, 1, -1, 1]);
        } else {
            c = c * i16x8::from_array([1, -1, 1, -1, 1, -1, 1, -1]);
        }
        let c = c;

        let res = ((a * b) + (c * d)) >> (self.sar & 0x3F) as i16;
        if sel4 & 1 == 0 {
            self.qreg[qz] = simd_swizzle!(
                res.cast() as u16x8,
                self.qreg[qz],
                [0, 1, 2, 3, 12, 13, 14, 15]
            );
        } else {
            self.qreg[qz] = simd_swizzle!(
                res.cast() as u16x8,
                self.qreg[qz],
                [9, 10, 11, 12, 4, 5, 6, 7]
            );
        }
    }

    pub fn cmul_s16_ld_incp(
        &mut self,
        buf: &[u16x8],
        qu: Reg,
        ac: Reg,
        qz: Reg,
        qx: Reg,
        qy: Reg,
        sel4: u8,
    ) {
        debug!(
            "EE.CMUL.S16.LD.INCP q{}, a{}, q{}, q{}, q{}, sel{}",
            qu, ac, qz, qx, qy, sel4
        );
        validate_qreg(qu);
        validate_areg(ac);
        validate_register_share(qu, &[qz, qy, qx]);
        self.cmul_s16(qz, qx, qy, sel4);
        self.load128incp(buf, qu, ac);
    }

    pub fn cmul_s16_st_incp(
        &mut self,
        buf: &mut [u16x8],
        qv: Reg,
        ac: Reg,
        qz: Reg,
        qx: Reg,
        qy: Reg,
        sel4: u8,
    ) {
        debug!(
            "EE.CMUL.S16.ST.INCP q{}, a{}, q{}, q{}, q{}, sel{}",
            qv, ac, qz, qx, qy, sel4
        );
        validate_qreg(qv);
        validate_areg(ac);
        validate_register_share(qv, &[qz, qy, qx]);
        self.cmul_s16(qz, qx, qy, sel4);
        self.store128incp(buf, qv, ac);
    }

    pub fn ld_128_usar_ip(&mut self, buf: &[u16x8], qu: Reg, ac: Reg, imm: i32) {
        debug!("EE.LD.128.USAR.IP q{}, a{}, imm{}", qu, ac, imm);
        validate_qreg(qu);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 12);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        self.load128(buf, qu, ac);
        self.sar_byte = self.areg[ac] as u8 & 0xF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 4) as i8 as i32) << 4);
    }

    pub fn ld_128_usar_xp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg, ad: Reg) {
        debug!("EE.LD.128.USAR.XP q{}, a{}, a{}", qu, ac, ad);
        validate_qreg(qu);
        validate_areg(ac);
        validate_areg(ad);
        self.load128(buf, qu, ac);
        self.sar_byte = self.areg[ac] as u8 & 0xF;
        self.areg[ac] = self.areg[ac].wrapping_add(self.areg[ad]);
    }

    pub fn ld_accx_ip(&mut self, buf: &[u16x8], ac: Reg, imm: i32) {
        debug!("EE.LD.ACCX.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 11);
        validate_signed_mask(imm, 0xFFFFFFF8u32 as i32);
        let mut both = load128(buf, ac);
        if imm & 0b100 > 0 {
            both = both.rotate_elements_right::<4>();
        }
        self.accx = u64::from_le_bytes(both.resize::<4>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);
    }

    /*pub fn ls_qacc_h_h_32_ip(&mut self, buf: &[u16x8], ac: Reg, imm: i32) {
        debug!("EE.LD.QACC_H.H.32.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 10);
        validate_signed_mask(imm, 0xFFFFFFFCu32 as i32);
        let mut both = load128(buf, ac);
        for _ in (imm & 0b110) >> 1 {
            both = both.rotate_elements_right::<2>();
        }
        self.qacc = u32::from_le_bytes(both.resize::<2>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);
    }*/

    pub fn ld_ua_state_ip(&mut self, buf: &[u16x8], ac: Reg, imm: i32) {
        debug!("EE.LD.UA_STATE.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 12);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        self.ua_state = u128::from_le_bytes(load128(buf, ac).to_le_bytes().into());
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 4) as i8 as i32) << 4);
    }

    fn ldf_128(&mut self, buf: &[u16x8], fu0: Reg, fu1: Reg, fu2: Reg, fu3: Reg, ac: Reg) {
        validate_areg(ac);
        validate_freg(fu0);
        validate_freg(fu1);
        validate_freg(fu2);
        validate_freg(fu3);
        let data = load128(buf, ac);
        for (f, a) in data
            .as_array()
            .array_chunks::<2>()
            .map(|ar| {
                f32::from_le_bytes(
                    [ar[0].to_le_bytes(), ar[1].to_le_bytes()]
                        .as_flattened()
                        .try_into()
                        .unwrap(),
                )
            })
            .zip([fu0, fu1, fu2, fu3])
        {
            self.freg[a] = f;
        }
    }

    fn ldf_64(&mut self, buf: &[u16x8], fu0: Reg, fu1: Reg, ac: Reg) {
        validate_areg(ac);
        validate_freg(fu0);
        validate_freg(fu1);
        let data = load64(buf, ac);
        for (f, a) in data
            .as_array()
            .array_chunks::<2>()
            .map(|ar| {
                f32::from_le_bytes(
                    [ar[0].to_le_bytes(), ar[1].to_le_bytes()]
                        .as_flattened()
                        .try_into()
                        .unwrap(),
                )
            })
            .zip([fu0, fu1, fu2, fu3])
        {
            self.freg[a] = f;
        }
    }

    pub fn ldf_128_ip(
        &mut self,
        buf: &[u16x8],
        fu0: Reg,
        fu1: Reg,
        fu2: Reg,
        fu3: Reg,
        ac: Reg,
        imm: i32,
    ) {
        debug!(
            "EE.LDF.128.IP fu{}, fu{}, fu{}, fu{}, a{}, imm{}",
            fu3, fu2, fu1, fu0, ac, imm
        );
        validate_areg(ac);
        validate_freg(fu0);
        validate_freg(fu1);
        validate_freg(fu2);
        validate_freg(fu3);
        validate_signed_immediate_by_bits(imm, 8);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        let data = load128(buf, ac);
        for (f, a) in data
            .as_array()
            .array_chunks::<2>()
            .map(|ar| {
                f32::from_le_bytes(
                    [ar[0].to_le_bytes(), ar[1].to_le_bytes()]
                        .as_flattened()
                        .try_into()
                        .unwrap(),
                )
            })
            .zip([fu0, fu1, fu2, fu3])
        {
            self.freg[a] = f;
        }
        self.areg[ac] = self.areg[ac].wrapping_add_signed(imm as i8 as i32);
    }
}
