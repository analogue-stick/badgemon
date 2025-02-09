//Library to make rust functions of the ESP32S3's SIMD instructions.
use std::{
    ops::IndexMut,
    simd::{prelude::*, ToBytes},
};

use log::{debug, trace, warn};

pub struct ESP32S3 {
    areg:          [u32; 16],
    freg:          [f32; 16],
    // only 8 of these really exist. the rest are for debug
    qreg:          [u16x8; 16],
    sar:           u8,
    sar_byte:      u8,
    accx:          u64,
    qacc:          u64x8,
    fft_bit_width: u8,
    ua_state:      u128,
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
    trace!("load128 a{}", ac);
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
    trace!("store128 a{}", ac);
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

fn load64_int(val: u16x8, ac: usize) -> u16x4 {
    if ac > 0 {
        val.rotate_elements_right::<4>()
    } else {
        val
    }
    .resize::<4>(0)
}

fn load64(buf: &[u16x8], ac: usize) -> u16x4 {
    trace!("load64 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let res = load64_int(val, (ac & 0b1000) >> 3);
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

fn store64_int(n_val: &mut u16x8, val: u16x4, ac: usize) {
    let large = val.resize::<8>(0);
    if ac > 0 {
        *n_val = simd_swizzle!(*n_val, large, [8, 9, 10, 11, 4, 5, 6, 7]);
    } else {
        *n_val = simd_swizzle!(*n_val, large, [0, 1, 2, 3, 8, 9, 10, 11]);
    }
}

fn store64(buf: &mut [u16x8], val: u16x4, ac: usize) {
    trace!("store64 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        store64_int(n_val, val, (ac & 0b1000) >> 3);
        debug!("stored {:?}", *n_val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store64 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn load32_int(mut val: u16x8, ac: usize) -> u16x2 {
    for _ in 0..ac {
        val = val.rotate_elements_right::<2>();
    }
    val.resize::<2>(0)
}

fn load32(buf: &[u16x8], ac: usize) -> u16x2 {
    trace!("load32 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let res = load32_int(val, (ac & 0b1100) >> 2);
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

fn store32_int(n_val: &mut u16x8, val: u16x2, ac: usize) {
    let large = val.resize::<8>(0);
    match ac {
        0 => {
            *n_val = simd_swizzle!(*n_val, large, [8, 9, 2, 3, 4, 5, 6, 7]);
        },
        1 => {
            *n_val = simd_swizzle!(*n_val, large, [0, 1, 8, 9, 4, 5, 6, 7]);
        },
        2 => {
            *n_val = simd_swizzle!(*n_val, large, [0, 1, 2, 3, 8, 9, 6, 7]);
        },
        3 => {
            *n_val = simd_swizzle!(*n_val, large, [0, 1, 2, 3, 4, 5, 8, 9]);
        },
        _ => unreachable!(),
    }
}

fn store32(buf: &mut [u16x8], val: u16x2, ac: usize) {
    trace!("store32 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        store32_int(n_val, val, (ac & 0b1100) >> 2);
        debug!("stored {:?}", val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store32 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn load16_int(val: u16x8, ac: usize) -> u16 {
    val[ac]
}

fn load16(buf: &[u16x8], ac: usize) -> u16 {
    trace!("load16 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let res = load16_int(val, (ac & 0b1110) >> 1);
        debug!("loaded {:?}", res);
        res
    } else {
        panic!(
            "OUT OF BOUNDS: tried load16 from address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn store16_int(n_val: &mut u16x8, val: u16, ac: usize) {
    *n_val.index_mut(ac) = val;
}

fn store16(buf: &mut [u16x8], val: u16, ac: usize) {
    trace!("store16 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        store16_int(n_val, val, (ac & 0b1110) >> 1);
        debug!("stored {:?}", val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store16 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn load8_int(val: u16x8, ac: usize) -> u8 {
    let pos = ac >> 1;
    if ac & 1 > 0 {
        (val[pos] >> 8) as u8
    } else {
        (val[pos] & 0xFF) as u8
    }
}

fn load8(buf: &[u16x8], ac: usize) -> u8 {
    trace!("load8 a{}", ac);
    if let Some(&val) = buf.get(ac >> 4) {
        let res = load8_int(val, ac & 0b1111);
        debug!("loaded {:?}", res);
        res
    } else {
        panic!(
            "OUT OF BOUNDS: tried load8 from address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

fn store8_int(n_val: &mut u16x8, val: u8, ac: usize) {
    let pos = ac >> 1;
    if ac & 1 > 0 {
        *n_val.index_mut(pos) = (n_val[pos] & 0xFF) | ((val as u16) << 8);
    } else {
        *n_val.index_mut(pos) = (n_val[pos] & 0xFF00) | (val as u16);
    }
}

fn store8(buf: &mut [u16x8], val: u8, ac: usize) {
    trace!("store8 a{}", ac);
    if let Some(n_val) = buf.get_mut(ac >> 4) {
        store8_int(n_val, val, ac & 0b1111);
        debug!("stored {:?}", val);
    } else {
        panic!(
            "OUT OF BOUNDS: tried store8 to address {} in array of length {}.",
            ac >> 4,
            buf.len()
        )
    }
}

impl ESP32S3 {
    fn load128(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load128 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load128(buf, self.areg[ac] as usize)
    }

    fn load128incp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load128incp q{}, a{}", qu, ac);
        self.load128(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(16);
    }

    fn load128decp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load128decp q{}, a{}", qu, ac);
        self.load128(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_sub(16);
    }

    fn store128(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store128 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store128(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store128incp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store128incp q{}, a{}", qv, ac);
        self.store128(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(16);
    }

    fn store128decp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store128decp q{}, a{}", qv, ac);
        self.store128(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_sub(16);
    }

    /*fn load64(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load64 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load64(buf, self.areg[ac] as usize)
    }

    fn load64incp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load64incp q{}, a{}", qu, ac);
        self.load64(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(8);
    }

    fn store64(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store64 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store64(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store64incp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store64incp q{}, a{}", qv, ac);
        self.store64(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(8);
    }

    fn load32(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load32 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load32(buf, self.areg[ac] as usize)
    }

    fn load32incp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load32incp q{}, a{}", qu, ac);
        self.load32(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(4);
    }

    fn store32(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store32 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store32(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store32incp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store32incp q{}, a{}", qv, ac);
        self.store32(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(4);
    }

    fn load16(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load16 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load16(buf, self.areg[ac] as usize)
    }

    fn load16incp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg) {
        trace!("load16incp q{}, a{}", qu, ac);
        self.load16(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(2);
    }

    fn store16(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store16 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store16(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store16incp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg) {
        trace!("store16incp q{}, a{}", qv, ac);
        self.store16(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(2);
    }

    fn load8(&mut self, buf: &[u8x8], qu: Reg, ac: Reg) {
        trace!("load8 q{}, a{}", qu, ac);
        validate_qreg(qu);
        validate_areg(ac);
        self.qreg[qu] = load8(buf, self.areg[ac] as usize)
    }

    fn load8incp(&mut self, buf: &[u8x8], qu: Reg, ac: Reg) {
        trace!("load8incp q{}, a{}", qu, ac);
        self.load8(buf, qu, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(1);
    }

    fn store8(&mut self, buf: &mut [u8x8], qv: Reg, ac: Reg) {
        trace!("store8 q{}, a{}", qv, ac);
        validate_qreg(qv);
        validate_areg(ac);
        store8(buf, self.qreg[qv], self.areg[ac] as usize)
    }

    fn store8incp(&mut self, buf: &mut [u8x8], qv: Reg, ac: Reg) {
        trace!("store8incp q{}, a{}", qv, ac);
        self.store8(buf, qv, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(1);
    }*/

    pub fn andq(&mut self, qa: Reg, qx: Reg, qy: Reg) {
        trace!("EE.ANDQ q{}, q{}, q{}", qa, qx, qy);
        validate_qreg(qa);
        validate_qreg(qx);
        validate_qreg(qy);
        self.qreg[qa] = self.qreg[qx] & self.qreg[qy];
    }

    pub fn bitrev(&mut self, qa: Reg, ac: Reg) {
        trace!("EE.BITREV q{}, a{}", qa, ac);
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
        trace!("EE.CMUL.S16 q{}, q{}, q{}, sel{}", qz, qx, qy, sel4);
        validate_sel(sel4, 4);
        validate_qreg(qz);
        validate_qreg(qx);
        validate_qreg(qy);
        let a = simd_swizzle!(self.qreg[qx], [0, 0, 2, 2, 4, 4, 6, 6]).cast() as i16x8;
        let b = simd_swizzle!(self.qreg[qy], [0, 1, 2, 3, 4, 5, 6, 7]).cast() as i16x8;
        let mut c = simd_swizzle!(self.qreg[qx], [1, 1, 3, 3, 5, 5, 7, 7]).cast() as i16x8;
        let d = simd_swizzle!(self.qreg[qy], [1, 0, 3, 2, 5, 4, 7, 6]).cast() as i16x8;
        if sel4 >> 1 == 0 {
            c *= i16x8::from_array([-1, 1, -1, 1, -1, 1, -1, 1]);
        } else {
            c *= i16x8::from_array([1, -1, 1, -1, 1, -1, 1, -1]);
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
        trace!(
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
        trace!(
            "EE.CMUL.S16.ST.INCP q{}, a{}, q{}, q{}, q{}, sel{}",
            qv, ac, qz, qx, qy, sel4
        );
        validate_qreg(qv);
        validate_areg(ac);
        validate_register_share(qv, &[qz, qy, qx]);
        self.cmul_s16(qz, qx, qy, sel4);
        self.store128incp(buf, qv, ac);
    }

    pub fn fft_ams_s16_ld_incp(
        &mut self,
        _buf: &[u16x8],
        qu: Reg,
        ac: Reg,
        qz: Reg,
        qz1: Reg,
        qx: Reg,
        qy: Reg,
        qm: Reg,
        sel2: u8,
    ) {
        trace!(
            "EE.FFT.AMS.S16.LD.INCP q{}, a{}, q{}, q{}, q{}, q{}, q{}, sel{}",
            qu, ac, qz, qz1, qx, qy, qm, sel2
        );
        validate_qreg(qu);
        validate_areg(ac);
        validate_qreg(qz);
        validate_qreg(qz1);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_qreg(qm);
        validate_sel(sel2, 2);
        todo!();
    }

    pub fn fft_ams_s16_ld_incp_uaup(
        &mut self,
        _buf: &[u16x8],
        qu: Reg,
        ac: Reg,
        qz: Reg,
        qz1: Reg,
        qx: Reg,
        qy: Reg,
        qm: Reg,
        sel2: u8,
    ) {
        trace!(
            "EE.FFT.AMS.S16.LD.INCP.UAUP q{}, a{}, q{}, q{}, q{}, q{}, q{}, sel{}",
            qu, ac, qz, qz1, qx, qy, qm, sel2
        );
        validate_qreg(qu);
        validate_areg(ac);
        validate_qreg(qz);
        validate_qreg(qz1);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_qreg(qm);
        validate_sel(sel2, 2);
        todo!();
    }

    pub fn fft_ams_s16_ld_r32_decp(
        &mut self,
        _buf: &[u16x8],
        qu: Reg,
        ac: Reg,
        qz: Reg,
        qz1: Reg,
        qx: Reg,
        qy: Reg,
        qm: Reg,
        sel2: u8,
    ) {
        trace!(
            "EE.FFT.AMS.S16.LD.R32.DECP q{}, a{}, q{}, q{}, q{}, q{}, q{}, sel{}",
            qu, ac, qz, qz1, qx, qy, qm, sel2
        );
        validate_qreg(qu);
        validate_areg(ac);
        validate_qreg(qz);
        validate_qreg(qz1);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_qreg(qm);
        validate_sel(sel2, 2);
        todo!();
    }

    pub fn fft_ams_s16_st_incp(
        &mut self,
        _buf: &mut [u16x8],
        qv: Reg,
        qz1: Reg,
        at: Reg,
        ac: Reg,
        qx: Reg,
        qy: Reg,
        qm: Reg,
        sel2: u8,
    ) {
        trace!(
            "EE.FFT.AMS.S16.ST.INCP q{}, q{}, a{}, a{}, q{}, q{}, q{}, sel{}",
            qv, qz1, at, ac, qx, qy, qm, sel2
        );
        validate_qreg(qv);
        validate_qreg(qz1);
        validate_areg(at);
        validate_areg(ac);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_qreg(qm);
        validate_sel(sel2, 2);
        todo!();
    }

    pub fn fft_cmul_s16_ld_xp(
        &mut self,
        _buf: &[u16x8],
        qu: Reg,
        ac: Reg,
        ad: Reg,
        qz: Reg,
        qx: Reg,
        qy: Reg,
        sel8: u8,
    ) {
        trace!(
            "EE.FFT.CMUL.S16.LD.XP q{}, a{}, a{}, q{}, q{}, q{}, sel{}",
            qu, ac, ad, qz, qx, qy, sel8
        );
        validate_qreg(qu);
        validate_areg(ac);
        validate_areg(ad);
        validate_qreg(qz);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_sel(sel8, 8);
        todo!();
    }

    pub fn fft_cmul_s16_st_xp(
        &mut self,
        _buf: &mut [u16x8],
        qx: Reg,
        qy: Reg,
        qv: Reg,
        ac: Reg,
        ad: Reg,
        sel8: u8,
        upd4: u8,
        sar4: u8,
    ) {
        trace!(
            "EE.FFT.CMUL.S16.ST.XP q{}, q{}, q{}, a{}, a{}, sel{}, upd{}, sar{}",
            qx, qy, qv, ac, ad, sel8, upd4, sar4
        );
        validate_qreg(qx);
        validate_qreg(qy);
        validate_qreg(qv);
        validate_areg(ac);
        validate_areg(ad);
        validate_sel(sel8, 8);
        validate_sel(upd4, 4);
        validate_sel(sar4, 4);
        todo!();
    }

    pub fn fft_r2bf_s16(&mut self, qa0: Reg, qa1: Reg, qx: Reg, qy: Reg, sel2: u8) {
        trace!(
            "EE.FFT.R2BF.S16 q{}, q{}, q{}, q{}, sel{}",
            qa0, qa1, qx, qy, sel2
        );
        validate_qreg(qa0);
        validate_qreg(qa1);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_sel(sel2, 2);
        todo!();
    }

    pub fn fft_r2bf_s16_st_incp(
        &mut self,
        _buf: &mut [u16x8],
        qa0: Reg,
        qx: Reg,
        qy: Reg,
        ac: Reg,
        sar4: u8,
    ) {
        trace!(
            "EE.FFT.R2BF.S16.ST.INCP q{}, q{}, q{}, a{}, sar{}",
            qa0, qx, qy, ac, sar4
        );
        validate_qreg(qa0);
        validate_qreg(qx);
        validate_qreg(qy);
        validate_areg(ac);
        validate_sel(sar4, 4);
        todo!();
    }

    // todo: Should be word big endian
    pub fn fft_vst_r32_decp(&mut self, buf: &mut [u16x8], qv: Reg, ac: Reg, sar2: u8) {
        trace!(
            "EE.FFT.VST.R32.DECP q{}, a{}, sar{}",
            qv, ac, sar2
        );
        validate_qreg(qv);
        validate_areg(ac);
        validate_sel(sar2, 2);
        warn!("EE.FFT.VST.R32.DECP function should be big endian but is not");
        store128(buf, self.qreg[qv] >> (sar2 as u16), self.areg[ac] as usize);
        self.areg[ac] = self.areg[ac].wrapping_sub(16);
    }

    pub fn ld_128_usar_ip(&mut self, buf: &[u16x8], qu: Reg, ac: Reg, imm: i32) {
        trace!("EE.LD.128.USAR.IP q{}, a{}, imm{}", qu, ac, imm);
        validate_qreg(qu);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 12);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        self.load128(buf, qu, ac);
        self.sar_byte = self.areg[ac] as u8 & 0xF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 4) as i8 as i32) << 4);
    }

    pub fn ld_128_usar_xp(&mut self, buf: &[u16x8], qu: Reg, ac: Reg, ad: Reg) {
        trace!("EE.LD.128.USAR.XP q{}, a{}, a{}", qu, ac, ad);
        validate_qreg(qu);
        validate_areg(ac);
        validate_areg(ad);
        self.load128(buf, qu, ac);
        self.sar_byte = self.areg[ac] as u8 & 0xF;
        self.areg[ac] = self.areg[ac].wrapping_add(self.areg[ad]);
    }

    pub fn ld_accx_ip(&mut self, buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.ACCX.IP a{}, imm{}", ac, imm);
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

    pub fn ld_qacc_h_h_32_ip(&mut self, _buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.QACC_H.H.32.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 10);
        validate_signed_mask(imm, 0xFFFFFFFCu32 as i32);
        todo!();
        /*let mut both = load128(buf, ac);
        for _ in (imm & 0b110) >> 1 {
            both = both.rotate_elements_right::<2>();
        }
        self.qacc = u32::from_le_bytes(both.resize::<2>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);*/
    }

    pub fn ld_qacc_h_l_128_ip(&mut self, _buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.QACC_H.L.128.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 12);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        todo!();
        /*let mut both = load128(buf, ac);
        for _ in (imm & 0b110) >> 1 {
            both = both.rotate_elements_right::<2>();
        }
        self.qacc = u32::from_le_bytes(both.resize::<2>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);*/
    }

    pub fn ld_qacc_l_h_32_ip(&mut self, _buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.QACC_L.H.32.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 10);
        validate_signed_mask(imm, 0xFFFFFFFCu32 as i32);
        todo!();
        /*let mut both = load128(buf, ac);
        for _ in (imm & 0b110) >> 1 {
            both = both.rotate_elements_right::<2>();
        }
        self.qacc = u32::from_le_bytes(both.resize::<2>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);*/
    }

    pub fn ld_qacc_l_l_128_ip(&mut self, _buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.QACC_L.L.128.IP a{}, imm{}", ac, imm);
        validate_areg(ac);
        validate_signed_immediate_by_bits(imm, 12);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        todo!();
        /*let mut both = load128(buf, ac);
        for _ in (imm & 0b110) >> 1 {
            both = both.rotate_elements_right::<2>();
        }
        self.qacc = u32::from_le_bytes(both.resize::<2>(0).to_le_bytes().into());
        self.accx &= 0xFF_FFFFFFFF;
        self.areg[ac] = self.areg[ac].wrapping_add_signed(((imm >> 3) as i8 as i32) << 3);*/
    }

    pub fn ld_ua_state_ip(&mut self, buf: &[u16x8], ac: Reg, imm: i32) {
        trace!("EE.LD.UA_STATE.IP a{}, imm{}", ac, imm);
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
            .zip([fu0, fu1])
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
        trace!(
            "EE.LDF.128.IP fu{}, fu{}, fu{}, fu{}, a{}, imm{}",
            fu3, fu2, fu1, fu0, ac, imm
        );
        validate_signed_immediate_by_bits(imm, 8);
        validate_signed_mask(imm, 0xFFFFFFF0u32 as i32);
        self.ldf_128(buf, fu0, fu1, fu2, fu3, ac);
        self.areg[ac] = self.areg[ac].wrapping_add_signed(imm as i8 as i32);
    }

    pub fn ldf_128_xp(
        &mut self,
        buf: &[u16x8],
        fu0: Reg,
        fu1: Reg,
        fu2: Reg,
        fu3: Reg,
        ac: Reg,
        ad: Reg,
    ) {
        trace!(
            "EE.LDF.128.XP fu{}, fu{}, fu{}, fu{}, a{}, a{}",
            fu3, fu2, fu1, fu0, ac, ad,
        );
        validate_areg(ad);
        self.ldf_128(buf, fu0, fu1, fu2, fu3, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(self.areg[ad]);
    }

    pub fn ldf_64_ip(&mut self, buf: &[u16x8], fu0: Reg, fu1: Reg, ac: Reg, imm: i32) {
        trace!("EE.LDF.64.IP fu{}, fu{}, a{}, imm{}", fu1, fu0, ac, imm);
        validate_signed_immediate_by_bits(imm, 11);
        validate_signed_mask(imm, 0xFFFFFFF8u32 as i32);
        self.ldf_64(buf, fu0, fu1, ac);
        self.areg[ac] = self.areg[ac].wrapping_add_signed(imm as i8 as i32);
    }

    pub fn ldf_64_xp(&mut self, buf: &[u16x8], fu0: Reg, fu1: Reg, ac: Reg, ad: Reg) {
        trace!("EE.LDF.64.XP fu{}, fu{}, a{}, a{}", fu1, fu0, ac, ad,);
        validate_areg(ad);
        self.ldf_64(buf, fu0, fu1, ac);
        self.areg[ac] = self.areg[ac].wrapping_add(self.areg[ad]);
    }

    pub fn ldxq_32(&mut self, buf: &[u16x8], qu: Reg, qs: Reg, ac: Reg, sel4: u8, sel8: u8) {
        trace!(
            "EE.LDXQ.32 q{}, q{}, a{}, sel{}, sel{}",
            qu, qs, ac, sel4, sel8
        );
        validate_qreg(qu);
        validate_qreg(qs);
        validate_areg(ac);
        validate_sel(sel4, 4);
        validate_sel(sel8, 8);

        let vaddr: u32x8 = (self.qreg[qs].cast() * u32x8::splat(4)) + u32x8::splat(self.areg[ac]);
        let data_in = load32(buf, vaddr[sel8 as usize] as usize);

        store32_int(self.qreg.get_mut(qu).unwrap(), data_in, sel4 as usize);
    }

    pub fn movi_32_a(&mut self, qs: Reg, au: Reg, sel4: u8) {
        trace!("EE.MOVI.32.A q{}, a{}, sel{}", qs, au, sel4,);
        validate_qreg(qs);
        validate_areg(au);
        validate_sel(sel4, 4);
        self.areg[au] = u32::from_le_bytes(
            load32_int(self.qreg[qs], sel4 as usize)
                .as_array()
                .map(u16::to_le_bytes)
                .as_flattened()
                .try_into()
                .unwrap(),
        );
    }

    pub fn movi_32_q(&mut self, qu: Reg, ac: Reg, sel4: u8) {
        trace!("EE.MOVI.32.Q q{}, a{}, sel{}", qu, ac, sel4,);
        validate_qreg(qu);
        validate_areg(ac);
        validate_sel(sel4, 4);
        let arr: [u8; 4] = self.areg[ac].to_le_bytes();
        let arr = [
            u16::from_le_bytes([arr[0], arr[1]]),
            u16::from_le_bytes([arr[2], arr[3]]),
        ];
        store32_int(self.qreg.get_mut(qu).unwrap(), arr.into(), sel4 as usize);
    }

    pub fn notq(&mut self, qa: Reg, qx: Reg) {
        trace!("EE.NOTQ q{}, q{}", qa, qx);
        validate_qreg(qa);
        validate_qreg(qx);
        self.qreg[qa] = !self.qreg[qx];
    }

    pub fn orq(&mut self, qa: Reg, qx: Reg, qy: Reg) {
        trace!("EE.ORQ q{}, q{}, q{}", qa, qx, qy);
        validate_qreg(qa);
        validate_qreg(qx);
        validate_qreg(qy);
        self.qreg[qa] = self.qreg[qx] | self.qreg[qy];
    }

    pub fn slci_2q(&mut self, qs1: Reg, qs0: Reg, sel16: u8) {
        trace!("EE.SLCI.2Q q{}, q{}, sel{}", qs1, qs0, sel16);
        validate_qreg(qs1);
        validate_qreg(qs0);
        validate_sel(sel16, 16);
        let mut q1 = u128::from_le_bytes(self.qreg[qs1].to_le_bytes().into());
        let mut q0 = u128::from_le_bytes(self.qreg[qs0].to_le_bytes().into());
        let shift = (sel16 as u32 + 1) * 8;
        q0 = q0.rotate_left(shift);
        q1 = q1.rotate_left(shift);
        let mask = (1_u128 << shift) - 1;
        q1 = (q1 & (!mask)) | (q0 & mask);
        q0 &= !mask;
        self.qreg[qs0] = u16x8::from_le_bytes(q0.to_le_bytes().into());
        self.qreg[qs1] = u16x8::from_le_bytes(q1.to_le_bytes().into());
    }

    pub fn slcxxp_2q(&mut self, qs1: Reg, qs0: Reg, ac: Reg, ad: Reg) {
        trace!("EE.SLCXXP.2Q q{}, q{}, a{}, a{}", qs1, qs0, ac, ad);
        validate_qreg(qs1);
        validate_qreg(qs0);
        validate_areg(ac);
        validate_areg(ad);
        let mut q1 = u128::from_le_bytes(self.qreg[qs1].to_le_bytes().into());
        let mut q0 = u128::from_le_bytes(self.qreg[qs0].to_le_bytes().into());
        let shift = ((self.areg[ac] & 0xF) + 1) * 8;
        q0 = q0.rotate_left(shift);
        q1 = q1.rotate_left(shift);
        let mask = (1_u128 << shift) - 1;
        q1 = (q1 & (!mask)) | (q0 & mask);
        q0 &= !mask;
        self.qreg[qs0] = u16x8::from_le_bytes(q0.to_le_bytes().into());
        self.qreg[qs1] = u16x8::from_le_bytes(q1.to_le_bytes().into());
        self.areg[ac] = self.areg[ac].wrapping_add(self.areg[ad]);
    }

    pub fn src_q(&mut self, qa: Reg, qs1: Reg, qs0: Reg) {
        trace!("EE.SLC.Q q{}, q{}, q{}", qa, qs1, qs0);
        validate_qreg(qa);
        validate_qreg(qs1);
        validate_qreg(qs0);
        let mut q1 = u128::from_le_bytes(self.qreg[qs1].to_le_bytes().into());
        let mut q0 = u128::from_le_bytes(self.qreg[qs0].to_le_bytes().into());
        let shift = (self.sar_byte as u32 & 0xF) * 8;
        q0 = q0.rotate_right(shift);
        q1 = q1.rotate_right(shift);
        let mask = u128::MAX >> shift;
        q0 = (q0 & mask) | (q1 & !mask);
        self.qreg[qa] = u16x8::from_le_bytes(q0.to_le_bytes().into());
    }
}
