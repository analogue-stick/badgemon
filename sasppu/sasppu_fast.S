//
// ESP32-S3 SIMD example
// Written by Larry Bank
// Copyright (c) 2024 BitBank Software, Inc.
//
	.text
	.align 4

// Simple signed 16-bit x 8 add
// registers with the args:     A2            A3            A4
// Call as int s3_add16x8(int16_t *pA, int16_t *pB, int16_t *pC);
	.global s3_add16x8
  .type   s3_add16x8,@function
s3_add16x8:
  entry   a1,16            # prepare windowed registers and reserve 16 bytes of stack
  ee.vld.128.ip	q0,a2,16   # load 8 "A" values into Q0 from A2, then add 16 to A2
  ee.vld.128.ip	q1,a3,16   # load 8 "B" values into Q1 from A3, then add 16 to A3
  ee.vadds.s16 q2,q0,q1    # C = A+B (with saturation)
  ee.vst.128.ip q2,a4,16   # store the 8 "C" values, then add 16 to A4
	movi.n	a2,0             # return value of 0
	retw.n                   # restore state (windowed registers) and return to caller

